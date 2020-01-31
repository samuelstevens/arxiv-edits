"""
Tries to process commands described in https://en.wikibooks.org/wiki/LaTeX/Macros
"""

import string


from typing import Optional, Set, List, Tuple


from arxivedits.detex.latex import find_pair
from arxivedits import structures

VALID_MACRO_CHARS = "@<>?"


class LatexCommand:
    """
    Represents a LaTeX command from `\\newcommand` or `\\def`, etc.
    """

    def __init__(
        self,
        name: str,
        definition: str,
        arg_num: int = 0,
        default_arg: Optional[str] = None,
    ):
        assert isinstance(name, str)
        assert name  # checks if len > 0
        assert name[0] == "\\"
        self.name = name

        assert isinstance(definition, str)
        self.definition = definition.strip()

        assert isinstance(arg_num, int)
        self.arg_num = arg_num

        assert isinstance(default_arg, str) or default_arg is None
        self.default_arg = default_arg

    def __str__(self):
        return f"Command: {self.name}, def: {self.definition}"

    def result(self, args: List[str]) -> structures.Go[str]:
        """
        Given some macro arguments, produces a result string.
        """
        result = self.definition

        if len(args) < self.arg_num:
            if self.default_arg:
                args = [self.default_arg, *args]
            else:
                return "", ValueError(f"Missing argument #{len(args)}")

        for i, a in enumerate(args):
            result = result.replace(f"{{#{i + 1}}}", a)  # replaces {#1}
            result = result.replace(f"#{i + 1}", a)  # replaces #1

        return result, None

    def required_arg_count(self):
        """
        The required number of arguments. Takes whether the command has a default arg into account.
        """
        if self.default_arg:
            return self.arg_num - 1

        return self.arg_num

    def __eq__(self, other):
        if not isinstance(other, LatexCommand):
            return False

        return (
            other.name == self.name
            and other.definition == self.definition
            and other.arg_num == self.arg_num
            and other.default_arg == self.default_arg
        )

    def __hash__(self):
        return hash(repr(self))


class MacroParser:
    r"""
    Class to parse a variety of LaTeX macros, such as \newcommand or \def.
    """

    def __init__(self, text, pos):
        self.text = text
        self.pos = pos

    def parse(self) -> structures.Go[Tuple[LatexCommand, int]]:
        raise NotImplementedError("Needs to be implemented")

    def context(self):
        return self.text[self.pos - 30 : self.pos + 30]

    def Error(self, msg) -> Tuple[Tuple[LatexCommand, int], Exception]:
        return (
            (LatexCommand("", ""), self.pos),
            RuntimeError(f"{self.context()}\n{msg}"),
        )


class DefParser(MacroParser):
    """
    Parses \\def
    """

    def __init__(self, text, pos):
        super().__init__(text, pos)

        self.command = r"\def"
        assert text.startswith(self.command, self.pos)

    def parse(self) -> structures.Go[Tuple[LatexCommand, int]]:
        r"""
        \def \name{\emph{else}}
        """

        self.pos += len(self.command)

        if self.text[self.pos] == "*":
            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)
        # self.tex[self.pos] should now be \

        if self.text[self.pos] != "\\":
            return self.Error(r"invalid \def because command doesn't start with \.")

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

        command_end = self.pos
        command_name = "\\" + self.text[command_start:command_end]

        if self.text[self.pos] != "{":
            return self.Error("Needs to start with '{'")

        start_def = self.pos + 1

        end_def = self.text.find("\n", self.pos) - 1

        if end_def < 0:
            return self.Error("Couldn't find end of definition on the same line.")

        definition = self.text[start_def:end_def]

        self.pos = end_def  # gets past }

        command = LatexCommand(command_name, definition, 0, None)

        return (command, self.pos), None


class NewCommandParser(MacroParser):
    """
    Parses \\newcommand and \\newcommand*
    """

    def __init__(self, text, pos):
        super().__init__(text, pos)

        self.command = r"\newcommand"

        assert text.startswith(self.command, pos), self.context()

    def parse(self) -> structures.Go[Tuple[LatexCommand, int]]:
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
                r"invalid \newcommand because of missing '{', '\', or ' '."
            )

        if self.text[self.pos] != "\\":
            return self.Error(r"invalid \newcommand.")

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
                print("invalid arguments.")

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
                print("invalid default arg.")

            self.pos += 1

        self.pos = skip_whitespace(self.text, self.pos)

        # looking for opening brace now.
        if self.text[self.pos] != "{":
            print(
                f"invalid definition at {self.pos}: {self.text[self.pos]} \ncontext: {self.text[self.pos -10: self.pos + 10]}\ncommand name: {command_name}"
            )

        start_def = self.pos + 1

        end_def, err = find_pair("{", "}", self.text, start=self.pos)

        if isinstance(err, Exception):
            print("could not find end of definition.")

        definition = self.text[start_def:end_def]

        self.pos = end_def  # gets past }

        command = LatexCommand(command_name, definition, arg_count, default_arg)

        return (command, self.pos), None


def skip_whitespace(text: str, position: int) -> int:
    """
    Returns the position in the text when it's no longer whitespace.
    """
    while position < len(text) and text[position] in string.whitespace:
        position += 1
    return position


def get_args(
    text: str, starting_position: int, command: LatexCommand
) -> Tuple[int, List[str]]:
    position = starting_position
    args: List[str] = []
    default_arg = None

    if command.default_arg:
        if text[position] == "[":
            end_of_arg, err = find_pair("[", "]", text, position)

            if err:
                print(err)

            default_arg = text[position + 1 : end_of_arg]

            position = end_of_arg + 1

    while command.required_arg_count() > len(args) and position < len(text):
        if text[position] != "{":
            print(
                f"Command requires {command.required_arg_count()} arguments. Found {len(args)}."
            )
            return position, args

        position += 1
        arg_start = position

        arg_end, err = find_pair("{", "}", text, position - 1)

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

    commands: Set[LatexCommand] = set()
    string_builder = []
    start_valid = 0
    position = 0

    while position < len(initial_tex):
        parser = MacroParser("", 0)

        if initial_tex[position] == "\\":  # potentially at a new command definition
            if initial_tex.startswith("newcommand", position + 1):
                parser = NewCommandParser(initial_tex, position)
            elif initial_tex.startswith("def", position + 1):
                parser = DefParser(initial_tex, position)
            else:
                position += 1
                continue

            string_builder.append(initial_tex[start_valid:position])
            try:
                result, err = parser.parse()

                if not err:
                    command, position = result
                    commands.add(command)
            except AssertionError:
                pass

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
                print("UH OH")
                # break

            end_command, arguments = get_args(text, end_command, command)

            if text[end_command] in ["\\"]:
                end_command += 1
            elif text[end_command : end_command + 1] == "{}":
                end_command += 2

            command_result, err = command.result(arguments)

            if err:
                print(err)

            string_builder.append(command_result)

            pos = end_command

        text = "".join(string_builder)

    return text

