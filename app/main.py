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

def custom_split(s):
    """
    Splits the input string into tokens, supporting:
      - Unquoted words separated by whitespace.
      - Double-quoted strings.
      - Single-quoted strings.
      - Backslashes as escape characters in all contexts, even within single quotes.
    
    For example:
      Input: echo 'It\'s a test' "Another \"test\"" unquoted\ word
      Output: ['echo', "It's a test", 'Another "test"', 'unquoted word']
    """
    tokens = []
    current = []
    state = None  # None, "single", or "double"
    escape = False
    # Map common escape sequences.
    escapes = {'n': '\n', 't': '\t', 'r': '\r'}

    for c in s:
        if escape:
            # Append the mapped escape or the character itself.
            current.append(escapes.get(c, c))
            escape = False
            continue

        if c == '\\':
            escape = True
            continue

        if state is None:
            # Not inside any quotes.
            if c in " \t":
                if current:
                    tokens.append(''.join(current))
                    current = []
            elif c == "'":
                state = "single"
            elif c == '"':
                state = "double"
            else:
                current.append(c)
        elif state == "double":
            if c == '"':
                state = None
            else:
                current.append(c)
        elif state == "single":
            if c == "'":
                state = None
            else:
                # Process backslashes within single quotes as escapes.
                current.append(c)
    if escape:
        # Append a trailing backslash if needed.
        current.append('\\')
    if current:
        tokens.append(''.join(current))
    return tokens

def main():
    while True:
        sys.stdout.write("$ ")
        try:
            line = input()
        except EOFError:
            break  # Exit on end-of-file (Ctrl+D)
        
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

if __name__ == "__main__":
    main()
