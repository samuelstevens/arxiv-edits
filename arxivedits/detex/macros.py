"""
Tries to process commands described in https://en.wikibooks.org/wiki/LaTeX/Macros
"""

import string
import logging

from typing import Optional, List, Tuple, Any


from arxivedits.detex import latex
from arxivedits import structures


VALID_MACRO_CHARS = "@<>?"


class LatexMacro:
    """
    Represents a LaTeX command from `\\newcommand` or `\\def`, etc.
    """

    def __init__(
        self,
        name: str,
        definition: str,
        arg_num: int = 0,
        default_arg: Optional[str] = None,
    ) -> None:
        assert isinstance(name, str), f"{name} is not a string"
        assert name, "name is empty"  # checks if len > 0
        assert name[0] == "\\", f"command {name} does not begin with \\"
        self.name = name

        assert isinstance(definition, str), f"{definition} is not a string"

        deflines = [
            line[: line.index("%")] if "%" in line else line
            for line in definition.split("\n")
        ]
        definition = "\n".join(deflines)

        self.definition = definition.strip()

        assert isinstance(arg_num, int)
        self.arg_num = arg_num

        assert isinstance(default_arg, str) or default_arg is None
        self.default_arg = default_arg

    def __str__(self) -> str:
        return f"Command: {self.name}, def: {self.definition}"

    def result(self, args: List[str]) -> structures.Result[str]:
        """
        Given some macro arguments, produces a result string.
        """
        result = self.definition

        if len(args) < self.arg_num:
            if self.default_arg:
                args = [self.default_arg, *args]
            else:
                return ValueError(f"Missing argument #{len(args) + 1}")

        for i, a in enumerate(args):
            result = result.replace(f"#{i + 1}", a)  # replaces #1, and leaves in in {}

        return result

    def required_arg_count(self) -> int:
        """
        The required number of arguments. Takes whether the command has a default arg into account.
        """
        if self.default_arg:
            return self.arg_num - 1

        return self.arg_num

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LatexMacro):
            return False

        return (
            other.name == self.name
            and other.definition == self.definition
            and other.arg_num == self.arg_num
            and other.default_arg == self.default_arg
        )

    def __hash__(self) -> int:
        return hash(repr(self))


class MacroParser:
    r"""
    Class to parse a variety of LaTeX macros, such as \newcommand or \def.
    """

    def __init__(self, text: str, pos: int, command: str = ""):
        self.text = text
        self.pos = pos
        self.command = command

        assert command
        assert text.startswith(command, pos), self.context()

    def parse(self) -> structures.Result[Tuple[LatexMacro, int]]:
        raise NotImplementedError("Needs to be implemented")

    def context(self) -> str:
        return self.text[self.pos - 30 : self.pos + 30]

    def Error(self, msg: str) -> Exception:
        return RuntimeError(f"{self.context()}\n{msg}")


class DefParser(MacroParser):
    """
    Parses `\\def \\name [arg1]arg2{replacement}`
    """

    def __init__(self, text: str, pos: int, command: str = r"\def") -> None:
        super().__init__(text, pos, command)

    def parse(self) -> structures.Result[Tuple[LatexMacro, int]]:
        r"""
        \def \name{\emph{else}}
        """

        self.pos += len(self.command)

        if self.text[self.pos] == "*":
            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)

        # self.tex[self.pos] should now be \
        if self.text[self.pos] != "\\":
            return self.Error(
                f"invalid {self.command} because command doesn't start with \\."
            )

        # find command name
        self.pos += 1
        command_start = self.pos

        # command can be one non-letter character
        if self.text[self.pos] not in string.ascii_letters:
            self.pos += 1
        # or command can be any sequence of letters
        else:
            while self.text[self.pos] in string.ascii_letters:
                self.pos += 1

        # args start with #1#2, but also like [#1]#2

        command_end = self.pos

        argcount = 0

        # parse argument in square brackets
        if self.text[self.pos : self.pos + 4] == "[#1]":
            argcount += 1
            self.pos = self.pos + 4

        while self.text[self.pos] == "#" and self.text[self.pos + 1] in string.digits:
            self.pos += 2
            argcount += 1

        command_name = "\\" + self.text[command_start:command_end]

        if self.text[self.pos] != "{":
            return self.Error("Needs to start with '{'")

        start_def = self.pos + 1

        end_def, err = latex.find_pair("{", "}", self.text, start=self.pos)

        if err:
            return self.Error(str(err))

        definition = self.text[start_def:end_def]

        self.pos = end_def  # gets past }

        command = LatexMacro(command_name, definition, argcount, None)

        return (command, self.pos)


class GdefParser(DefParser):
    """
    Parses \\gdef
    """

    def __init__(self, text: str, pos: int, command: str = r"\gdef") -> None:
        super().__init__(text, pos, command)


