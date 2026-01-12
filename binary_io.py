"""
binary_io.py

Handles the binary encoding and decoding of diff operations.
Implements the streaming generation of .diff files from large inputs.
"""

import struct
import hashlib
from typing import List, Generator, BinaryIO
from diff import Insert, Delete, Change, DiffOp, MyersLinear

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
