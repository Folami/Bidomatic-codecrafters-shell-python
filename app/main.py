import sys, os, subprocess
from dataclasses import dataclass

supported_commands = ["exit", "echo", "type", "pwd"]
path_str = os.environ.get("PATH")

@dataclass
class Arg:
    val: str
    type: str

@dataclass
class Command:
    val: str
    args: [Arg]

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        # Wait for user input
        command = input()
        command_and_params = parse_command_and_args(command)
        command_key = command_and_params.val
        paths = path_str.split(":") if path_str else []
        args = command_and_params.args
        handle_command(paths=paths, command=command_key, args=args)

def handle_command(paths: [str], command: str, args: [Arg]):
    if command == "exit":
        sys.exit(int(args[0].val))
    elif command == "echo":
        handle_echo_command(args)
    elif command == "cat":
        handle_cat_command(args)
    elif command == "pwd":
        sys.stdout.write(f"{os.getcwd()}\n")
    elif command == "cd":
        handle_cd_command(args)
    elif command == "type":
        handle_type_command(paths, args[0].val)
    else:
        custom_command = get_custom_command_if_exists(command=command)
        custom_args = list(map(lambda n: n.val, args))
        if custom_command is None:
            sys.stdout.write(f"{command}: not found\n")
        else:
            result = subprocess.run(
                [custom_command, *custom_args], capture_output=True, text=True
            )
            sys.stdout.write(result.stdout)
def handle_cat_command(args: [Arg]):
    what_to_echo = ""
    for arg in args:
        if arg.type == "file":
            f = open(arg.val, "r")
            what_to_echo += f.read()
        else:
            raise Exception(f"cat: {arg.val}: No such file or directory")
    sys.stdout.write(f"{what_to_echo.strip()}\n")
def handle_echo_command(args: [Arg]):
    what_to_echo = ""
    for arg in args:
        what_to_echo += " "
        what_to_echo += arg.val
    sys.stdout.write(f"{what_to_echo.strip()}\n")

def parse_command_and_args(raw_args: str):
    args_striped = strip_arg(raw_args)
    args = []
    for arg in args_striped[1:]:
        if os.path.isfile(arg):
            args.append(Arg(arg, "file"))
        elif os.path.isdir(arg):
            args.append(Arg(arg, "dir"))
        else:
            args.append(Arg(arg, "simple"))
    return Command(args_striped[0], args)

def strip_arg(full_arg: str):
    in_single_quote = False
    in_double_quote = False
    last_backslash = False
    args = []
    arg = ""
    for ch in full_arg:
        if last_backslash:
            arg += ch
            last_backslash = False
        elif ch == "\\" and in_single_quote:
            arg += ch
            last_backslash = False
        elif ch == "\\" and not in_single_quote and not in_double_quote:
            last_backslash = True
        elif ch == " " and not in_single_quote and not in_double_quote:
            if arg:
                args.append(arg)
                arg = ""
        elif ch == "'" and not in_double_quote:
            if in_single_quote:
                args.append(arg)
                arg = ""
                in_single_quote = False
            else:
                in_single_quote = True

        elif ch == '"' and not in_single_quote:
            if in_double_quote:
                args.append(arg)
                arg = ""
                in_double_quote = False
            else:
                in_double_quote = True
        else:
            arg += ch
    if arg:
        args.append(arg)
    if in_single_quote or in_double_quote:
        raise Exception("Invalid args passed")
    return args
def handle_cd_command(args: [Arg]):
    path = args[0].val
    if path == "~":
        os.chdir(f"{os.path.expanduser(path)}")
    elif args[0].type == "dir":
        os.chdir(f"{path}")
    else:
        sys.stdout.write(f"cd: {path}: No such file or directory\n")
def handle_type_command(paths: [str], target_command: str):
    command_path_key = None
    if len(paths) > 0:
        for path in paths:
            if os.path.isfile(f"{path}/{target_command}"):
                command_path_key = f"{path}/{target_command}"
    if target_command in supported_commands:
        sys.stdout.write(f"{target_command} is a shell builtin\n")
    elif command_path_key is not None:
        sys.stdout.write(f"{target_command} is {command_path_key}\n")
    else:
        sys.stdout.write(f"{target_command}: not found\n")
def get_custom_command_if_exists(command: str):
    for path in path_str.split(":"):
        if os.path.isfile(f"{path}/{command}"):
            return f"{path}/{command}"
    return None
if __name__ == "__main__":
    main()