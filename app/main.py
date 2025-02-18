import sys
import os
import shlex
import subprocess

shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

def main():
    while True:
        sys.stdout.write("$ ")
        command_line = input()
        if not command_line:
            continue

        try:
            # 1. Split by spaces outside of quotes (like a simple shell)
            tokens = split_outside_quotes(command_line)
            if not tokens:
                continue

            args = []
            command, *parts = tokens
            # 2. Process each argument, handling single quotes and backslashes
            for arg in parts:
                if arg.startswith("'") and arg.endswith("'"):
                    # Remove the single quotes and handle backslashes literally
                    processed_arg = arg[1:-1].replace("\\", "\\\\") # Double backslashes to escape them
                    args.append(processed_arg)
                else:
                    try:
                        shlex_split_args = shlex.split(arg) # Use shlex for double quotes and other escapes if no single quote is found
                        args.extend(shlex_split_args)
                    except:
                        args.append(arg) # If shlex fails, append the original arg

            match command:
                case "exit":
                    break
                case "echo":
                    print(" ".join(args))
                case "type":
                    if not args:
                        print("type: missing operand")
                    elif args[0] in shBuiltins:
                        print(f"{args[0]} is a shell builtin")
                    else:
                        executable = find_executable(args[0])
                        if executable:
                            print(f"{args[0]} is {executable}")
                        else:
                            print(f"{args[0]}: not found")
                case "pwd":
                    print(os.getcwd())
                case "cd":
                    if not args:
                        print("cd: missing operand")
                    else:
                        new_dir = os.path.expanduser(args[0])
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
                case _:
                    run_external_command(command, args)

        except EOFError:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

def split_outside_quotes(s):
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
    

    while True:
        sys.stdout.write("$ ")
        command_line = input()
        if not command_line:
            continue

        # Tokenize using our custom tokenizer.
        tokens = custom_split(line)
        if not tokens:
            continue

        command, *args = tokens

        match command:
            case "exit":
                break
            case "echo":
                print(" ".join(args))
            case "type":
                if not args:
                    print("type: missing operand")
                elif args[0] in shBuiltins:
                    print(f"{args[0]} is a shell builtin")
                else:
                    executable = find_executable(args[0])
                    if executable:
                        print(f"{args[0]} is {executable}")
                    else:
                        print(f"{args[0]}: not found")
            case "pwd":
                print(os.getcwd())
            case "cd":
                if not args:
                    print("cd: missing operand")
                else:
                    new_dir = os.path.expanduser(args[0])
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
            case default:
                # Attempt to run external commands.
                try:
                    result = subprocess.run([command] + args)
                    if result.returncode != 0:
                        print(f"{command}: command failed with exit code {result.returncode}")
                except FileNotFoundError:
                    print(f"{command}: command not found")
                except Exception as e:
                    print(f"{command}: error: {e}")


def find_executable(command):
    path_env = os.environ.get("PATH")
    if path_env:
        for directory in path_env.split(os.pathsep):
            file_path = os.path.join(directory, command)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path
    return None

def run_external_command(command, args):
    try:
        # subprocess.run handles the execution and waiting for the command
        result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
        print(result.stdout, end="") # Print the output of the command
    except subprocess.CalledProcessError as e:
        print(f"{command}: command failed with exit code {e.returncode}")
        print(e.stderr, end="", file=sys.stderr) # Print error to stderr
    except FileNotFoundError:
        print(f"{command}: command not found")
    except Exception as e:
        print(f"An error occurred while running {command}: {e}")



if __name__ == "__main__":
    main()

