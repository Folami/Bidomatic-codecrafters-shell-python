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
    stdout_redirect = None
    stderr_redirect = None
    stdout_append = None
    stderr_append = None
    content = []

    i = 0
    while i < len(args):
        if args[i] in ['>', '1>'] and i + 1 < len(args):
            stdout_redirect = args[i + 1]
            i += 2
        elif args[i] in ['>>', '1>>'] and i + 1 < len(args):
            stdout_append = args[i + 1]
            i += 2
        elif args[i] == '2>' and i + 1 < len(args):
            stderr_redirect = args[i + 1]
            i += 2
        elif args[i] == '2>>' and i + 1 < len(args):
            stderr_append = args[i + 1]
            i += 2
        else:
            content.append(args[i])
            i += 1

    output = " ".join(content)

    try:
        if stdout_redirect:
            with open(stdout_redirect, 'w') as f:
                f.write(output + '\n')
        elif stdout_append:
            with open(stdout_append, 'a') as f:
                f.write(output + '\n')
        elif stderr_redirect:
            with open(stderr_redirect, 'w') as f:
                f.write("")
        elif stderr_append:
            with open(stderr_append, 'a') as f:
                f.write("")
        else:
            print(output)
    except IOError as e:
        print(f"echo: {e}", file=sys.stderr)

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
    try:
        stdout_redirect = None
        stderr_redirect = None
        stdout_append = None
        stderr_append = None
        stdout_file = None
        stderr_file = None

        # Check for stdout redirection
        if '>' in args or '1>' in args:
            redirect_symbol = '>' if '>' in args else '1>'
            idx = args.index(redirect_symbol)
            if idx + 1 < len(args):
                stdout_file = args[idx + 1]
                args = args[:idx] + args[idx+2:]
                stdout_redirect = open(stdout_file, 'w')
            else:
                print("Syntax error: no file specified for stdout redirection", file=sys.stderr)
                return
        elif '>>' in args or '1>>' in args:
            redirect_symbol = '>>' if '>>' in args else '1>>'
            idx = args.index(redirect_symbol)
            if idx + 1 < len(args):
                stdout_file = args[idx + 1]
                args = args[:idx] + args[idx+2:]
                stdout_append = open(stdout_file, 'a')
            else:
                print("Syntax error: no file specified for stdout append redirection", file=sys.stderr)
                return

        # Check for stderr redirection
        if '2>' in args:
            idx = args.index('2>')
            if idx + 1 < len(args):
                stderr_file = args[idx + 1]
                args = args[:idx] + args[idx+2:]
                stderr_redirect = open(stderr_file, 'w')
            else:
                print("Syntax error: no file specified for stderr redirection", file=sys.stderr)
                return
        elif '2>>' in args:
            idx = args.index('2>>')
            if idx + 1 < len(args):
                stderr_file = args[idx + 1]
                args = args[:idx] + args[idx+2:]
                stderr_append = open(stderr_file, 'a')
            else:
                print("Syntax error: no file specified for stderr append redirection", file=sys.stderr)
                return

        # Execute the command with appropriate redirections
        result = subprocess.run(
            [command] + args,
            stdout=stdout_redirect or stdout_append or subprocess.PIPE,
            stderr=stderr_redirect or stderr_append or subprocess.PIPE,
            text=True
        )

        # Print stdout to console if not redirected
        if result.stdout and not (stdout_redirect or stdout_append):
            print(result.stdout.strip())

        # Print stderr to console if not redirected
        if result.stderr and not (stderr_redirect or stderr_append):
            print(result.stderr.strip(), file=sys.stderr)

        if result.returncode != 0 and not (stderr_redirect or stderr_append):
            print(f"{command}: command failed with exit code {result.returncode}", file=sys.stderr)

    except FileNotFoundError:
        print(f"{command}: command not found", file=sys.stderr)
    except Exception as e:
        print(f"{command}: {e}", file=sys.stderr)
    finally:
        # Close any opened files
        if stdout_redirect:
            stdout_redirect.close()
        if stderr_redirect:
            stderr_redirect.close()
        if stdout_append:
            stdout_append.close()
        if stderr_append:
            stderr_append.close()

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

if __name