"""
Facade pattern exposing all the functionality from diff.py and binary_io.py to main.py.
"""

import argparse
import os
from binary_io import generate_diff_file, apply_patch_file, compute_file_hash, MAGIC_HEADER, HASH_SIZE
from main import print_error

def files_are_identical(file_path_a: str, file_path_b: str, chunk_size: int = 2 ** 16) -> bool:
    """
    Checks if two files are identical by reading them in chunks.

    Args:
        file_path_a -- path to the first file
        file_path_b -- path to the second file
        chunk_size -- size of the chunk that will be read at a time
    
    Returns:
        False immediately upon finding a mismatch
    """
    
    if os.path.getsize(file_path_a) != os.path.getsize(file_path_b):
        return False
        
    with open(file_path_a, "rb") as f_a, open(file_path_b, "rb") as f_b:
        while True:
            chunk_a = f_a.read(chunk_size)
            chunk_b = f_b.read(chunk_size)
            
            if not chunk_a: 
                return True
            
            if chunk_a != chunk_b:
                return False
                

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

    file_hash = compute_file_hash(args.file_path)
    with open(args.diff, "rb") as f_diff:
        f_diff.seek(len(MAGIC_HEADER))
        diff_hash = f_diff.read(HASH_SIZE)

        if file_hash != diff_hash:
            print_error(f"The hash value of the file '{args.file_path}' does not match the one of the diff '{args.diff}'")

    if args.name is None:
        basename = os.path.splitext(args.file_path)[0]
        extension = os.path.splitext(args.file_path)[1]
        output_path = basename + "(new)" + extension
    else:
        output_path = args.name
        
    apply_patch_file(args.file_path, args.diff, output_path)
