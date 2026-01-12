from os import path
from rich import print
import argparse
import sys
import re

import facade

def print_error(msg: str):
    """Print an error message with a colored "ERROR" prefix."""

    print("[red]ERROR[/red]: " + msg)

def print_table_color(table: dict[str, str]):
    """Print an aligned table with colored fields."""
    width = len(max(table.keys(), key=len))
    for name, value in table.items():
        print(f"[blue]{name:<{width}}[/blue]: {value}")

def validate_filename(filename: str) -> bool:
    """
    Validate that a filename does not contain illegal characters.
    
    Args:
        filename -- The filename to check

    Returns:
        True if the filename is valid and False otherwise
    """
        
    if path.basename(filename) != filename:
        print_error(f"Invalid filename '{filename}': Directory traversal (slashes) not allowed in name.")
        return False
    
    result = re.search(r'[<>:"/\\|?*]', filename)
    if result:
        print_error(f"Invalid filename '{filename}': Contains illegal character '{result.group(0)}'.")
        return False
    
    if filename.strip(" .") != filename:
        print_error(f"Invalid filename '{filename}': Cannot end with a dot or space.")
        return False

    return True
        
def validate_file(file_path: str, mode: str = "r") -> bool:
    """
    Checks whether a file exists, is a regular file and can be accessed.

    Args:
        file_path -- the path to the file as a string
        mode -- the mode in which the file is opened, default to "r"

    Returns:
        True if the filepath is valid and False otherwise
    """
    if not path.exists(file_path):
        print_error(f"{file_path} does not exist.")
        return False

    if not path.isfile(file_path):
        print_error(f"{file_path} is not a file.")
        return False
    
    try:
        with open(file_path, mode):
            pass
    except OSError as e:
        print_error(f"encountered when trying to open {file_path} --> {e}")
        return False

    return True

def validate_update_command_args(args: argparse.Namespace):
    """Validates the arguments for the "update" command.""" 
    if not validate_file(args.file_path, mode="r+") or not validate_file(args.diff):
        sys.exit(1)

    # TODO: actually check if the content of the file is correct, not just the extension
    if not args.diff.lower().strip().endswith(".diff"):
        print_error(f"{args.diff} is not a .diff file.")
        sys.exit(1)
            
    print_table_color({"File":args.file_path, "Diff":args.diff})

def validate_create_command_args(args: argparse.Namespace):
    """Validates the arguments for the "create" command."""
    for file_path in args.old_files:
        if not validate_file(file_path):
            sys.exit(1)

    if not validate_file(args.latest_file):
        sys.exit(1)

    names = args.name if args.name is not None else []
    for name in names:
        if not validate_filename(name):
            sys.exit(1)
    
    print_table_color({
        "Latest file":args.latest_file,
         **{f"Old version({i})":file_name for (i, file_name) in enumerate(args.old_files)},
         **{f"Diff of ver.({i})":name + ".diff" for (i, name) in enumerate(names)}
    })

def main():
    """Parse the command line arguments and delegate tasks to appropriate functions."""

    PROGRAM_NAME = "myDiff"
    PROGRAM_DESCRIPTION = """Generate the difference between two files.
                           Update the first file with the difference in order to produce the second file."""

    cmd_args_parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=PROGRAM_DESCRIPTION)
    subparsers = cmd_args_parser.add_subparsers(dest="command", required=True)

    create_command_parser = subparsers.add_parser("create")
    create_command_parser.add_argument("old_files", nargs="+",
                                       help="The path to one or more older versions of the file")
    create_command_parser.add_argument("latest_file", help="The path to the latest version of the file")
    create_command_parser.add_argument("--chunk_size",
                                       help="The size of the chunk that will be read from both files at a time",
                                       type=int)
    create_command_parser.add_argument("-n", "--name", nargs="*",
                                       help="The name(s) of the resulting .diff file(s). If there are more 'old_files' than names the first 'old_files' would be given the names and the rest would remain default")


    update_command_parser = subparsers.add_parser("update")
    update_command_parser.add_argument("file_path", help="The path to the file that would be modified")
    update_command_parser.add_argument("diff", help="The path to the .diff file that would be applied")

    cmd_args = cmd_args_parser.parse_args()

    match cmd_args.command:
        case "create":
            validate_create_command_args(cmd_args)
            facade.execute_create_command(cmd_args)
        case "update":
            validate_update_command_args(cmd_args)
    
        
if __name__ == "__main__":
    main()
