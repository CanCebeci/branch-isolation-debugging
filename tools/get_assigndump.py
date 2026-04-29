#!/usr/bin/env python3

import sys
import subprocess

from config import *

OUT_FILE = "assigndump.smt2"

#pyright

class Z3ErrorsException(Exception):
    def __init__(self, z3_errors):
        self.z3_errors = z3_errors


# I don't want to run z3 thorugh the Python bindings for now.
# The behavior doesn't seem to be indentical to running through the command line and I don't want to debug this.
def run_z3(smt2, args=[]):
    result = subprocess.run(
        [Z3_BIN, smt2] + args,
        capture_output=True,
        text=True
    )
    if (result.stderr):
        print(result.stderr)
        raise Exception("Z3 failed")
    
    # For some reason missing declararion errors are printed to stdout
    if result.returncode != 0:
        raise Z3ErrorsException(result.stdout.splitlines()[:-1])
    
    return result.stdout.strip()

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

smt_input=sys.argv[1]

# TODO: make sure smt_input returns unknown

# Copy the configuration commands in the smt input
with open(smt_input) as f_in:
    with open(OUT_FILE, "w") as f_out:
        for line in f_in:
            if line.startswith("(set-option") or line.startswith("(set-info"):
                f_out.write(line)

with open(OUT_FILE, "a") as f:
    f.write(run_z3(smt_input, ["pp.single_line=true", "pp.min_alias_size=1000000", "pp.max_depth=100000", "smt.dump_assignments=true"]))
remove_last_line(OUT_FILE) # remove "unknown"
with open(OUT_FILE, "a") as f:
    f.write("\n(check-sat)")