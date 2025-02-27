import os
import sys
import shlex
import subprocess

def main():
    while True:
        try:
            command_line = input("$ ").strip()
            if not command_line:
                continue
            tokens = shlex.split(command_line, posix=True)
            execute_command(tokens)
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

def execute_command(tokens):
    if not tokens:
        return
    command, *args = tokens
    if command == "exit":
        sys.exit(0)
    elif command == "echo":
        execute_echo(args)
    elif command == "pwd":
        print(os.getcwd())
    elif command == "cd":
        execute_cd(args)
    elif command == "type":
        execute_type(args)
    else:
        run_external_command(command, args)

def execute_cd(args):
    if not args:
        print("cd: missing operand", file=sys.stderr)
        return
    path = os.path.expanduser(args[0])
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {args[0]}: No such file or directory", file=sys.stderr)
    except NotADirectoryError:
        print(f"cd: {args[0]}: Not a directory", file=sys.stderr)
    except PermissionError:
        print(f"cd: {args[0]}: Permission denied", file=sys.stderr)

def execute_type(args):
    if not args:
        print("type: missing operand", file=sys.stderr)
        return
    command = args[0]
    if command in {"echo", "exit", "type", "pwd", "cd"}:
        print(f"{command} is a shell builtin")
    else:
        path = find_executable(command)
        if path:
            print(f"{command} is {path}")
        else:
            print(f"{command}: not found", file=sys.stderr)

def find_executable(command):
    if os.path.isabs(command) and os.access(command, os.X_OK):
        return command
    for directory in os.getenv("PATH", "").split(os.pathsep):
        full_path = os.path.join(directory, command)
        if os.access(full_path, os.X_OK):
            return full_path
    return None

def execute_echo(args):
    output, stdout_redirect, stderr_redirect = parse_redirections(args)
    if stdout_redirect:
        with open(stdout_redirect, "w") as f:
            f.write(output + "\n")
    else:
        print(output)

def parse_redirections(args):
    output, stdout_redirect, stderr_redirect = [], None, None
    i = 0
    while i < len(args):
        if args[i] in {">", "1>"} and i + 1 < len(args):
            stdout_redirect = args[i + 1]
            i += 1
        elif args[i] == "2>" and i + 1 < len(args):
            stderr_redirect = args[i + 1]
            i += 1
        else:
            output.append(args[i])
        i += 1
    return " ".join(output), stdout_redirect, stderr_redirect

def run_external_command(command, args):
    path = find_executable(command)
    if not path:
        print(f"{command}: command not found", file=sys.stderr)
        return
    
    stdout_redirect, stderr_redirect = None, None
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] in {">", "1>"} and i + 1 < len(args):
            stdout_redirect = args[i + 1]
            i += 1
        elif args[i] == "2>" and i + 1 < len(args):
            stderr_redirect = args[i + 1]
            i += 1
        else:
            filtered_args.append(args[i])
        i += 1
    
    with open(stdout_redirect, "w") if stdout_redirect else sys.stdout as stdout,
         open(stderr_redirect, "w") if stderr_redirect else sys.stderr as stderr:
        process = subprocess.run([path] + filtered_args, stdout=stdout, stderr=stderr)
        if process.returncode != 0:
            print(f"{command}: exited with status {process.returncode}", file=sys.stderr)

if __name__ == "__main__":
    main()
