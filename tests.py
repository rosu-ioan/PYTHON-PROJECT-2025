import math
import myers
import random
import string
from hypothesis import given, strategies as st
from dataclasses import dataclass
from rich import print
from diff import MyersLinear, Insert, Delete, Change, DiffOp, patch

def random_validation(iters=20):
    mismatch = False
    for i in range(iters):
        s1 = "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 20)))
        s2 = "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 20)))
        
        # Calculate distance using the library
        # myers.diff returns tags like ('keep', 'a'), ('insert', 'b'), ('remove', 'c')
        lib_diff = myers.diff(s1, s2)
        expected_d = sum(1 for tag, content in lib_diff if tag != 'k')
        #print(f"S1: {s1} | S2: {s2}")
        actual_d = MyersLinear(s1, s2).ses()

        
        if actual_d == expected_d:
            print(f"Test {i}: Match! (D={actual_d})")
        else:
            print(f"Test {i}: Mismatch! Expected {expected_d}, got {actual_d}")
            print(f"S1: {s1} | S2: {s2}")
            mismatch = True

    if mismatch == True:
        print("[red]There's been an error[/red]")
    else:
        print("[green]All tests passed[/green]")


@given(st.text(), st.text())
def test_myers_properties(a, b):
    n, m = len(a), len(b)
    d = MyersLinear(a, b).ses()
    
    # PROPERTY 1: Identity
    # The distance from a string to itself must be 0.
    if a == b:
        assert d == 0
        
    # PROPERTY 2: Symmetry
    # The distance from A to B must be the same as B to A.
    assert d == MyersLinear(b,a).ses()
    
    # PROPERTY 3: Upper Bound
    # The max possible distance is deleting everything and inserting everything.
    assert d <= (n + m)
    
    # PROPERTY 4: Parity (A very strong check for Myers)
    # The distance D and the sum of lengths (N+M) must have the same parity.
    # Mathematically: D ≡ (N + M) (mod 2)
    assert d % 2 == (n + m) % 2

    
@given(st.text(), st.text())
def test_against_reference_library(a, b):
    # 1. Get the "Absolute Truth" from the myers library
    # The lib returns a list of tuples: [('keep', 'a'), ('insert', 'b'), ('remove', 'c')]
    diff = myers.diff(a, b)
    
    # 2. Calculate the Edit Distance D from the reference
    # In Myers, D = Count of (Inserts + Removals)
    expected_d = sum(1 for tag, content in diff if tag != 'k')
    
    # 3. Get your result
    actual_d = MyersLinear(a, b).ses()
    
    # 4. Compare
    assert actual_d == expected_d, f"Failed on a={repr(a)}, b={repr(b)}"

@given(st.binary(), st.binary())
def test_patch_reconstruction(a, b):
    """
    Property: applying the diff of (A, B) to A must always yield B.
    """
    # 1. Compute Diff
    ops = MyersLinear(a, b).diff()
    
    # 2. Apply Patch
    reconstructed = patch(a, ops)
    
    # 3. Assert Equality
    # This gives us a rigorous check that your operations are valid
    assert reconstructed == b, (
        f"Reconstruction failed!\n"
        f"Expected len: {len(b)}\n"
        f"Got len:      {len(reconstructed)}\n"
        f"Diff Ops:     {len(ops)}"
    )
    
if __name__ == "__main__":
    random_validation(100)
