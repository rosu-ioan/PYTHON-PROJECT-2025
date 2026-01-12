"""
binary_io.py

Handles the binary encoding and decoding of diff operations.
Implements the streaming generation of .diff files from large inputs.
"""

import struct
import hashlib
import os
from typing import List, Generator, BinaryIO
from diff import Insert, Delete, Change, DiffOp, MyersLinear
from utils import print_error

MAGIC_HEADER = b"MYDIFF"
HASH_SIZE = 32
OP_INSERT = 0x01
OP_DELETE = 0x02
OP_CHANGE = 0x03

def compute_file_hash(file_path: str) -> bytes:
    """ Computes SHA-256 hash of a file. """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        chunk = f.read(2 ** 16)
        while chunk:
            sha256.update(chunk)
            chunk = f.read(2 ** 16)
    return sha256.digest()

def encode_ops(operations: List[DiffOp]) -> bytes:
    """
    Serialize a list of DiffOps into a binary byte string.
    
    Format per Op:
    [OpCode (1B)] [Position (8B)] [Length (8B)] [Payload (Length B)]

    Args:
        operations -- a list of DiffOp(Insert/Delete/Change)

    Returns:
        The binary representation of the operations
    """
    
    binary_buffer = bytearray()
    
    for op in operations:
        if isinstance(op, Insert):
            code = OP_INSERT
            payload = op.payload
            length = len(payload)
        elif isinstance(op, Delete):
            code = OP_DELETE
            payload = b""
            length = op.length
        elif isinstance(op, Change):
            code = OP_CHANGE
            payload = op.payload
            length = len(payload)
            
        # Pack Metadata: ! = Big Endian, B = uchar, Q = ulonglong
        # Structure: Opcode (1) + Position (8) + Length (8) = 17 bytes fixed header
        header = struct.pack("!BQQ", code, op.position, length)
        
        binary_buffer.extend(header)
        if payload:
            binary_buffer.extend(payload)
            
    return bytes(binary_buffer)

def generate_diff_file(old_file_path: str, new_file_path: str, output_path: str, chunk_size: int = 1024 * 1024):
    """
    Reads two files in chunks, calculates diffs, and streams the binary output to a .diff file.

    Args:
        old_file_path -- The path to the original file that should be modified
        new_file_path -- The path to the target file that the old file would be modified into
        output_path -- The path for the resulting .diff file
        chunk_size -- Size of the chunk that would be read from each file at a time
    """

    old_file_hash = compute_file_hash(old_file_path)
    
    with open(old_file_path, "rb") as f_old, \
         open(new_file_path, "rb") as f_new, \
         open(output_path, "wb") as f_out:
        
        f_out.write(MAGIC_HEADER)
        f_out.write(old_file_hash)
        
        abs_offset = 0
        
        while True:
            chunk_a = f_old.read(chunk_size)
            chunk_b = f_new.read(chunk_size)
            
            if not chunk_a and not chunk_b:
                break
                            
            ops = MyersLinear(chunk_a, chunk_b).diff()
            for op in ops:
                op.position += abs_offset
                
            binary_data = encode_ops(ops)
            f_out.write(binary_data)
            
            abs_offset += len(chunk_a)


def load_ops_from_file(diff_file_path: str) -> Generator[DiffOp, None, None]:
    """
    Load the DiffOp operations from a .diff file

    Args:
        diff_file_path -- path to the .diff file containing the binary representation of a list of DiffOps
    
    Returns:
        A generator that yields one DiffOp at a time from the .diff file
    """
    with open(diff_file_path, "rb") as f:
        f.seek(len(MAGIC_HEADER) + HASH_SIZE)
            
        while True:
            chunk = f.read(17)
            if not chunk: break
            
            code, pos, length = struct.unpack("!BQQ", chunk)
            
            if code == OP_INSERT:
                payload = f.read(length)
                yield Insert(pos, payload)
            elif code == OP_DELETE:
                yield Delete(pos, length)
            elif code == OP_CHANGE:
                payload = f.read(length)
                yield Change(pos, payload)
                
def apply_patch_file(old_file_path: str, diff_file_path: str, output_path: str):
    """
    Applies a binary diff file to an old file to generate a new file.

    Args:
        old_file_path -- Path to the original file
        diff_file_path -- Path to the .diff file
        output_path -- Path where the new file will be written
    """
    
    ops_generator = load_ops_from_file(diff_file_path)

    with open(old_file_path, "rb") as f_old, \
         open(output_path, "wb") as f_new:
        
        cursor = 0 
        
        for op in ops_generator:
            if op.position > cursor:
                bytes_to_copy = op.position - cursor
                _copy_chunk(f_old, f_new, bytes_to_copy)
                cursor += bytes_to_copy
            
            if isinstance(op, Insert):
                f_new.write(op.payload)
                
            elif isinstance(op, Delete):
                f_old.seek(op.length, 1) 
                cursor += op.length
                
            elif isinstance(op, Change):
                f_new.write(op.payload)
                f_old.seek(len(op.payload), 1)
                cursor += len(op.payload)
                
        f_old.seek(0, 2)
        total_size = f_old.tell()
        f_old.seek(cursor) 

        remaining_bytes = total_size - cursor

        if remaining_bytes > 0:
            _copy_chunk(f_old, f_new, remaining_bytes)


def _copy_chunk(src: BinaryIO, dst: BinaryIO, amount: int, chunk_size: int = 1024 * 1024):
    """Helper to copy 'amount' bytes from src to dst in chunks."""
    remaining = amount
    while remaining > 0:
        to_read = min(remaining, chunk_size)
        data = src.read(to_read)
        if not data: break
        dst.write(data)
        remaining -= len(data)

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
                
def verify_diff_file(diff_file_path: str) -> bool:
    """
    Verifies the integrity of a .diff file structure.
    
    Checks:
    1. Magic Header presence.
    2. Old file hash presence.
    2. Validity of all OpCodes.
    3. Payload lengths (ensures file is not truncated in the middle of an op).

    Args:
        diff_file_path -- path to the .diff file
        
    Returns:
        True if the file structure is valid, False otherwise
    """
    
    try:
        with open(diff_file_path, "rb") as f:
            header = f.read(len(MAGIC_HEADER))
            if header != MAGIC_HEADER:
                print_error(f"Invalid magic header. Expected {MAGIC_HEADER}, got {header}")
                return False

            f.seek(0, 2)
            file_size = f.tell()
            f.seek(len(MAGIC_HEADER) + HASH_SIZE, 0)
            
            op_count = 0
            while True:
                current_pos = f.tell()
                
                if current_pos == file_size:
                    break
                
                chunk = f.read(17)
                if len(chunk) < 17:
                    print_error(f"Truncated operation header at byte {current_pos}.")
                    return False
                
                code, pos, length = struct.unpack("!BQQ", chunk)
                
                if code not in [OP_INSERT, OP_DELETE, OP_CHANGE]:
                    print_error(f"Unknown opcode {code} at byte {current_pos} (Op #{op_count}).")
                    return False
                
                if code in [OP_INSERT, OP_CHANGE]:
                    if f.tell() + length > file_size:
                        print_error(f"Unexpected EOF. Op #{op_count} requires {length} bytes of payload, but file ends.")
                        return False
                    
                    f.seek(length, 1)
                op_count += 1
            return True
            
    except Exception as e:
        print_error(f"Error checking file integrity: {e}")
        return False
