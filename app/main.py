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

def execute_command(command_line):
    """
    Executes the given command line, handling built-ins and external commands.
    """
    # Split the command line into command and arguments
    try:
        tokens = shlex.split(command_line, posix=True)
    except ValueError as e:
        print(f"Error parsing command: {e}")
        return

    if not tokens:
        return

    # Check for output redirection
    if '>' in tokens:
        # Ensure there's exactly one '>' and it's not the first or last token
        if tokens.count('>') == 1 and tokens[-2] == '>':
            command = tokens[0]
            args = tokens[1:-2]
            output_file = tokens[-1]
            redirect_output = True
        else:
            print("Syntax error: invalid use of '>'")
            return
    else:
        command = tokens[0]
        args = tokens[1:]
        output_file = None
        redirect_output = False

    if command in sh_builtins:
        execute_builtin(command, args)
    else:
        run_external_command(command, args, output_file, redirect_output)

def execute_builtin(command, args):
    """
    Executes a shell built-in command.
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
        print(f"{command}: command not found")

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

def run_external_command(command, args, output_file=None, redirect_output=False):
    """
    Executes an external command with the provided arguments.
    """
    try:
        if redirect_output and output_file:
            with open(output_file, 'w') as outfile:
                subprocess.run([command] + args, stdout=outfile, stderr=subprocess.PIPE)
        else:
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
        execute_command(command_line)

if __name__ == '__main__':
    main()