class NewCommandParser(MacroParser):
    """
    Parses \\newcommand and \\newcommand*
    """

    def __init__(self, text: str, pos: int, command: str = r"\newcommand") -> None:
        super().__init__(text, pos, command)

    def parse(self) -> structures.Result[Tuple[LatexMacro, int]]:
        r"""
        \newcommand{\name}[2][default]{my other stuff #1 here and #2}

        \newcommand\help{please help me bro}
        """
        self.pos += len(self.command)

        if self.text[self.pos] == "*":
            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)
        # self.tex[self.pos] should now be { or \

        opening_brace = self.text[self.pos]

        if opening_brace == "{":
            closing_brace = "}"
            self.pos += 1
        elif opening_brace == "\\":  # start of command name
            closing_brace = ""
        else:
            return self.Error(
                r"invalid " + self.command + r" because of missing '{', '\', or ' '."
            )

        if self.text[self.pos] != "\\":
            return self.Error(r"invalid " + self.command)

        # find command name
        self.pos += 1
        command_start = self.pos
        while self.text[self.pos] in string.ascii_letters + VALID_MACRO_CHARS:
            self.pos += 1
        command_end = self.pos
        command_name = "\\" + self.text[command_start:command_end]

        self.pos += len(closing_brace)

        self.pos = skip_whitespace(self.text, self.pos)

        arg_count = 0
        # check for optional arguments
        if self.text[self.pos] == "[":
            # we have args
            self.pos += 1
            arg_count = int(self.text[self.pos])
            self.pos += 1

            if self.text[self.pos] != "]":
                logging.warning("invalid arguments.")

            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)

        # check for default argument
        default_arg = None
        if self.text[self.pos] == "[":
            # we have a default argument
            start_default = self.pos + 1
            while self.pos < len(self.text) and self.text[self.pos] != "]":
                self.pos += 1
            end_default = self.pos

            default_arg = self.text[start_default:end_default]

            if self.text[self.pos] != "]":
                logging.warning("invalid default arg.")

            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)

        # looking for opening brace now.
        if self.text[self.pos] != "{":
            return self.Error(
                f"invalid definition at {self.pos}: {self.text[self.pos]}"
            )

        start_def = self.pos + 1

        end_def, err = latex.find_pair("{", "}", self.text, start=self.pos)

        if isinstance(err, Exception):
            return self.Error("Cound't find end of definition.")

        definition = self.text[start_def:end_def]

        self.pos = end_def  # gets past }

        command = LatexMacro(command_name, definition, arg_count, default_arg)

        return (command, self.pos)


class RobustCommandParser(NewCommandParser):
    def __init__(
        self, text: str, pos: int, command: str = r"\DeclareRobustCommand"
    ) -> None:
        super().__init__(text, pos, command)


def skip_whitespace(text: str, position: int) -> int:
    """
    Returns the position in the text when it's no longer whitespace.
    """
    while position < len(text) and text[position] in string.whitespace:
        position += 1
    return position


def get_args(
    text: str, starting_position: int, command: LatexMacro
) -> Tuple[int, List[str]]:

    position = starting_position
    args: List[str] = []
    default_arg = None

    if command.default_arg:
        if text[position] == "[":
            end_of_arg, err = latex.find_pair("[", "]", text, position)

            if err:
                logging.warning(err)

            default_arg = text[position + 1 : end_of_arg]

            position = end_of_arg + 1

    # first argument can be in square braces
    if text[position] == "[":
        position += 1
        arg_start = position

        arg_end, err = latex.find_pair("[", "]", text, position - 1)

        args.append(text[arg_start:arg_end])

        position = arg_end
        position += 1

    while command.required_arg_count() > len(args) and position < len(text):
        if text[position] != "{":
            logging.info(
                f"Command {command.name} requires {command.required_arg_count()} arguments. Found {len(args)}: {', '.join(args)}",
            )

            return position, args

        position += 1
        arg_start = position

        arg_end, err = latex.find_pair("{", "}", text, position - 1)

        args.append(text[arg_start:arg_end])

        position = arg_end
        position += 1

    if default_arg:
        args.insert(0, default_arg)

    return position, args


def process(initial_tex: str) -> str:
    """
    Processes `\\newcommand` and similar commands in LaTeX.
    """

    commands: List[LatexMacro] = []  # order is very important
    string_builder = []
    start_valid = 0
    position = 0

    while position < len(initial_tex):
        parser: MacroParser

        if initial_tex[position] == "\\":  # potentially at a new command definition
            if initial_tex.startswith("newcommand", position + 1):
                parser = NewCommandParser(initial_tex, position)

            elif initial_tex.startswith("def", position + 1):
                parser = DefParser(initial_tex, position)

            elif initial_tex.startswith("gdef", position + 1):
                parser = GdefParser(initial_tex, position)

            elif initial_tex.startswith("DeclareRobustCommand", position + 1):
                parser = RobustCommandParser(initial_tex, position)

            else:
                position += 1
                continue

            string_builder.append(initial_tex[start_valid:position])

            result = parser.parse()

            if isinstance(result, Exception):
                logging.debug(f"Parse error: {result}")
            else:
                command, position = result
                commands.append(command)

            start_valid = position + 1  # get past }

        position += 1

    string_builder.append(initial_tex[start_valid:])

    position = 0

    text = "".join(string_builder)

    for command in commands:
        string_builder = []

        end_command = 0
        pos = 0

        while pos < len(text):
            start_command = text.find(command.name, pos)

            if start_command < 0:
                # finished with this command
                string_builder.append(text[end_command:])
                break

            # if we find a command, check that it's not escaped with \
            if text[start_command - 1] == "\\":
                pos = start_command + 1
                continue

            # if we find a command, check that it's not another valid latex command
            if (
                start_command + len(command.name) < len(text)
                and text[start_command + len(command.name)] in string.ascii_letters
            ):
                pos = start_command + 1
                continue

            string_builder.append(text[end_command:start_command])

            end_command = start_command + len(command.name)

            if end_command >= len(text):
                logging.warning(f"Couldn't find the end of the word '{command.name}'.")
                break

            end_command, arguments = get_args(text, end_command, command)

            if end_command >= len(text):
                logging.warning(f"Couldn't find the end of '{command}'.")
                break

            if text[end_command] in ["\\"]:
                end_command += 1
            elif text[end_command : end_command + 1] == "{}":
                end_command += 2

            command_result = command.result(arguments)

            if isinstance(command_result, Exception):
                logging.debug(command_result)
            else:
                string_builder.append(command_result)

            pos = end_command

        text = "".join(string_builder)

    return text
