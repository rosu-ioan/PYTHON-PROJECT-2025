"""
Facade pattern exposing all the functionality from diff.py and binary_io.py to main.py.
"""

import argparse
import os
from binary_io import generate_diff_file

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
        if names is not None and idx < len(names):
            output_path = names[idx] + ".diff"
        else:
            old_file_name = os.path.splitext(old_file)[0]
            latest_file_name = os.path.splitext(args.latest_file)[0]
            output_path = old_file_name + "-" + latest_file_name + ".diff"

        chunk_size = args.chunk_size if args.chunk_size != None else 1024 * 1024
        generate_diff_file(old_file, args.latest_file, output_path, chunk_size)
