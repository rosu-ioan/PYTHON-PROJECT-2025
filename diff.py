from dataclasses import dataclass
import math
from itertools import pairwise 

@dataclass
class Box:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def size(self):
        return self.width + self.height

    @property
    def delta(self):
        return self.width - self.height

class MyersLinear:
    def __init__(self, A, B):
        self.A = A
        self.B = B
        self.diff_ops = []

    def diff(self):
        self.walk_snakes()
        return self.diff_ops

    def ses(self):
        ops = self.diff()
        return sum(1 for op, _, _ in ops if op != "eql")

    def find_path(self, left, top, right, bottom):
        box = Box(left, top, right, bottom)
        snake = self.midpoint(box)

        if snake is None:
            return None

        start, finish = snake

        head = self.find_path(box.left, box.top, start[0], start[1])
        tail = self.find_path(finish[0], finish[1], box.right, box.bottom)

        head = [start] if head is None else head
        tail = [finish] if tail is None else tail

        return head + tail

    def midpoint(self, box):
        if box.size == 0:
            return None

        maximum = math.ceil(box.size / 2)

        vf    = [None] * (2 * maximum + 1)
        vf[1] = box.left
        vb    = [None] * (2 * maximum + 1)
        vb[1] = box.bottom

        for d in range(0, maximum + 1):
            fwd = self.forward(box, vf, vb, d)
            bwd = self.backward(box, vf, vb, d)

            if fwd is not None:
                return fwd
            if bwd is not None:
                return bwd

    def forward(self, box, vf, vb, d):
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

    def backward(self, box, vf, vb, d):
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

    def walk_snakes(self):
        path = self.find_path(0, 0, len(self.A), len(self.B))
        if path is None:
            return None

        for [x1, y1], [x2, y2] in pairwise(path):
            x1, y1 = self.walk_diagonal(x1, y1, x2, y2)

            diff_x = x2 - x1
            diff_y = y2 - y1
            
            if diff_x < diff_y:
                self.add_op(x1, y1, x1, y1+1)
                y1 += 1
            elif diff_x > diff_y:
                self.add_op(x1, y1, x1 + 1, y1)
                x1 += 1

            self.walk_diagonal(x1, y1, x2, y2)

    def walk_diagonal(self, x1, y1, x2, y2):
        while x1 < x2 and y1 < y2 and self.A[x1] == self.B[y1]:
            self.add_op(x1, y1, x1 + 1, y1 + 1)
            x1, y1 = x1 + 1, y1 + 1
        return [x1, y1]

    def add_op(self, x1, y1, x2, y2):
        if x1 == x2:
            self.diff_ops += [("ins", None, self.B[y1])]
        elif y1 == y2:
            self.diff_ops += [("del", self.A[x1], None)]
        else:
            self.diff_ops += [("eql", self.A[x1], self.B[y1])]
            
myers = MyersLinear("abcabba", "cbabac")
print(myers.diff())
    
