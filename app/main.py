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
        self.completion_state = 0  # Track TAB presses for multiple completions
        self.setup_autocomplete()

    def setup_autocomplete(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)

    def complete(self, text, state):
        if state == 0:
            self.completion_state += 1
            self.completion_options = self._get_completion_options(text)
            if len(self.completion_options) > 1:
                common_prefix = os.path.commonprefix(self.completion_options)
                if common_prefix != text:
                    return common_prefix + " "
            if len(self.completion_options) > 1 and self.completion_state == 1:
                sys.stdout.write("\a")
                sys.stdout.flush()
                return None
            elif len(self.completion_options) > 1 and self.completion_state == 2:
                print("\n" + "  ".join(self.completion_options))
                sys.stdout.write("$ " + text)
                sys.stdout.flush()
                self.completion_state = 0
                return None
        if state < len(self.completion_options):
            return self.completion_options[state] + " "
        self.completion_state = 0
        return None

    def _get_completion_options(self, text):
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
        return builtin_options + sorted(external_options)


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
        output, error = self._parse_redirection(args)
        output_str = " ".join(output)
        self._handle_redirection(output_str, error)

    def _parse_redirection(self, args):
        output_args = []
        redirections = {"stdout": None, "stderr": None}
        i = 0
        while i < len(args):
            if args[i] in [">", "1>"]:
                redirections["stdout"] = (args[i + 1], "w")
                i += 2
            elif args[i] in [">>", "1>>"]:
                redirections["stdout"] = (args[i + 1], "a")
                i += 2
            elif args[i] == "2>":
                redirections["stderr"] = (args[i + 1], "w")
                i += 2
            elif args[i] == "2>>":
                redirections["stderr"] = (args[i + 1], "a")
                i += 2
            else:
                output_args.append(args[i])
                i += 1
        return output_args, redirections

    def _handle_redirection(self, output_str, redirections):
        try:
            if redirections["stdout"]:
                self._write_to_file(output_str, redirections["stdout"][0], redirections["stdout"][1])
            else:
                print(output_str)
            if redirections["stderr"]:
                self._write_to_file("", redirections["stderr"][0], redirections["stderr"][1])
        except IOError as e:
            print(f"echo: {e}", file=sys.stderr)

    def _write_to_file(self, content, filename, mode):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode) as f:
            f.write(content + "\n" if mode in ['w','a'] and content else content)


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
        executable = self.find_executable(command)
        if not executable:
            print(f"{command}: command not found", file=sys.stderr)
            return
        command_with_args, redirections = self._parse_redirection([command] + args)
        self._run_process(command_with_args, redirections)

    def _run_process(self, command_with_args, redirections):
        try:
            stdout_target = self._get_redirection_target(redirections.get("stdout"))
            stderr_target = self._get_redirection_target(redirections.get("stderr"))
            stdout_pipe = subprocess.PIPE if not stdout_target else None
            stderr_pipe = subprocess.PIPE if not stderr_target else None
            process = subprocess.Popen(command_with_args, stdout=stdout_target or stdout_pipe, stderr=stderr_target or stderr_pipe, text=True)
            stdout_content, stderr_content = process.communicate()
            if stdout_pipe:
                print(stdout_content or '', end='')
            if stderr_pipe:
                print(stderr_content or '', file=sys.stderr, end='')
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()
            if process.returncode != 0 and not redirections.get("stdout") and not redirections.get("stderr"):
                print(f"{command_with_args[0]}: command failed with exit code {process.returncode}", file=sys.stderr)
        except Exception as e:
            print(f"{command_with_args[0]}: {e}", file=sys.stderr)
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

    def _get_redirection_target(self, redirection):
        if redirection:
            os.makedirs(os.path.dirname(redirection[0]), exist_ok=True)
            return open(redirection[0], redirection[1])
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
