"""
diff.py

An implementation of the Myers diff algorithm with the linear space refinement.
This module provides a main class "MyersLinear" that should be given two sequences when instantiated.
Then either call "diff" for a list of Insert, Delete or Change operations or "ses" for the length of
the shortest edit script.
"""

from dataclasses import dataclass
from typing import Optional
import math
import random
import string

@dataclass
class Insert:
    """Represent insert operation""" 
    position: int
    payload: bytes
    
    @property
    def es_len(self) -> int:
        """Return the length of the edit script for this operation"""
        return len(self.payload)

@dataclass
class Delete:
    """Represent delete operation"""
    position: int
    length: int
    @property
    def es_len(self) -> int:
        """Return the length of the edit script for this operation"""
        return self.length

@dataclass
class Change:
    """Represent change operation(a delete followed immediately by an insert"""
    position: int
    payload: bytes
    @property
    def es_len(self) -> int:
        """Return the length of the edit script for this operation"""
        return 2*len(self.payload)

DiffOp = Insert | Delete | Change
    
@dataclass
class Box:
    """Represent a segment of the edit graph"""
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def size(self) -> int:
        return self.width + self.height

    @property
    def delta(self) -> int:
        return self.width - self.height

class MyersLinear:
    """A linear-space implementation of the Myers diff algorithm."""

    def __init__(self, A: bytes, B: bytes):
        """
        Initialize the diff class.

        Args:
            A -- the original sequence of bytes
            B -- the modified sequence of bytes
        """
        
        self.A = A
        self.B = B
        self.diff_ops: list[DiffOp]

    def diff(self) -> list[DiffOp]:
        """
        Compute the difference between sequence A and B.

        Apply myers diff algorithm in O((N+M)D) time and O(N+M) space in order to compute the
        shortest edit script with delete/insert operations. Then merge adjacent delete + insert operations
        into a change operation. 
        
        Returns:
            A list of DiffOp(Insert/Delete/Change) representing the edits
        """
        self.diff_ops = []
        self._find_path(0, 0, len(self.A), len(self.B))
        self._merge()
        self._consolidate()
        return self.diff_ops

    def ses(self) -> int:
        """
        Calculate the length of the shortest edit script(SES).

        The length of the SES is measured as if the edit script contains only delete or insert operations
        in order to be compatible with other myers implementations for testing purposes. 

        Returns:
           The total number of operations at the granularity of byte
        """
        
        ops = self.diff()
        return sum(op.es_len for op in ops)

    def _merge(self):
        if len(self.diff_ops) == 0:
            return
        
        merged_ops = []
        curr = self.diff_ops[0]
        
        for next_op in self.diff_ops[1:]:
            if isinstance(curr, Insert) and isinstance(next_op, Insert):
                if curr.position == next_op.position:
                    curr.payload += next_op.payload
                    continue
            
            if isinstance(curr, Delete) and isinstance(next_op, Delete):
                if next_op.position == curr.position + curr.length:
                    curr.length += next_op.length
                    continue

            merged_ops.append(curr)
            curr = next_op
        merged_ops.append(curr)
        self.diff_ops = merged_ops
            
    def _consolidate(self):
        merged_ops = self.diff_ops
        final_ops = []
        i = 0
        while i < len(merged_ops):
            op = merged_ops[i]
            if i + 1 < len(merged_ops):
                next_op = merged_ops[i+1]
                
                if isinstance(op, Delete) and isinstance(next_op, Insert):
                    if op.position == next_op.position:
                        del_len = op.length
                        ins_len = len(next_op.payload)
                        common = min(del_len, ins_len)
                        
                        change_payload = next_op.payload[:common]
                        final_ops.append(Change(op.position, change_payload))
                        
                        if del_len > common:
                            rem_len = del_len - common
                            rem_pos = op.position + common
                            final_ops.append(Delete(rem_pos, rem_len))
                        elif ins_len > common:
                            rem_payload = next_op.payload[common:]
                            rem_pos = op.position + common
                            final_ops.append(Insert(rem_pos, rem_payload))
                            
                        i += 2
                        continue
            
            final_ops.append(op)
            i += 1

        self.diff_ops = final_ops
    
    def _find_path(self, left: int, top: int, right: int, bottom: int) -> None:
        box = Box(left, top, right, bottom)
        snake = self._midpoint(box)

        if snake is None:
            return None
        
        (start, finish), is_forward = snake
        
        if box.width == 0:
            if box.height > 0:
                payload = self.B[box.top:box.bottom]
                self.diff_ops.append(Insert(box.left, payload))
            return

        if box.height == 0:
            if box.width > 0:
                length = box.right - box.left
                self.diff_ops.append(Delete(box.left, length))
            return

        self._find_path(box.left, box.top, start[0], start[1])
        
        dx = finish[0] - start[0]
        dy = finish[1] - start[1]

        if dy > dx:
            if is_forward:
                self.diff_ops.append(Insert(start[0], self.B[start[1]:start[1]+1]))
            else:
                self.diff_ops.append(Insert(finish[0], self.B[finish[1] - 1:finish[1]]))
        elif dx > dy:
            if is_forward:
                self.diff_ops.append(Delete(start[0], 1))
            else:
                self.diff_ops.append(Delete(finish[0]-1, 1))
        
        self._find_path(finish[0], finish[1], box.right, box.bottom)

    def _midpoint(self, box: Box):
        if box.size == 0:
            return None

        maximum = math.ceil(box.size / 2)

        vf    = [None] * (2 * maximum + 1)
        vf[1] = box.left
        vb    = [None] * (2 * maximum + 1)
        vb[1] = box.bottom

        for d in range(0, maximum + 1):
            fwd = self._forward(box, vf, vb, d)
            bwd = self._backward(box, vf, vb, d)

            if fwd is not None:
                return (fwd, True)
            if bwd is not None:
                return (bwd, False)

    def _forward(self, box: Box, vf: list[int], vb: list[int], d: int):
        for k in range(-d, d+1, 2):
            c = k - box.delta

            if k == -d or (k != d and vf[k-1] < vf[k + 1]):
                px = x = vf[k + 1]
            else:
                px = vf[k - 1]
                x = px + 1

            y = box.top + (x - box.left) - k
            py = y if (d == 0 or x != px) else y - 1

            while x < box.right and y < box.bottom and self.A[x] == self.B[y]:
                x, y = x + 1, y + 1

            vf[k] = x

            if box.delta % 2 == 1 and c in range(-(d-1), d) and y >= vb[c]:
                return ([px, py], [x, y])

        return None
    
    def _backward(self, box: Box, vf: list[int], vb: list[int], d: int):
        for c in range(-d, d+1, 2):
            k = c + box.delta

            if c == -d or (c != d and vb[c-1] > vb[c+1]):
                py = y = vb[c+1]
            else:
                py = vb[c-1]
                y = py - 1

            x = box.left + (y - box.top) + k
            px = x if (d == 0 or y != py) else x + 1

            while x > box.left and y > box.top and self.A[x-1] == self.B[y-1]:
                x, y = x - 1, y - 1

            vb[c] = y

            if box.delta % 2 == 0 and k in range(-d, d+1) and x <= vf[k]:
                return ([x,y], [px, py])
            
        return None

