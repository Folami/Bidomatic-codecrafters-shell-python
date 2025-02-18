import sys
import os
import subprocess

shBuiltins = ["echo", "exit", "type", "pwd", "cd"]

def find_executable(command):
    """Search for an executable file in the PATH and return its full path if found."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(directory, command)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None

def main():
    while True:
        sys.stdout.write("$ ")
        # Read input and split into command and arguments.
        tokens = input().split(" ")
        if not tokens or tokens[0] == "":
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
                    # Expand the '~' character to the user's home directory.
                    new_dir = os.path.expanduser(args[0])
                    # If the path is not absolute, convert it to an absolute path.
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
                # Attempt to run the external command with the provided arguments.
                try:
                    result = subprocess.run([command] + args)
                    if result.returncode != 0:
                        print(f"{command}: command failed with exit code {result.returncode}")
                except FileNotFoundError:
                    print(f"{command}: command not found")
                except Exception as e:
                    print(f"{command}: error: {e}")
    return

if __name__ == "__main__":
    main()
