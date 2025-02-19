import sys
import os
import subprocess

def inputPrompt():
    sys.stdout.write("$ ")
    return input()

def main():
    shBuiltins = ["echo", "exit", "type", "pwd", "cd"]
    
    """Main function of the shell program."""
    while True:
        command_line = inputPrompt()
        if not command_line:  # Handle empty input
            continue

        try:
            # Use our custom tokenizer (without shlex) to split the input
            tokens = manual_tokenize(command_line)
            if not tokens:
                continue

            # The first token is the command; the rest are arguments
            command = tokens[0]
            args = tokens[1:]
            execute_command(command, args, shBuiltins)

        except EOFError:  # Handle Ctrl+D
            break
        except Exception as e:  # Handle other exceptions
            print(f"An error occurred: {e}")

def manual_tokenize(s):
    """
    Manually tokenizes the input string into tokens, supporting:
      - Unquoted text (tokens separated by whitespace)
      - Double-quoted strings: backslashes escape the next character
      - Single-quoted strings: backslashes also escape the next character (non‐POSIX behavior)
      - Backslashes outside quotes escape the following character
    """
    tokens = []
    current = []        # List of characters for the current token
    state = None        # Can be None, 'single', or 'double'
    escape = False      # True if the previous character was a backslash

    for char in s:
        if escape:
            # Append the next character literally, regardless of quoting state
            current.append(char)
            escape = False
            continue

        if char == '\\':
            escape = True
            continue

        if state is None:
            # Not inside any quotes
            if char == "'":
                state = "single"
            elif char == '"':
                state = "double"
            elif char.isspace():
                if current:
                    tokens.append("".join(current))
                    current = []
            else:
                current.append(char)
        elif state == "single":
            # Inside single quotes, we want to support backslash escapes as well.
            if char == "'":
                state = None
            else:
                current.append(char)
        elif state == "double":
            if char == '"':
                state = None
            else:
                current.append(char)
    # If we ended with an escape, add the literal backslash
    if escape:
        current.append('\\')
    # If there's any remaining text, add it as a token
    if current:
        tokens.append("".join(current))
    return tokens

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