def patch(original: bytes, operations: list[DiffOp]) -> bytes:
    """
    Reconstructs the target file from the original and the diff operations.
    
    Args:
        original -- The original byte sequence
        operations -- A sorted list of Insert, Delete, Change operations
    
    Returns:
        The patched byte sequence
    """
    
    result = bytearray()
    cursor = 0
    
    for i, op in enumerate(operations):
        if op.position < cursor:
             raise ValueError(f"Op #{i} at {op.position} overlaps with cursor at {cursor}. "
                              "Operations must be sorted and non-overlapping.")

        if cursor < op.position:
            result.extend(original[cursor:op.position])
            cursor = op.position
            
        if isinstance(op, Insert):
            result.extend(op.payload)
            
        elif isinstance(op, Delete):
            cursor += op.length
            
        elif isinstance(op, Change):
            result.extend(op.payload)
            cursor += len(op.payload)

    if cursor < len(original):
        result.extend(original[cursor:])
        
    return bytes(result)
    

if __name__ == "__main__":            
    myers = MyersLinear("abcabba", "cbabac")
    print(myers.diff())

    # myers = MyersLinear("jbjqzkwcmbhawqmdg", "cnbtjoncoopbargkq")
    # print(myers.diff())

    # iters = 20
    # for i in range(iters):
    #     s1 = "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 20)))
    #     s2 = "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 20)))

    #     print(MyersLinear(s1,s2).diff())

