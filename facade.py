"""
Facade pattern exposing all the functionality from diff.py and binary_io.py to main.py.
"""

import argparse
import os
import sys
from binary_io import generate_diff_file, apply_patch_file, compute_file_hash, MAGIC_HEADER, HASH_SIZE, files_are_identical, verify_diff_file
from utils import print_error, print_table_color

def check_file_hash(file_path:str, diff_path: str) -> bool:
    """ Helper function to verify that the has of the old file and .diff file match. """
    file_hash = compute_file_hash(file_path)
    with open(diff_path, "rb") as f_diff:
        f_diff.seek(len(MAGIC_HEADER))
        diff_hash = f_diff.read(HASH_SIZE)

        if file_hash != diff_hash:
            return False
        else:
            return True

def validate_filename(filename: str) -> bool:
    """
    Validate that a filename does not contain illegal characters.
    
    Args:
        filename -- The filename to check

    Returns:
        True if the filename is valid and False otherwise
    """
        
    if os.path.basename(filename) != filename:
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
    if not os.path.exists(file_path):
        print_error(f"{file_path} does not exist.")
        return False

    if not os.path.isfile(file_path):
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

    if args.name is not None:
        if not validate_filename(name):
            sys.exit(1)

        if os.path.exists(name):
            print_error(f"The file '{name}' already exists.")
            sys.exit(1)
        
    if not verify_diff_file(args.diff):
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

        if os.path.exists(name + ".diff"):
            print_error(f"The file '{name + '.diff'}' already exists.")
            sys.exit(1)
    
    print_table_color({
        "Latest file":args.latest_file,
         **{f"Old version({i})":file_name for (i, file_name) in enumerate(args.old_files)},
         **{f"Diff of ver.({i})":name + ".diff" for (i, name) in enumerate(names)}
    })


def execute_create_command(args: argparse.Namespace):
    """
    Execute the create command, creating a .diff file for every old file specified.

    Args:
        args -- The arguments provided with the "create" command(old files, latest file)
    """

    if args.name is not None:
        names = args.name[:len(args.old_files)]
    else:
        names = None
        
    for idx, old_file in enumerate(args.old_files):
        if files_are_identical(old_file, args.latest_file):
            print(f"Skipping {old_file}: Identical to latest version.")
            continue
        
        if names is not None and idx < len(names):
            output_path = names[idx] + ".diff"
        else:
            old_file_name = os.path.splitext(old_file)[0]
            latest_file_name = os.path.splitext(args.latest_file)[0]
            output_path = old_file_name + "-" + latest_file_name + ".diff"

        chunk_size = args.chunk_size if args.chunk_size != None else 1024 * 1024
        generate_diff_file(old_file, args.latest_file, output_path, chunk_size)

        
def execute_update_command(args: argparse.Namespace):
    """
    Execute the update command, creating a new file from an old file and a .diff file.

    Args:
        args -- The arguments provided with the "update" command(file path, diff file path)
    """

    if not verify_diff_file(args.diff):
        sys.exit(1)
    
    if not check_file_hash(args.file_path, args.diff):
        print_error(f"The hash value of the file '{args.file_path}' does not match the one of the diff '{args.diff}'")
        sys.exit(1)

    if args.name is None:
        basename = os.path.splitext(args.file_path)[0]
        extension = os.path.splitext(args.file_path)[1]
        output_path = basename + "(new)" + extension
    else:
        output_path = args.name
        
    apply_patch_file(args.file_path, args.diff, output_path)


