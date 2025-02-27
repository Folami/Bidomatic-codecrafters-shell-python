import os
import shlex
import subprocess
import sys

# List of shell built-in commands
sh_builtins = ['echo', 'exit', 'type', 'pwd', 'cd']

def input_prompt():
    """Displays the shell prompt and reads user input."""
    try:
        return input('$ ')
    except EOFError:
        return None

def execute_command(command, args):
    """Executes the given command with the provided arguments."""
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
    """Exits the shell."""
    sys.exit(0)

def execute_echo(args):
    """Executes the echo command with support for all redirection operators."""
    stdout_file = None      # For > or 1>
    append_stdout_file = None  # For >> or 1>>
    stderr_file = None      # For 2>
    append_stderr_file = None  # For 2>>
    content = []

    # Parse arguments for redirection
    i = 0
    while i < len(args):
        if args[i] in ['>', '1>'] and i + 1 < len(args):
            stdout_file = args[i + 1]
            i += 2
        elif args[i] in ['>>', '1>>'] and i + 1 < len(args):
            append_stdout_file = args[i + 1]
            i += 2
        elif args[i] == '2>' and i + 1 < len(args):
            stderr_file = args[i + 1]
            i += 2
        elif args[i] == '2>>' and i + 1 < len(args):
            append_stderr_file = args[i + 1]
            i += 2
        else:
            content.append(args[i])
            i += 1

    output = " ".join(content)

    try:
        # Handle stdout redirection (overwrite)
        if stdout_file:
            os.makedirs(os.path.dirname(stdout_file), exist_ok=True)
            with open(stdout_file, 'w') as f:
                f.write(output + '\n')
        # Handle stdout redirection (append)
        elif append_stdout_file:
            os.makedirs(os.path.dirname(append_stdout_file), exist_ok=True)
            with open(append_stdout_file, 'a') as f:
                f.write(output + '\n')
        else:
            print(output)

        # Handle stderr redirection (overwrite)
        if stderr_file:
            os.makedirs(os.path.dirname(stderr_file), exist_ok=True)
            with open(stderr_file, 'w') as f:
                f.write('')  # Echo has no stderr by default
        # Handle stderr redirection (append)
        elif append_stderr_file:
            os.makedirs(os.path.dirname(append_stderr_file), exist_ok=True)
            with open(append_stderr_file, 'a') as f:
                f.write('')  # Echo has no stderr by default

    except IOError as e:
        print(f"echo: {e}", file=sys.stderr)

def execute_type(args):
    """Implements the type command to identify command type."""
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
    """Prints the current working directory."""
    print(os.getcwd())

def execute_cd(args):
    """Changes the current working directory."""
    if not args:
        print("cd: missing operand")
        return

    new_dir = args[0]
    if new_dir.startswith('~'):
        new_dir = os.path.expanduser(new_dir)

    try:
        new_path = os.path.abspath(os.path.join(os.getcwd(), new_dir))
        if os.path.exists(new_path) and os.path.isdir(new_path):
            os.chdir(new_path)
        else:
            print(f"cd: {new_dir}: No such file or directory", file=sys.stderr)
    except Exception as e:
        print(f"cd: {new_dir}: {e}", file=sys.stderr)

def find_executable(command):
    """Searches for an executable in the PATH or current directory."""
    for dir in os.getenv('PATH', '').split(os.pathsep):
        file_path = os.path.join(dir, command)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    # Check current directory
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, command)
    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
        return file_path
    return None

def run_external_command(command, args):
    """Executes an external command with all redirection operators."""
    if not find_executable(command):
        print(f"{command}: command not found", file=sys.stderr)
        return

    stdout_file = None
    append_stdout_file = None
    stderr_file = None
    append_stderr_file = None
    command_args = []

    # Parse arguments for redirection
    i = 0
    while i < len(args):
        if args[i] in ['>', '1>'] and i + 1 < len(args):
            stdout_file = args[i + 1]
            i += 2
        elif args[i] in ['>>', '1>>'] and i + 1 < len(args):
            append_stdout_file = args[i + 1]
            i += 2
        elif args[i] == '2>' and i + 1 < len(args):
            stderr_file = args[i + 1]
            i += 2
        elif args[i] == '2>>' and i + 1 < len(args):
            append_stderr_file = args[i + 1]
            i += 2
        else:
            command_args.append(args[i])
            i += 1

    try:
        process_args = [command] + command_args
        process_builder = subprocess.Popen(
            process_args,
            stdout=subprocess.PIPE if not (stdout_file or append_stdout_file) else None,
            stderr=subprocess.PIPE if not (stderr_file or append_stderr_file) else None,
            text=True
        )

        # Handle redirections
        if stdout_file:
            os.makedirs(os.path.dirname(stdout_file), exist_ok=True)
            with open(stdout_file, 'w') as f:
                f.write(process_builder.stdout.read() if process_builder.stdout else '')
        elif append_stdout_file:
            os.makedirs(os.path.dirname(append_stdout_file), exist_ok=True)
            with open(append_stdout_file, 'a') as f:
                f.write(process_builder.stdout.read() if process_builder.stdout else '')

        if stderr_file:
            os.makedirs(os.path.dirname(stderr_file), exist_ok=True)
            with open(stderr_file, 'w') as f:
                f.write(process_builder.stderr.read() if process_builder.stderr else '')
        elif append_stderr_file:
            os.makedirs(os.path.dirname(append_stderr_file), exist_ok=True)
            with open(append_stderr_file, 'a') as f:
                f.write(process_builder.stderr.read() if process_builder.stderr else '')

        # Output to console if no redirection
        if not (stdout_file or append_stdout_file) and process_builder.stdout:
            for line in process_builder.stdout:
                print(line.rstrip('\n'))
        if not (stderr_file or append_stderr_file) and process_builder.stderr:
            for line in process_builder.stderr:
                print(line.rstrip('\n'), file=sys.stderr)

        return_code = process_builder.wait()
        if return_code != 0 and not (stdout_file or append_stdout_file or stderr_file or append_stderr_file):
            print(f"{command}: command failed with exit code {return_code}", file=sys.stderr)

    except IOError as e:
        print(f"{command}: {e}", file=sys.stderr)
    except subprocess.SubprocessError as e:
        print(f"{command}: process interrupted", file=sys.stderr)

def main():
    """Main loop of the shell."""
    while True:
        command_line = input_prompt()
        if not command_line or command_line.strip() == '':
            continue

        try:
            tokens = shlex.split(command_line, posix=True)
            if not tokens:
                continue
            command = tokens[0]
            command_args = tokens[1:]
            execute_command(command, command_args)
        except ValueError as e:
            print(f"Error parsing command: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()