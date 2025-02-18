import sys
import os

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
        # Wait for user input and split on whitespace.
        command, *args = input().split(" ")
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
                sys.stdout.write(f"{command}: command not found\n")
    return

if __name__ == "__main__":
    main()
