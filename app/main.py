import sys
import os
import shlex
import subprocess

# List of built-in commands
shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

def main():
    """Main shell loop."""
    while True:
        sys.stdout.write("$ ")
        try:
            command_line = input().strip()
            if not command_line:
                continue
            
            # Tokenize the input command line
            tokens = split_outside_quotes(command_line)
            if not tokens:
                continue
            
            # Process arguments
            command, args = process_tokens(tokens)
            
            # Execute the command
            execute_command(command, args)
        except EOFError:
            break  # Exit on end-of-file (Ctrl+D)
        except Exception as e:
            print(f"An error occurred: {e}")

def split_outside_quotes(s):
    """Splits a command line into tokens while respecting single and double quotes."""
    parts = []
    in_single_quotes = False
    in_double_quotes = False
    current_part = ""
    
    for char in s:
        if char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
        elif char == " " and not in_single_quotes and not in_double_quotes:
            if current_part:
                parts.append(current_part)
                current_part = ""
        else:
            current_part += char
    
    if current_part:
        parts.append(current_part)
    return parts

def process_tokens(tokens):
    """Processes tokens, handling single quotes and backslashes appropriately."""
    command, *args = tokens
    processed_args = []
    
    for arg in args:
        if arg.startswith("'") and arg.endswith("'"):
            # Remove single quotes and handle backslashes literally
            processed_arg = arg[1:-1].replace("\\", "\\\\")
            processed_args.append(processed_arg)
        else:
            try:
                shlex_split_args = shlex.split(arg)  # Use shlex for double quotes
                processed_args.extend(shlex_split_args)
            except:
                processed_args.append(arg)
    
    return command, processed_args

def execute_command(command, args):
    """Determines whether the command is built-in or external and executes it."""
    match command:
        case "exit":
            sys.exit(0)
        case "echo":
            print(" ".join(args))
        case "type":
            execute_type(args)
        case "pwd":
            print(os.getcwd())
        case "cd":
            execute_cd(args)
        case _:
            run_external_command(command, args)

def execute_type(args):
    """Handles the 'type' built-in command."""
    if not args:
        print("type: missing operand")
        return
    
    target = args[0]
    if target in shBuiltins:
        print(f"{target} is a shell builtin")
    else:
        executable = find_executable(target)
        if executable:
            print(f"{target} is {executable}")
        else:
            print(f"{target}: not found")

def execute_cd(args):
    """Handles the 'cd' built-in command."""
    if not args:
        print("cd: missing operand")
        return
    
    new_dir = os.path.expanduser(args[0])  # Expand '~' to home directory
    if not os.path.isabs(new_dir):
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
    """Searches for an executable file in the system's PATH."""
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        file_path = os.path.join(directory, command)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    return None

def run_external_command(command, args):
    """Executes an external command with arguments."""
    try:
        result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
        print(result.stdout, end="")  # Print command output
    except subprocess.CalledProcessError as e:
        print(f"{command}: command failed with exit code {e.returncode}")
        print(e.stderr, end="", file=sys.stderr)  # Print error to stderr
    except FileNotFoundError:
        print(f"{command}: command not found")
    except Exception as e:
        print(f"An error occurred while running {command}: {e}")

if __name__ == "__main__":
    main()
