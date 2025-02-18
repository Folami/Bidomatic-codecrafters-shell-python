import sys
import os
import subprocess

shBuiltins = ["echo", "exit", "type"]

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
        # (Note: this simple split does not handle quotes/escapes.)
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
