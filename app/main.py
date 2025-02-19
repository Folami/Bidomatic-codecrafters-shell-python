import sys
import os
import subprocess

def inputPrompt():
    sys.stdout.write("$ ")
    return input()

def main():
    shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

    while True:
        command_line = inputPrompt()
        if not command_line:
            continue

        try:
            tokens = custom_tokenize(command_line)  # Use custom tokenizer
            if not tokens:
                continue

            command, *parts = tokens
            args = custom_process_arguments(parts)  # Use custom argument processor

            execute_command(command, args)

        except EOFError:
            break
        except Exception as e:
            print(f"An error occurred: {e}")


def custom_tokenize(command_line):
    """Custom tokenizer to handle quoting and backslashes."""
    tokens = []
    in_single_quotes = False
    in_double_quotes = False
    current_token = ""

    for char in command_line:
        if char == "'" and not in_double_quotes:
            if in_single_quotes:
                tokens.append(current_token)
                current_token = ""
            in_single_quotes = not in_single_quotes
        elif char == '"' and not in_single_quotes:
            if in_double_quotes:
                tokens.append(current_token)
                current_token = ""
            in_double_quotes = not in_double_quotes
        elif char == "\\" and (in_single_quotes or in_double_quotes):
            # Handle backslashes within quotes (literally)
            current_token += char
        elif char == " " and not in_single_quotes and not in_double_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ""
        else:
            current_token += char

    if current_token:
        tokens.append(current_token)

    return tokens


def custom_process_arguments(parts):
    """Custom argument processor to handle quotes and backslashes."""
    args = []
    for arg in parts:
        if arg.startswith("'") and arg.endswith("'"):
            # Remove single quotes and handle backslashes literally
            processed_arg = arg[1:-1].replace("\\\\", "\\").replace("\\'", "'").replace("\\\"", "\"")
            args.append(processed_arg)
        elif arg.startswith('"') and arg.endswith('"'):
            processed_arg = arg[1:-1].replace("\\\\", "\\").replace("\\'", "'").replace("\\\"", "\"")
            args.append(processed_arg)
        else:
            args.append(arg)

    return args

def execute_command(command, args, shBuiltins):
    """Executes the command, handling built-ins and external commands."""
    match command:
        case "exit":
            exit_shell()
        case "echo":
            execute_echo(args)
        case "type":
            execute_type(args, shBuiltins)
        case "pwd":
            execute_pwd()
        case "cd":
            execute_cd(args)
        case _:
            run_external_command(command, args)

def exit_shell():
    """Exits the shell."""
    sys.exit(0)

def execute_echo(args):
    """Executes the echo command."""
    print(" ".join(args))

def execute_type(args, shBuiltins):
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
    if not os.path.isabs(new_dir):         # Make relative paths absolute
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
