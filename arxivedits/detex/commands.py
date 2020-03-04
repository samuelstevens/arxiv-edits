from collections import namedtuple
import logging

from arxivedits.detex import latex
from arxivedits import structures

from typing import Callable, Tuple


class LatexCommand:
    def __init__(
        self,
        name: str,
        general_parse: Callable[[str, int, str], structures.Go[Tuple[str, int]]],
    ):
        self.name = name
        self.parse = general_parse

    def __call__(
        self, inital_tex: str, position: int, command_name: str
    ) -> structures.Go[Tuple[str, int]]:
        return self.parse(inital_tex, position, command_name)


def LengthParse(
    initial_tex: str, position: int, name: str
) -> structures.Go[Tuple[str, int]]:
    r"""
    Expects some .tex that looks like {\setlength\arraycolsep{1pt} some more text here}.

    Returns "" (because \setlength is a useless command)
    """

    if initial_tex[position] != "\\":
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    if not initial_tex.startswith(name, position + 1):
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    position += 1 + len(name)

    if initial_tex[position] not in ["\\", "{"]:
        return (
            ("", position),
            ValueError("Command needs to an arg starting with \\ or {"),
        )

    if initial_tex[position] == "{":

        argend, err = latex.find_pair("{", "}", initial_tex, position)

        if err is not None:
            return ("", argend), err

    elif initial_tex[position] == "\\":
        argend = initial_tex.find("{", position)

        if argend < 0:
            return ("", position), ValueError("Command needs to arg to end with {")

    endvalue, err = latex.find_pair("{", "}", initial_tex, argend)

    if err is not None:
        return ("", endvalue), err

    return ("", endvalue), None


BAD_COMMANDS = [
    LatexCommand("setlength", LengthParse),
    LatexCommand("addtolength", LengthParse),
]


def process(initial_tex: str) -> str:
    position = 0
    string_builder = []
    start_valid = 0
    while position < len(initial_tex):
        if initial_tex[position] == "\\":
            for command in BAD_COMMANDS:
                if not initial_tex.startswith(command.name, position + 1):
                    continue

                string_builder.append(initial_tex[start_valid:position])

                result, err = command.parse(initial_tex, position, command.name)

                if err is not None:
                    logging.warning(err)

                text, position = result

                string_builder.append(text)
                start_valid = position + 1

        position += 1

    string_builder.append(initial_tex[start_valid:])

    return "".join(string_builder)


def main():
    test_command = r"""{\setlength\arraycolsep{1pt}
    [EQUATION]}"""

    text = process(test_command)
    print(text)


if __name__ == "__main__":
    main()
