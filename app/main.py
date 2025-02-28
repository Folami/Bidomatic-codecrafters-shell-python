import os
import subprocess
import shlex
import sys
import readline

class Shell:
    def __init__(self):
        self.shell_home = os.getcwd()
        self.sh_builtins = ["echo", "exit", "type", "pwd", "cd"]
        self.completion_options = []  # Store completion options for the current cycle
        self.setup_autocomplete()

    def setup_autocomplete(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)  # Rename to match new method name


    def complete(self, text, state):
        """Autocompletion function for built-in commands and external executables with trailing space."""
        if state == 0:
            # First call for this input, generate options
            builtin_options = [cmd for cmd in self.sh_builtins if cmd.startswith(text)]
            external_options = set()
            path_env = os.environ.get("PATH", "")
            if path_env:
                paths = path_env.split(os.pathsep)
                for dir in paths:
                    try:
                        for file in os.listdir(dir):
                            file_path = os.path.join(dir, file)
                            if (os.path.isfile(file_path) and os.access(file_path, os.X_OK) and file.startswith(text) and file not in self.sh_builtins):
                                external_options.add(file)
                    except (OSError, FileNotFoundError):
                        continue
            self.completion_options = builtin_options + sorted(external_options)
            self.completion_state = state
        if len(self.completion_options) == 1:
            # Only one match, return it with a trailing space
            return self.completion_options[0] + " "
        elif len(self.completion_options) > 1 and self.completion_state == 0:
            # Multiple matches, ring a bell on the first TAB press
            print("\a", end="", flush=True)
            self.completion_state += 1
            return text
        elif len(self.completion_options) > 1 and self.completion_state == 1:
            # Multiple matches, print all matches on the second TAB press
            print("\n" + "  ".join(self.completion_options))
            readline.redisplay()  # Redisplay the prompt
            return text
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
    
    def run_external_command(self, command, args):
        """Executes an external command with support for redirection."""
        executable = self.find_executable(command)
        if not executable:
            print(f"{command}: command not found", file=sys.stderr)
            return

        output_file = None
        append_output_file = None
        error_file = None
        append_error_file = None
        command_with_args = [command]

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
                command_with_args.append(args[i])
                i += 1

        try:
            # Configure redirection targets
            stdout_target = None
            stderr_target = None

            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                stdout_target = open(output_file, "w")
            elif append_output_file:
                os.makedirs(os.path.dirname(append_output_file), exist_ok=True)
                stdout_target = open(append_output_file, "a")

            if error_file:
                os.makedirs(os.path.dirname(error_file), exist_ok=True)
                stderr_target = open(error_file, "w")
            elif append_error_file:
                os.makedirs(os.path.dirname(append_error_file), exist_ok=True)
                stderr_target = open(append_error_file, "a")

            # Use pipes only if no redirection for that stream
            stdout_pipe = subprocess.PIPE if not stdout_target else None
            stderr_pipe = subprocess.PIPE if not stderr_target else None

            # Start the process
            process = subprocess.Popen(
                command_with_args,
                stdout=stdout_target if stdout_target else stdout_pipe,
                stderr=stderr_target if stderr_target else stderr_pipe,
                text=True
            )

            # Handle output/error if piped
            if stdout_pipe or stderr_pipe:
                stdout_content, stderr_content = process.communicate()
                if stdout_pipe:
                    print(stdout_content or '', end='')
                if stderr_pipe:
                    print(stderr_content or '', file=sys.stderr, end='')
            else:
                process.wait()

            # Close redirected files
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

            # Check return code
            return_code = process.returncode
            if return_code != 0 and not (output_file or append_output_file or error_file or append_error_file):
                print(f"{command}: command failed with exit code {return_code}", file=sys.stderr)

        except Exception as e:
            print(f"{command}: {e}", file=sys.stderr)
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

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
