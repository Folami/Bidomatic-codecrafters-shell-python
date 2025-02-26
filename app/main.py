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
    Executes the echo command and handles redirection.
    """
    if '>' in args or '1>' in args:
        try:
            # Determine the redirection operator and its index
            if '>' in args:
                redirect_index = args.index('>')
            else:
                redirect_index = args.index('1>')

            # Extract the output file path
            output_file = args[redirect_index + 1]

            # Content to be written is everything before the redirection operator
            content = " ".join(args[:redirect_index])

            # Write the content to the specified file
            with open(output_file, 'w') as f:
                f.write(content + '\n')
        except (IndexError, IOError) as e:
            print(f"echo: error handling redirection: {e}")
    else:
        # No redirection; print to standard output
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
    Executes an external command with the provided arguments and handles output and error redirection.
    """
    stdout_redirect = None
    stderr_redirect = None
    stdout_file = None
    stderr_file = None

    # Parse arguments to handle redirection
    i = 0
    while i < len(args):
        if args[i] in ('>', '1>'):
            if i + 1 < len(args):
                stdout_file = args[i + 1]
                del args[i:i + 2]
            else:
                print("Syntax error: no file specified for stdout redirection")
                return
        elif args[i] == '2>':
            if i + 1 < len(args):
                stderr_file = args[i + 1]
                del args[i:i + 2]
            else:
                print("Syntax error: no file specified for stderr redirection")
                return
        else:
            i += 1

    # Open files for redirection if specified
    if stdout_file:
        try:
            stdout_redirect = open(stdout_file, 'w')
        except IOError as e:
            print(f"Error opening file for stdout redirection: {e}")
            return
    if stderr_file:
        try:
            stderr_redirect = open(stderr_file, 'w')
        except IOError as e:
            print(f"Error opening file for stderr redirection: {e}")
            return

    try:
        # Execute the command with appropriate redirections
        result = subprocess.run(
            [command] + args,
            stdout=stdout_redirect or subprocess.PIPE,
            stderr=stderr_redirect or subprocess.PIPE,
            text=True
        )

        # If stderr was not redirected to a file, print it to the console
        if result.stderr and not stderr_redirect:
            print(result.stderr.strip())

    except FileNotFoundError:
        print(f"{command}: command not found")
    except subprocess.CalledProcessError as e:
        print(f"{command}: command failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr.strip())
    except Exception as e:
        print(f"{command}: {e}")
    finally:
        # Close any opened files
        if stdout_redirect:
            stdout_redirect.close()
        if stderr_redirect:
            stderr_redirect.close()



def handle_redirection(command, args):
    """
    Handles output redirection for a command.
    """
    redirect_index = -1
    for i, arg in enumerate(args):
        if arg == '>':
            redirect_index = i
            break

    if redirect_index == -1:
        return command, args, None

    output_file = args[redirect_index + 1] if redirect_index + 1 < len(args) else None
    if not output_file:
        print("Syntax error: no file specified for redirection")
        return None, None, None

    return command, args[:redirect_index], output_file


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

