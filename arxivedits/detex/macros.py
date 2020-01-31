"""
Tries to process commands described in https://en.wikibooks.org/wiki/LaTeX/Macros
"""

import string


from typing import Optional, Set, List, Tuple


from arxivedits.detex import latex
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
            end_of_arg, err = latex.find_pair("[", "]", text, position)

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

    commands: Set[LatexCommand] = set()
    string_builder = []
    start_valid = 0
    position = 0

    while position < len(initial_tex):
        if initial_tex[position] == "\\":  # potentially at a new command definition
            if initial_tex.startswith("newcommand", position + 1):

                string_builder.append(initial_tex[start_valid:position])

                position += len(r"\newcommand")
                if initial_tex[position] == "*":
                    position += 1

                position = skip_whitespace(initial_tex, position)

                # initial_tex[position] should now be {, <space>, or \

                opening_brace = initial_tex[position]

                if opening_brace == "{":
                    closing_brace = "}"
                    position += 1
                elif opening_brace == " ":
                    closing_brace = " "
                    position += 1
                elif opening_brace == "\\":
                    closing_brace = ""
                else:
                    print(initial_tex[position - 10 : position + 10])
                    print(r"invalid \newcommand because of missing '{', '\', or ' '.")
                    break

                if initial_tex[position] != "\\":
                    print(initial_tex[position - 10 : position + 10])
                    print(r"invalid \newcommand.")
                    break

                # find command name
                position += 1
                command_start = position
                while initial_tex[position] in string.ascii_letters + VALID_MACRO_CHARS:
                    position += 1
                command_end = position
                command_name = "\\" + initial_tex[command_start:command_end]

                position += len(closing_brace)

                position = skip_whitespace(initial_tex, position)

                arg_count = 0
                # check for optional arguments
                if initial_tex[position] == "[":
                    # we have args
                    position += 1
                    arg_count = int(initial_tex[position])
                    position += 1

                    if initial_tex[position] != "]":
                        print("invalid arguments.")
                        break

                    position += 1

                position = skip_whitespace(initial_tex, position)

                # check for default argument
                default_arg = None
                if initial_tex[position] == "[":
                    # we have a default argument
                    start_default = position + 1
                    while position < len(initial_tex) and initial_tex[position] != "]":
                        position += 1
                    end_default = position

                    default_arg = initial_tex[start_default:end_default]

                    if initial_tex[position] != "]":
                        print("invalid default arg.")
                        break

                    position += 1

                position = skip_whitespace(initial_tex, position)

                # looking for opening brace now.
                if initial_tex[position] != "{":
                    print(
                        f"invalid definition at {position}: {initial_tex[position]} \ncontext: {initial_tex[position -10: position + 10]}\ncommand name: {command_name}"
                    )
                    break

                start_def = position + 1

                end_def, err = latex.find_pair("{", "}", initial_tex, start=position)

                if isinstance(err, Exception):
                    print("could not find end of definition.")
                    break

                definition = initial_tex[start_def:end_def]

                command = LatexCommand(command_name, definition, arg_count, default_arg)

                commands.add(command)

                start_valid = end_def + 1  # get past }

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

            if (
                text[end_command] not in [".", ",", "-", "}", "{", "\n", "$"]
                and text[end_command : end_command + 1] != "{}"
            ):
                end_command += 1
            command_result, err = command.result(arguments)

            if err:
                print(err)

            string_builder.append(command_result)

            pos = end_command

        text = "".join(string_builder)

    return text

