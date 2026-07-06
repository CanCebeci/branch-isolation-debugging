import os
import subprocess

from config import *
from datatypes import Propagation

class Z3ErrorsException(Exception):
    def __init__(self, z3_errors):
        self.z3_errors = z3_errors

def copy_file(src, dst):
    os.system(f"cp {src} {dst}")
    
def append_line(file, line):
    os.system(f"echo \'{line}\' >> {file}")

def remove_last_line(file):
    with open(file, "rb+") as f:
        f.seek(0, 2)  # go to end of file
        pos = f.tell()

        # walk backwards to find last newline
        while pos > 0:
            pos -= 1
            f.seek(pos)
            if f.read(1) == b"\n":
                break

        f.truncate(pos)

# I don't want to run z3 through the Python bindings for now.
# The behavior doesn't seem to be identical to running through the command line and I don't want to debug this.
def run_z3(smt2, args=[]):
    result = subprocess.run(
        [Z3_BIN, smt2] + args,
        capture_output=True,
        text=True
    )
    if (result.stderr):
        print(result.stderr)
        raise Exception("Z3 failed")
    
    # For some reason missing declaration errors are printed to stdout
    if result.returncode != 0:
        raise Z3ErrorsException(result.stdout.splitlines()[:-1])
    
    return result.stdout.strip()

def intelligible_jst(p: Propagation):
    jst = p.justification
    if jst == "bin":
        return "binary clause"
    if jst == "justification -1:":
        if p.input:
            return "input assertion"
        return "theory propagation"
    else:
        return jst