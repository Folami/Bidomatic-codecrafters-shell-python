import os
import subprocess
import shlex
import sys
import readline

class Shell:
    def __init__(self):
        self.shell_home = os.getcwd()
        self.sh_builtins = ["echo", "exit", "type", "pwd", "cd"]
        self.setup_autocomplete()

    def setup_autocomplete(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete_builtin)

    def complete_builtin(self, text, state):
        """Autocompletion function for built-in commands with trailing space."""
        options = [cmd for cmd in self.sh_builtins if cmd.startswith(text)]
        if state < len(options):
            return options[state] + " "  # Add trailing space to completed command
        return None

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
        """Executes the echo command with proper redirection handling."""
        output_file = None
        append_output_file = None
        error_file = None
        append_error_file = None
        echo_args = []

        # Parse arguments for redirection
        i = 0
        while i < len(args):
            if args[i] in [">", "1>"]:
                if i + 1 < len(args):
                    output_file = args[i + 1]
                    i += 2  # Skip operator and file name
                else:
                    print("Syntax error: no file specified for redirection", file=sys.stderr)
                    return
            elif args[i] in [">>", "1>>"]:
                if i + 1 < len(args):
                    append_output_file = args[i + 1]
                    i += 2
                else:
                    print("Syntax error: no file specified for append redirection", file=sys.stderr)
                    return
            elif args[i] == "2>":
                if i + 1 < len(args):
                    error_file = args[i + 1]
                    i += 2
                else:
                    print("Syntax error: no file specified for error redirection", file=sys.stderr)
                    return
            elif args[i] == "2>>":
                if i + 1 < len(args):
                    append_error_file = args[i + 1]
                    i += 2
                else:
                    print("Syntax error: no file specified for error append redirection", file=sys.stderr)
                    return
            else:
                echo_args.append(args[i])
                i += 1

        output = " ".join(echo_args)

        try:
            # Handle stdout redirection
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(output + "\n")
            elif append_output_file:
                os.makedirs(os.path.dirname(append_output_file), exist_ok=True)
                with open(append_output_file, "a") as f:
                    f.write(output + "\n")
            else:
                print(output)

            # Handle stderr redirection
            if error_file:
                os.makedirs(os.path.dirname(error_file), exist_ok=True)
                with open(error_file, "w") as f:
                    f.write("")  # No stderr for echo by default
            elif append_error_file:
                os.makedirs(os.path.dirname(append_error_file), exist_ok=True)
                with open(append_error_file, "a") as f:
                    f.write("")  # No stderr for echo by default

        except IOError as e:
            print(f"echo: {e}", file=sys.stderr)

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
        path_env = os.environ.get("PATH")
        if path_env:
            paths = path_env.split(os.pathsep)
            for dir in paths:
                file_path = os.path.join(dir, command)
                if os.path.exists(file_path) and os.access(file_path, os.X_OK):
                    return file_path
        # Check in the current directory
        file_path = os.path.join(os.getcwd(), command)
        if os.path.exists(file_path) and os.access(file_path, os.X_OK):
            return file_path
        return None

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
