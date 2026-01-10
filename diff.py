"""
diff.py

An implementation of the Myers diff algorithm with the linear space refinement.
This module provides a main class "MyersLinear" that should be given two sequences when instantiated.
Then either call "diff" for a list of Insert, Delete or Change operations or "ses" for the length of
the shortest edit script.
"""

from dataclasses import dataclass
from itertools import pairwise
import math
from typing import Optional

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
        return len(self.payload)

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

        Returns:
            A list of DiffOp representind the edits
        """
        self.diff_ops = []
        self._find_path(0, 0, len(self.A), len(self.B))
        return self.diff_ops

    def ses(self) -> int:
        """
        Calculate the length of the shortest edit script(SES).

        Returns:
           The total number of operations at the granularity of byte
        """
        
        ops = self.diff()
        return sum(op.es_len for op in ops)
                
    def _find_path(self, left: int, top: int, right: int, bottom: int) -> None:
        box = Box(left, top, right, bottom)
        snake = self._midpoint(box)

        if snake is None:
            return None
        
        if box.width == 0:
            if box.height > 0:
                payload = self.B[box.top : box.bottom]
                self.diff_ops.append(Insert(box.left, payload))
            return

        if box.height == 0:
            if box.width > 0:
                length = box.right - box.left
                self.diff_ops.append(Delete(box.left, length))
            return
        
        start, finish = snake

        dx = finish[0] - start[0]
        dy = finish[1] - start[1]

        if dy > dx:
            self.diff_ops.append(Insert(start[0], self.B[start[1]]))
        elif dx > dy:
            self.diff_ops.append(Delete(start[0], 1))
        
        self._find_path(box.left, box.top, start[0], start[1])
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
                return fwd
            if bwd is not None:
                return bwd

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


if __name__ == "__main__":            
    myers = MyersLinear("abcabba", "cbabac")
    print(myers.diff())

