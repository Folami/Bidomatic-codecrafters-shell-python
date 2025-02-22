import os
import shlex
import subprocess
import sys

# List of shell built-in commands
sh_builtins = ['echo', 'exit', 'type', 'pwd', 'cd']

def manual_tokenize(cmd_line):
    """
    Tokenizes the command line input, handling single quotes, double quotes, and backslashes.
    """
    tokens = []
    current = []
    single_quote = False
    double_quote = False
    escape = False

    for c in cmd_line:
        if escape:
            current.append(c)
            escape = False
        elif c == '\\':
            escape = True
        elif c == "'" and not double_quote:
            single_quote = not single_quote
        elif c == '"' and not single_quote:
            double_quote = not double_quote
        elif c.isspace() and not single_quote and not double_quote:
            if current:
                tokens.append(''.join(current))
                current = []
        else:
            current.append(c)

    if current:
        tokens.append(''.join(current))

    return tokens

def input_prompt():
    """
    Displays the shell prompt and reads user input.
    """
    try:
        return input('$ ')
    except EOFError:
        return 'exit'

def execute_command(command, args):
    """
    Executes the given command with the provided arguments.
    """
    if command == 'exit':
        exit_shell()
    elif command == 'echo':
        execute_echo(args)
    elif command == 'type':
        execute_type(args)
    elif command == 'pwd':
        execute_pwd()
    elif command == 'cd':
        execute_cd(args)
    else:
        run_external_command(command, args)

def exit_shell():
    """
    Exits the shell.
    """
    sys.exit(0)

def execute_echo(args):
    """
    Implements the echo command with support for the -n flag and output redirection.
    """
    if not args:
        print()
        return

    suppress_newline = False
    start_index = 0

    # Check for the -n flag
    if args[0] == '-n':
        suppress_newline = True
        start_index = 1

    output = ' '.join(args[start_index:])

    # Handle output redirection
    if '>' in args:
        try:
            redir_index = args.index('>')
            file_path = args[redir_index + 1]
            output = ' '.join(args[start_index:redir_index])
            write_file(output, file_path, suppress_newline)
        except (IndexError, IOError) as e:
            print(f"Error writing to file: {e}")
        return

    # Print to console
    if suppress_newline:
        print(output, end='')
    else:
        print(output)

def write_file(content, file_path, suppress_newline):
    """
    Writes the given content to the specified file.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
            if not suppress_newline:
                f.write('\n')
    except IOError as e:
        print(f"Error writing to file: {e}")

def execute_type(args):
    """
    Implements the type command to identify if a command is a shell builtin or an external executable.
    """
    if not args:
        print("type: missing operand")
        return

    target_command = args[0]

    if target_command in sh_builtins:
        print(f"{target_command} is a shell builtin")
    else:
        executable = find_executable(target_command)
        if executable:
            print(f"{target_command} is {executable}")
        else:
            print(f"{target_command}: not found")

def execute_pwd():
    """
    Prints the current working directory.
    """
    print(os.getcwd())

def execute_cd(args):
    """
    Changes the current working directory.
    """
    if not args:
        print("cd: missing operand")
        return

    new_dir = os.path.expanduser(args[0])

    try:
        os.chdir(new_dir)
    except OSError as e:
        print(f"cd: {new_dir}: {e.strerror}")

def find_executable(command):
    """
    Searches for the specified command in the system's PATH.
    """
    for dir in os.getenv('PATH', '').split(os.pathsep):
        potential_path = os.path.join(dir, command)
        if os.path.isfile(potential_path) and os.access(potential_path, os.X_OK):
            return potential_path
    return None

def run_external_command(command, args):
    """
    Executes an external command with the provided arguments.
    """
    try:
        subprocess.run([command] + args)
    except FileNotFoundError:
        print(f"{command}: command not found")
    except Exception as e:
        print(f"{command}: {e}")

def main():
    """
    Main loop of the shell.
    """
    while True:
        command_line = input_prompt()
        if not command_line:
            continue

        tokens = manual_tokenize(command_line)
        if not tokens:
            continue

        command = tokens[0]
        command_args = tokens[1:]

        execute_command(command, command_args)

if __name__ == '__main__':
    main()
