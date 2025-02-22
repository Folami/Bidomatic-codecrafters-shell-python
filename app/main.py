import os
import subprocess
import sys

sh_builtins = ["echo", "exit", "type", "pwd", "cd"]

class Tokenizer:
    @staticmethod
    def manual_tokenize(cmd_line):
        tokens = []
        current = ""
        single_quote = False
        double_quote = False
        escape = False

        for c in cmd_line:
            if escape:
                current += c
                escape = False
            elif c == '\\':
                escape = True
            elif c == "'" and not double_quote:
                if single_quote:
                    tokens.append(current)
                    current = ""
                single_quote = not single_quote
            elif c == '"' and not single_quote:
                if double_quote:
                    tokens.append(current)
                    current = ""
                double_quote = not double_quote
            elif c.isspace() and not single_quote and not double_quote:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += c

        if current:
            tokens.append(current)
        return tokens

def input_prompt():
    sys.stdout.write("$ ")
    return input()

def execute_command(command, args):
    if command == "exit":
        exit_shell()
    elif command == "echo":
        execute_echo(args)
    elif command == "type":
        execute_type(args)
    elif command == "pwd":
        execute_pwd()
    elif command == "cd":
        execute_cd(args)
    else:
        run_external_command(command, args)

def exit_shell():
    sys.exit(0)

def execute_echo(args):
    suppress_newline = False
    start_index = 0

    if args and args[0] == "-n":
        suppress_newline = True
        start_index = 1

    join_echo_args(args, start_index, suppress_newline)

def join_echo_args(args, start_index, suppress_newline):
    output = ""
    for i in range(start_index, len(args)):
        if args[i] == ">" and i + 1 < len(args):
            file_path = args[i + 1].replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
            write_file(output, file_path, suppress_newline)
            return
        output += args[i]
        if i < len(args) - 1:
            output += " "

    if suppress_newline:
        print(output, end="")
    else:
        print(output)

def write_file(content, file_path, suppress_newline):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
            if not suppress_newline:
                f.write("\n")
    except Exception as e:
        sys.stderr.write(f"Error writing to file: {e}\n")

def execute_type(args):
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
    print(os.getcwd())

def execute_cd(args):
    if not args:
        print("cd: missing operand")
        return

    new_dir = os.path.abspath(os.path.expanduser(args[0]))
    try:
        os.chdir(new_dir)
    except Exception as e:
        print(f"cd: {args[0]}: {e}")

def find_executable(command):
    path_env = os.environ.get("PATH")
    if path_env:
        for directory in path_env.split(os.pathsep):
            file_path = os.path.join(directory, command)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path
    return None

def run_external_command(command, args):
    command_with_args = [command] + args
    try:
        process = subprocess.Popen(command_with_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
        process.wait()
    except Exception as e:
        print(f"{command}: {e}")

def main():
    while True:
        command_line = input_prompt()
        if not command_line:
            continue
        try:
            tokens = Tokenizer.manual_tokenize(command_line)
            if not tokens:
                continue
            command = tokens[0]
            command_args = tokens[1:]
            execute_command(command, command_args)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()