import math
import myers
import random
import string
import tempfile
import os
from hypothesis import given, strategies as st
from dataclasses import dataclass
from rich import print
from diff import MyersLinear, Insert, Delete, Change, DiffOp, patch
from binary_io import generate_diff_file, apply_patch_file

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
    
    if a == b:
        assert d == 0
        
    assert d == MyersLinear(b,a).ses()
    assert d <= (n + m)
    assert d % 2 == (n + m) % 2

    
@given(st.text(), st.text())
def test_against_reference_library(a, b):
    diff = myers.diff(a, b)
    
    expected_d = sum(1 for tag, content in diff if tag != 'k')
    
    actual_d = MyersLinear(a, b).ses()
    
    assert actual_d == expected_d, f"Failed on a={repr(a)}, b={repr(b)}"

@given(st.binary(), st.binary())
def test_patch_reconstruction(a, b):
    ops = MyersLinear(a, b).diff()
    
    reconstructed = patch(a, ops)
    
    assert reconstructed == b, (
        f"Reconstruction failed!\n"
        f"Expected len: {len(b)}\n"
        f"Got len:      {len(reconstructed)}\n"
        f"Diff Ops:     {len(ops)}"
    )

@given(st.binary(), st.binary())
def test_full_file_io_cycle(a, b):
    with tempfile.TemporaryDirectory() as tmpdir:
        p_old = os.path.join(tmpdir, "old.bin")
        p_new = os.path.join(tmpdir, "new.bin")
        p_diff = os.path.join(tmpdir, "update.diff")
        p_restored = os.path.join(tmpdir, "restored.bin")

        with open(p_old, "wb") as f: f.write(a)
        with open(p_new, "wb") as f: f.write(b)

        generate_diff_file(p_old, p_new, p_diff, chunk_size=1024)

        apply_patch_file(p_old, p_diff, p_restored)

        with open(p_restored, "rb") as f:
            restored_data = f.read()
        
        assert restored_data == b, (
            f"File I/O Reconstruction failed!\n"
            f"Original size: {len(a)}\n"
            f"Target size:   {len(b)}\n"
            f"Result size:   {len(restored_data)}"
        )
    
if __name__ == "__main__":
    random_validation(100)
