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
            tokens = shlex.split(command_line)
            if not tokens:
                continue

            command = tokens[0]
            args = tokens[1:]

            match command:
                case "exit":
                    break
                case "echo":
                    print(" ".join(args))
                case "type":
                    if not args:
                        print("type: missing operand")
                        continue

                    target_command = args[0]
                    if target_command in shBuiltins:
                        print(f"{target_command} is a shell builtin")
                    else:
                        path = find_executable(target_command)
                        if path:
                            print(f"{target_command} is {path}")
                        else:
                            print(f"{target_command} not found")
                case "pwd":
                    print(os.getcwd())
                case "cd":
                    if not args:
                        print("cd: missing operand")
                    else:
                        path = args[0]
                        if path.startswith("~"):  # Handle ~ character
                            home_dir = os.path.expanduser("~")  # Get home directory
                            if len(path) > 1:
                                path = os.path.join(home_dir, path[1:]) # Join home directory with the rest of the path
                            else:
                                path = home_dir # If path is only ~, change to home directory
                        try:
                            os.chdir(path)
                        except FileNotFoundError:
                            print(f"cd: {path}: No such file or directory")
                        except NotADirectoryError:
                            print(f"cd: {path}: Not a directory")
                        except OSError as e:
                            print(f"cd: {path}: {e}")
                case _:
                    run_external_command(command, args)

        except EOFError:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

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