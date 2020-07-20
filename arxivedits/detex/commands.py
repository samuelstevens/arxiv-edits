import logging

from arxivedits.detex import latex, macros
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


def NewTheoremParse(
    initial_tex: str, position: int, name: str = "newtheorem"
) -> structures.Go[Tuple[str, int]]:
    r"""
    expects some .tex that looks like:
    1. \newtheorem{some}{thing}
    2. \newtheorem{some}{thing}[count]
    3. \newtheorem{some}[count]{thing}
    4. \newtheorem*{some}{thing}

    Replaces it with "" because we hope no one sets really complicated environments (theorems)
    """

    if initial_tex[position] != "\\":
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    if not initial_tex.startswith(name, position + 1):
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    position += 1 + len(name)

    saw_count = False
    numbered = True

    if initial_tex[position] == "*":
        position += 1
        numbered = False

    if initial_tex[position] != "{":
        return ("", position), ValueError("Command needs to an arg starting with {")

    if initial_tex[position] == "{":
        position, err = latex.find_pair("{", "}", initial_tex, position)

        if err is not None:
            return ("", position), err

        position += 1
    else:
        return ("", position), ValueError("newtheorem needs one arg starting with {")

    if initial_tex[position] == "[":
        position, err = latex.find_pair("[", "]", initial_tex, position)

        if err is not None:
            return ("", position), err

        saw_count = True

        position += 1

    if initial_tex[position] == "{":
        position, err = latex.find_pair("{", "}", initial_tex, position)

        if err is not None:
            return ("", position), err

    else:
        return (
            ("", position),
            ValueError("newtheorem needs a second arg starting with {"),
        )

    if (
        position + 1 < len(initial_tex)
        and initial_tex[position + 1] == "["
        and not saw_count
        and numbered
    ):
        position, err = latex.find_pair("[", "]", initial_tex, position)

        if err is not None:
            return ("", position), err

    return ("", position), None


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
            ValueError("Command needs an arg starting with \\ or {"),
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


def LstDefineLanguageParse(
    initial_tex: str, position: int, name: str
) -> structures.Go[Tuple[str, int]]:
    r"""
    Expects some .tex that looks like 
    
    \lstdefinelanguage[bzr]{c++}
        {
            basicstyle=\scriptsize,
            morekeywords={node, returns, let, tel, peId, peid,  int,  var, contract,
            assume, enforce, with, bool, *, +, if, then , else, hwParam,
            func, main, and, not, until, state, do, true, false, automaton, end},  
        }

    OR 

    \lstdefinelanguage{idl2}
        {
            basicstyle=\scriptsize,
            morekeywords={in, out, interface, void},
            backgroundcolor=\color{yellow},
        }

    Returns empty string
    """

    if initial_tex[position] != "\\":
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    if not initial_tex.startswith(name, position + 1):
        return ("", position), ValueError(f"Command needs to start with \\{name}")

    position += 1 + len(name)

    position = macros.skip_whitespace(initial_tex, position)

    # parse optional [stuff]
    if initial_tex[position] == "[":
        position, err = latex.find_pair("[", "]", initial_tex, position)
        position += 1  # skip the ]
        position = macros.skip_whitespace(initial_tex, position)

    if initial_tex[position] != "{":
        return (
            ("", position),
            ValueError(
                f"Command {name} needs an language (c++, etc) arg starting with {{"
            ),
        )

    position, err = latex.find_pair("{", "}", initial_tex, position)

    if err is not None:
        return ("", position), err

    position += 1  # skip the }

    position = macros.skip_whitespace(initial_tex, position)

    if initial_tex[position] != "{":
        return (
            ("", position),
            ValueError(
                f"Command {name} needs a body (basicstyle, etc) arg starting with {{"
            ),
        )

    position, err = latex.find_pair("{", "}", initial_tex, position)

    position += 1

    if err is not None:
        return ("", position), err

    return ("", position), None

    return ("", len(initial_tex) - 1), None


BAD_COMMANDS = [
    LatexCommand("setlength", LengthParse),
    LatexCommand("addtolength", LengthParse),
    LatexCommand("newtheorem", NewTheoremParse),
    LatexCommand("lstdefinelanguage", LstDefineLanguageParse),
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

                if err:
                    logging.debug(err)

                text, position = result

                string_builder.append(text)
                start_valid = position + 1

        position += 1

    string_builder.append(initial_tex[start_valid:])

    return "".join(string_builder)


def main() -> None:
    test_command = r"""{\setlength\arraycolsep{1pt}
    [EQUATION]}"""

    text = process(test_command)
    print(text)


if __name__ == "__main__":
    main()
