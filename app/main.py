import sys
import os
import subprocess

shBuiltins = ["echo", "exit", "type"]

def main():
    while True:
        sys.stdout.write("$ ")
        command_line = input()
        if not command_line:
            continue
        try:
            # Wait for user input and split on whitespace.
            command, *args = input().split(" ")
            match command:
                case "exit":
                    break
                case "echo":
                    print(" ".join(args))
                case "type":
                    if not args: # Check if argument is provided
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
                case _:  # Default case: Try running as an external program
                        run_external_command(command, args)  # Call the new function

        except EOFError:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
    return


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
        result = subprocess.run([command] + args)
        if result.returncode != 0:
            print(f"{command}: command failed with exit code {result.returncode}")
    except FileNotFoundError:
        print(f"{command}: command not found")
    except Exception as e:
        print(f"{command}: error: {e}")
    except subprocess.CalledProcessError as e:
        print(f"{command}: command failed with exit code {e.returncode}")
        print(e.stderr, end="", file=sys.stderr) # Print error to stderr
    
if __name__ == "__main__":
    main()
