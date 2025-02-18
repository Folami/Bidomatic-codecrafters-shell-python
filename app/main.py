import sys
import os
import shlex
import subprocess

shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

def main():
    """Main function of the shell program."""
    while True:
        sys.stdout.write("$ ")
        command_line = input()
        if not command_line:  # Handle empty input
            continue

        try:
            tokens = tokenize_command(command_line)  # Tokenize the command line
            if not tokens:
                continue

            command, *parts = tokens  # Separate command and arguments
            args = process_arguments(parts)  # Process arguments (quotes, escapes)

            execute_command(command, args)  # Execute the command

        except EOFError:  # Handle Ctrl+D
            break
        except Exception as e:  # Handle other exceptions
            print(f"An error occurred: {e}")


def tokenize_command(command_line):
    """Tokenizes the command line, handling spaces outside of quotes."""
    parts = []
    in_single_quotes = False
    in_double_quotes = False
    current_part = ""
    for char in command_line:
        if char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
        elif char == " " and not in_single_quotes and not in_double_quotes:
            if current_part:
                parts.append(current_part)
                current_part = ""
        else:
            current_part += char
    if current_part:
        parts.append(current_part)
    return parts


def process_arguments(parts):
    """Processes arguments, handling single quotes and backslashes."""
    args = []
    for arg in parts:
        if arg.startswith("'") and arg.endswith("'"):
            # Remove the single quotes but keep backslashes literal
            processed_arg = arg[1:-1]
            args.append(processed_arg)
        else:
            try:
                shlex_split_args = shlex.split(arg)  # Use shlex for double quotes and other escapes
                args.extend(shlex_split_args)
            except:
                args.append(arg)  # If shlex fails, append the original arg
    return args



def execute_command(command, args):
    """Executes the command, handling built-ins and external commands."""
    match command:
        case "exit":
            exit_shell()
        case "echo":
            execute_echo(args)
        case "type":
            execute_type(args)
        case "pwd":
            execute_pwd()
        case "cd":
            execute_cd(args)
        case _:
            run_external_command(command, args)


def exit_shell():
    """Exits the shell."""
    return  # No need for explicit exit in this simple case


def execute_echo(args):
    """Executes the echo command."""
    print(" ".join(args))


def execute_type(args):
    """Executes the type command."""
    if not args:
        print("type: missing operand")
        return

    target_command = args[0]
    if target_command in shBuiltins:
        print(f"{target_command} is a shell builtin")
    else:
        executable = find_executable(target_command)
        if executable:
            print(f"{target_command} is {executable}")
        else:
            print(f"{target_command}: not found")


def execute_pwd():
    """Executes the pwd command."""
    print(os.getcwd())


def execute_cd(args):
    """Executes the cd command."""
    if not args:
        print("cd: missing operand")
        return

    new_dir = os.path.expanduser(args[0])  # Handle ~
    if not os.path.isabs(new_dir):  # Make relative paths absolute
        new_dir = os.path.abspath(new_dir)

    try:
        os.chdir(new_dir)
    except FileNotFoundError:
        print(f"cd: {args[0]}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {args[0]}: Not a directory")
    except Exception as e:
        print(f"cd: error: {e}")


def find_executable(command):
    """Searches the PATH for an executable."""
    path_env = os.environ.get("PATH")
    if path_env:
        for directory in path_env.split(os.pathsep):
            file_path = os.path.join(directory, command)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path
    return None


def run_external_command(command, args):
    """Runs an external command using subprocess."""
    try:
        result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
        print(result.stdout, end="")
    except subprocess.CalledProcessError as e:
        print(f"{command}: command failed with exit code {e.returncode}")
        print(e.stderr, end="", file=sys.stderr)
    except FileNotFoundError:
        print(f"{command}: command not found")
    except Exception as e:
        print(f"An error occurred while running {command}: {e}")


if __name__ == "__main__":
    main()