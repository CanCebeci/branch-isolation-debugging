#!/usr/bin/env python3

import sys
import subprocess

from config import *
from utils import *

OUT_FILE = "assigndump.smt2"

#pyright

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