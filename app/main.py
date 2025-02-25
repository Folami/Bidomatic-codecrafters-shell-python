import os
import shlex
import subprocess
import sys

# List of shell built-in commands
sh_builtins = ['echo', 'exit', 'type', 'pwd', 'cd']

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

def execute_echo(args):
    """
    Executes the echo command.
    """
    print(" ".join(args))

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

        try:
            # Use shlex to split the command line into tokens
            tokens = shlex.split(command_line, posix=True)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue

        if not tokens:
            continue

        command = tokens[0]
        command_args = tokens[1:]

        execute_command(command, command_args)

if __name__ == '__main__':
    main()
