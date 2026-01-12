from os import path
import argparse
import sys
import re
from utils import print_error, print_table_color
import facade

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
    update_command_parser.add_argument("-n", "--name", help="The name of the resulting file")

    cmd_args = cmd_args_parser.parse_args()

    match cmd_args.command:
        case "create":
            facade.validate_create_command_args(cmd_args)
            facade.execute_create_command(cmd_args)
        case "update":
            facade.validate_update_command_args(cmd_args)
            facade.execute_update_command(cmd_args)
    
        
if __name__ == "__main__":
    main()
