import sys
import os
import subprocess

def inputPrompt():
    sys.stdout.write("$ ")
    return input()

def main():
    # List of built-in commands.
    shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

    """Main function of the shell program."""
    while True:
        command_line = inputPrompt()
        if not command_line:  # Handle empty input
            continue

        try:
            # Tokenize the command line using our custom manual tokenizer.
            tokens = manual_tokenize(command_line)
            if not tokens:
                continue

            # The first token is the command; remaining tokens are arguments.
            command = tokens[0]
            args = tokens[1:]
            execute_command(command, args, shBuiltins)

        except EOFError:  # Handle Ctrl+D
            break
        except Exception as e:  # Handle other exceptions
            print(f"An error occurred: {e}")

def manual_tokenize(cmd_line):
    """
    Manually tokenizes the input string into tokens, supporting:
      - Unquoted text (tokens separated by whitespace)
      - Double-quoted strings: backslashes escape the next character
      - Single-quoted strings: backslashes are preserved literally
      - Support for nested literal single-quoted segments within double quotes.
                  "/tmp/baz/'f \\67\\'" ]
    """
    tokens = []
    current = []        # List of characters in the current token.
    state = None        # None, 'single', or 'double'
    escape = False      # True if the previous character was a backslash.
    i = 0
    n = len(cmd_line)
    while i < n:
        if cmd_line[i].isspace():
            i += 1
            continue
        elif cmd_line[i] == "'":
            token, i = handle_single_quote(cmd_line, i)
        elif cmd_line[i] == '"':
            token, i = handle_double_quote(cmd_line, i)
        else:
            token, i = handle_unquoted(cmd_line, i)
        tokens.append(token)
    return tokens

def handle_unquoted(s, i):
    """
    Handles tokenization of unquoted text, interpreting backslashes as escape characters.
    """
    token_chars = []
    n = len(s)
    while i < n and not s[i].isspace() and s[i] not in ("'", '"'):
        if s[i] == '\\' and i + 1 < n:
            i += 1  # Skip the backslash
        token_chars.append(s[i])
        i += 1
    return ''.join(token_chars), i

def handle_single_quote(s, i):
    """
    Handles tokenization of single-quoted strings, preserving backslashes literally.
    """
    token_chars = []
    i += 1  # Skip the opening single quote
    n = len(s)
    while i < n:
        if s[i] == "'":
            i += 1  # Skip the closing single quote
            break
        token_chars.append(s[i])
        i += 1
    return ''.join(token_chars), i

def handle_double_quote(s, i):
    """
    Handles tokenization of double-quoted strings, interpreting backslashes as escape characters.
    """
    token_chars = []
    i += 1  # Skip the opening double quote
    n = len(s)
    while i < n:
        if s[i] == '\\' and i + 1 < n:
            i += 1  # Skip the backslash
        elif s[i] == '"':
            i += 1  # Skip the closing double quote
            break
        token_chars.append(s[i])
        i += 1
    return ''.join(token_chars), i



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

    new_dir = os.path.expanduser(args[0])  # Handle ~ expansion.
    if not os.path.isabs(new_dir):         # Convert relative paths to absolute.
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
        # Construct the command string to be executed by the shell.
        command_string = " ".join([command] + args)

        # Execute the command using /bin/sh -c to let the shell handle quoting.
        result = subprocess.run(["/bin/sh", "-c", command_string], capture_output=True, text=True, check=True)
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
