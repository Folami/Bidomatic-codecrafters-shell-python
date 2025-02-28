import os
import subprocess
import shlex
import sys

class Shell:
    def __init__(self):
        self.shell_home = os.getcwd()
        self.sh_builtins = ["echo", "exit", "type", "pwd", "cd"]

    def input_prompt(self):
        return input("$ ")

    def execute_command(self, command, args):
        if command in self.sh_builtins:
            getattr(self, f"execute_{command}")(args)
        else:
            self.run_external_command(command, args)

    def execute_exit(self, args):
        sys.exit(0)

    def execute_echo(self, args):
        output_file = None
        append_output_file = None
        error_file = None
        append_error_file = None
        echo_args = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in [">", "1>"]:
                if i + 1 < len(args):
                    output_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for redirection", file=sys.stderr)
                    return
            elif arg in [">>", "1>>"]:
                if i + 1 < len(args):
                    append_output_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for append redirection", file=sys.stderr)
                    return
            elif arg == "2>":
                if i + 1 < len(args):
                    error_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for error redirection", file=sys.stderr)
                    return
            elif arg == "2>>":
                if i + 1 < len(args):
                    append_error_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for error append redirection", file=sys.stderr)
                    return
            else:
                echo_args.append(arg)
            i += 1

        output = " ".join(echo_args)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output + "\n")
        elif append_output_file:
            with open(append_output_file, "a") as f:
                f.write(output + "\n")
        else:
            print(output)

    def execute_type(self, args):
        if not args:
            print("type: missing operand")
            return
        command = args[0]
        if command in self.sh_builtins:
            print(f"{command} is a shell builtin")
        else:
            executable = self.find_executable(command)
            if executable:
                print(f"{command} is {executable}")
            else:
                print(f"{command}: not found")

    def execute_pwd(self, args):
        print(os.getcwd())

    def execute_cd(self, args):
        if not args:
            print("cd: missing operand")
            return
        new_dir = args[0]
        if new_dir.startswith("~"):
            new_dir = os.path.expanduser(new_dir)
        try:
            os.chdir(new_dir)
        except FileNotFoundError:
            print(f"cd: {new_dir}: No such file or directory", file=sys.stderr)

    def find_executable(self, command):
        path_env = os.environ.get("PATH", "").split(os.pathsep)
        for dir in path_env:
            file_path = os.path.join(dir, command)
            if os.path.exists(file_path) and os.access(file_path, os.X_OK):
                return file_path
        return None

    def run_external_command(self, command, args):
        executable = self.find_executable(command)
        if not executable:
            print(f"{command}: command not found", file=sys.stderr)
            return

        output_file = None
        append_output_file = None
        error_file = None
        append_error_file = None
        command_with_args = [command]

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in [">", "1>"]:
                if i + 1 < len(args):
                    output_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for redirection", file=sys.stderr)
                    return
            elif arg in [">>", "1>>"]:
                if i + 1 < len(args):
                    append_output_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for append redirection", file=sys.stderr)
                    return
            elif arg == "2>":
                if i + 1 < len(args):
                    error_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for error redirection", file=sys.stderr)
                    return
            elif arg == "2>>":
                if i + 1 < len(args):
                    append_error_file = args[i + 1]
                    i += 1
                else:
                    print("Syntax error: no file specified for error append redirection", file=sys.stderr)
                    return
            else:
                command_with_args.append(arg)
            i += 1

        with open(output_file, "w") if output_file else open(os.devnull, "w") as out,
             open(error_file, "w") if error_file else open(os.devnull, "w") as err:
            process = subprocess.Popen(command_with_args, stdout=out, stderr=err)
            process.wait()

    def run(self):
        while True:
            command_line = self.input_prompt()
            if not command_line:
                continue
            try:
                tokens = shlex.split(command_line)
                if not tokens:
                    continue
                command = tokens[0]
                args = tokens[1:]
                self.execute_command(command, args)
            except Exception as e:
                print(f"Error parsing command: {e}", file=sys.stderr)

if __name__ == "__main__":
    shell = Shell()
    shell.run()
