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
        """Autocompletion function for built-in commands and external executables with trailing space."""
        if state == 0:
            self.completion_state += 1
            # Built-in commands
            builtin_options = [cmd for cmd in self.sh_builtins if cmd.startswith(text)]
            
            # External executables from PATH
            external_options = set()
            path_env = os.environ.get("PATH", "")
            if path_env:
                paths = path_env.split(os.pathsep)
                for dir in paths:
                    try:
                        for file in os.listdir(dir):
                            file_path = os.path.join(dir, file)
                            if (os.path.isfile(file_path) and 
                                os.access(file_path, os.X_OK) and 
                                file.startswith(text) and 
                                file not in self.sh_builtins):
                                external_options.add(file)
                    except (OSError, FileNotFoundError):
                        continue
            
            self.completion_options = builtin_options + sorted(external_options)

        if len(self.completion_options) > 1 and self.completion_state == 1:
            sys.stdout.write("\a")  # Ring the bell
            sys.stdout.flush()
            return None
        elif len(self.completion_options) > 1 and self.completion_state == 2:
            print("\n" + "  ".join(self.completion_options))
            sys.stdout.write("$ ")  # Reprint prompt
            sys.stdout.flush()
            self.completion_state = 0  # Reset state
            return None

        if state < len(self.completion_options):
            return self.completion_options[state] + " "
        
        self.completion_state = 0  # Reset state if no matches
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
        print(" ".join(args))

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
        file_path = os.path.join(os.getcwd(), command)
        if os.path.exists(file_path) and os.access(file_path, os.X_OK):
            return file_path
        return None
    
    def run_external_command(self, command, args):
        executable = self.find_executable(command)
        if not executable:
            print(f"{command}: command not found", file=sys.stderr)
            return
        try:
            process = subprocess.Popen([command] + args)
            process.wait()
        except Exception as e:
            print(f"{command}: {e}", file=sys.stderr)

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
