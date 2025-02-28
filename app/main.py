import os
import subprocess
import shlex
import sys
import readline


class Shell:
    def __init__(self):
        """
        Initializes the Shell object.
        Sets the shell's home directory, built-in commands, and sets up autocompletion.
        """
        self.shell_home = os.getcwd()  # Get the current working directory as the shell's home
        self.built_in_commands = ["echo", "exit", "type", "pwd", "cd"]  # List of built-in shell commands
        self.completion_options = []  # List to store autocompletion options
        self.completion_state = 0  # State variable to track multiple tab presses for autocompletion
        self.setup_autocomplete()  # Set up autocompletion functionality

    def setup_autocomplete(self):
        """
        Sets up autocompletion using the readline library.
        Binds the Tab key to the complete method.
        """
        readline.parse_and_bind("tab: complete")  # Bind the Tab key to the complete function
        readline.set_completer(self.complete)  # Set the completer function to the complete method

    def complete(self, text, state):
        """
        Autocompletion function for built-in commands and external executables.

        Args:
            text (str): The text to be completed.
            state (int): The state of the completion.

        Returns:
            str: The completed text or None.
        """
        if state == 0:  # Reset completion state on the first call
            self.completion_state += 1  # Increment the completion state
            self.completion_options = self._get_completion_options(text)  # Get completion options
            if len(self.completion_options) > 1:  # If there are multiple completion options
                common_prefix = os.path.commonprefix(self.completion_options)  # Get the longest common prefix
                if common_prefix != text:  # If the common prefix is different from the input text
                    return common_prefix + " "  # Return the common prefix with a space
            if len(self.completion_options) > 1 and self.completion_state == 1:  # If multiple options and first tab press
                sys.stdout.write("\a")  # Ring the bell
                sys.stdout.flush()
                return None
            elif len(self.completion_options) > 1 and self.completion_state == 2:  # If multiple options and second tab press
                print("\n" + "  ".join(self.completion_options))  # Print completion options with spaces
                sys.stdout.write("$ " + text)  # Reprint the prompt
                sys.stdout.flush()
                self.completion_state = 0  # Reset completion state
                return None
        if state < len(self.completion_options):  # If there are more completion options
            return self.completion_options[state] + " "  # Return the next completion option with a space
        self.completion_state = 0  # Reset completion state if no more options
        return None

    def _get_completion_options(self, text):
        """
        Gets the list of completion options for the given text.

        Args:
            text (str): The text to be completed.

        Returns:
            list: A list of completion options.
        """
        builtin_options = [cmd for cmd in self.built_in_commands if cmd.startswith(text)]  # Get built-in command options
        external_options = set()  # Set to store external executable options
        path_env = os.environ.get("PATH", "")  # Get the PATH environment variable
        if path_env:
            paths = path_env.split(os.pathsep)  # Split the PATH into directories
            for directory in paths:
                try:
                    for file in os.listdir(directory):  # Iterate through files in the directory
                        file_path = os.path.join(directory, file)  # Get the full file path
                        if (os.path.isfile(file_path) and os.access(file_path, os.X_OK) and file.startswith(text) and file not in self.built_in_commands):
                            external_options.add(file)  # Add executable file to options
                except (OSError, FileNotFoundError):
                    continue
        return builtin_options + sorted(external_options)  # Return combined list of options

    def input_prompt(self):
        """
        Displays the shell prompt and reads user input.

        Returns:
            str: The user input.
        """
        return input("$ ")  # Display prompt and read input

    def execute_command(self, command, args):
        """
        Executes the given command with arguments.

        Args:
            command (str): The command to execute.
            args (list): The arguments for the command.
        """
        if command in self.built_in_commands:  # If the command is a built-in command
            getattr(self, f"execute_{command}")(args)  # Call the corresponding execute method
        else:
            self.run_external_command(command, args)  # Run the command as an external command

    def execute_exit(self, args):
        """
        Exits the shell.
        """
        sys.exit(0)  # Exit the program

    def execute_echo(self, args):
        """
        Executes the echo command with proper redirection handling.

        Args:
            args (list): The arguments for the echo command.
        """
        output, error = self._parse_redirection(args)  # Parse redirection arguments
        output_str = " ".join(output)  # Join output arguments into a string
        self._handle_redirection(output_str, error)  # Handle redirection

    def _parse_redirection(self, args):
        """
        Parses redirection arguments.

        Args:
            args (list): The list of arguments.

        Returns:
            tuple: A tuple containing the output arguments and redirection information.
        """
        output_args = []  # List to store output arguments
        redirections = {"stdout": None, "stderr": None}  # Dictionary to store redirection information
        i = 0
        while i < len(args):
            if args[i] in [">", "1>"]:  # If stdout redirection
                redirections["stdout"] = (args[i + 1], "w")  # Store filename and mode
                i += 2
            elif args[i] in [">>", "1>>"]:  # If stdout append redirection
                redirections["stdout"] = (args[i + 1], "a")  # Store filename and mode
                i += 2
            elif args[i] == "2>":  # If stderr redirection
                redirections["stderr"] = (args[i + 1], "w")  # Store filename and mode
                i += 2
            elif args[i] == "2>>":  # If stderr append redirection
                redirections["stderr"] = (args[i + 1], "a")  # Store filename and mode
                i += 2
            else:
                output_args.append(args[i])  # Add argument to output arguments
                i += 1
        return output_args, redirections

    def _handle_redirection(self, output_str, redirections):
        """
        Handles redirection of output and error streams.

        Args:
            output_str (str): The output string.
            redirections (dict): The redirection information.
        """
        try:
            if redirections["stdout"]:  # If stdout redirection
                self._write_to_file(output_str, redirections["stdout"][0], redirections["stdout"][1])  # Write to file
            else:
                print(output_str)  # Print to stdout
            if redirections["stderr"]:  # If stderr redirection
                self._write_to_file("", redirections["stderr"][0], redirections["stderr"][1])  # Write to file
        except IOError as e:
            print(f"echo: {e}", file=sys.stderr)  # Print error message

    def _write_to_file(self, content, filename, mode):
        """
        Writes content to a file.

        Args:
            content (str): The content to write.
            filename (str): The filename.
            mode (str): The file mode.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)  # Create directories if needed
        with open(filename, mode) as f:
            f.write(content + "\n" if mode in ['w', 'a'] and content else content)  # Write content to file

    def execute_type(self, args):
        """
        Executes the type command.

        Args:
            args (list): The arguments for the type command.
        """
        if not args:
            print("type: missing operand")  # Print error message if no operand
            return
        command = args[0]  # Get the command to check
        if command in self.built_in_commands:
            print(f"{command} is a shell builtin")  # Print if it's a built-in command
        else:
            executable = self.find_executable(command)  # Find the executable
            if executable:
                print(f"{command} is {executable}")  # Print the executable path
            else:
                print(f"{command}: not found")  # Print if command not found

    def execute_pwd(self, args):
        """
        Executes the pwd command.
        """
        print(os.getcwd())  # Print the current working directory

    def execute_cd(self, args):
        """
        Executes the cd command.

        Args:
            args (list): The arguments for the cd command.
        """
        if not args:
            print("cd: missing operand")  # Print error message if no operand
            return
        new_dir = args[0]  # Get the new directory
        if new_dir.startswith("~"):
            new_dir = os.path.expanduser(new_dir)  # Expand home directory if needed
        try:
            os.chdir(new_dir)  # Change the current working directory
        except FileNotFoundError:
            print(f"cd: {new_dir}: No such file or directory", file=sys.stderr)  # Print error message

    def find_executable(self, command):
        """
        Finds the executable path for the given command.

        Args:
            command (str): The command to find.

        Returns:
            str: The executable path or None.
        """
        path_env = os.environ.get("PATH")  # Get the PATH environment variable
        if path_env:
            paths = path_env.split(os.pathsep)  # Split the PATH into directories
            for directory in paths:
                file_path = os.path.join(directory, command)  # Construct the file path
                if os.path.exists(file_path) and os.access(file_path, os.X_OK):  # Check if the file exists and is executable
                    return file_path
        file_path = os.path.join(os.getcwd(), command)  # Check in current directory
        if os.path.exists(file_path) and os.access(file_path, os.X_OK):
            return file_path
        return None

    def run_external_command(self, command, args):
        """
        Runs an external command with arguments and handles redirection.

        Args:
            command (str): The command to run.
            args (list): The arguments for the command.
        """
        executable = self.find_executable(command)  # Find the executable path
        if not executable:
            print(f"{command}: command not found", file=sys.stderr)  # Print error message if not found
            return
        command_with_args, redirections = self._parse_redirection([command] + args)  # Parse redirection
        self._run_process(command_with_args, redirections)  # Run the process

    def _run_process(self, command_with_args, redirections):
        """
        Runs a subprocess and handles redirection.

        Args:
            command_with_args (list): The command and arguments.
            redirections (dict): The redirection information.
        """
        try:
            stdout_target = self._get_redirection_target(redirections.get("stdout"))  # Get stdout target
            stderr_target = self._get_redirection_target(redirections.get("stderr"))  # Get stderr target
            stdout_pipe = subprocess.PIPE if not stdout_target else None  # Set stdout pipe if no redirection
            stderr_pipe = subprocess.PIPE if not stderr_target else None  # Set stderr pipe if no redirection
            process = subprocess.Popen(command_with_args, stdout=stdout_target or stdout_pipe, stderr=stderr_target or stderr_pipe, text=True)  # Start the process
            stdout_content, stderr_content = process.communicate()  # Get the output and error
            if stdout_pipe:
                print(stdout_content or '', end='')  # Print stdout content
            if stderr_pipe:
                print(stderr_content or '', file=sys.stderr, end='')  # Print stderr content
            if stdout_target:
                stdout_target.close()  # Close stdout target
            if stderr_target:
                stderr_target.close()  # Close stderr target
            if process.returncode != 0 and not redirections.get("stdout") and not redirections.get("stderr"):
                print(f"{command_with_args[0]}: command failed with exit code {process.returncode}", file=sys.stderr)  # Print error message if command failed
        except Exception as e:
            print(f"{command_with_args[0]}: {e}", file=sys.stderr)  # Print exception message
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

    def _get_redirection_target(self, redirection):
        """
        Gets the redirection target file object.

        Args:
            redirection (tuple): The redirection information.

        Returns:
            file: The file object or None.
        """
        if redirection:
            os.makedirs(os.path.dirname(redirection[0]), exist_ok=True)  # Create directories if needed
            return open(redirection[0], redirection[1])  # Open the file
        return None

    def run(self):
        """
        Runs the shell's main loop.
        """
        while True:
            command_line = self.input_prompt()  # Get user input
            if not command_line:
                continue
            try:
                tokens = shlex.split(command_line)  # Tokenize the command line
                if not tokens:
                    continue

                command = tokens[0]  # Get the command
                args = tokens[1:]  # Get the arguments
                self.execute_command(command, args)  # Execute the command

            except Exception as e:
                print(f"Error parsing command: {e}", file=sys.stderr)  # Print error message

if __name__ == "__main__":
    shell = Shell()  # Create a Shell object
    shell.run()  # Run the shell