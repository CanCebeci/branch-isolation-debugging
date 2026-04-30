#!/usr/bin/env python3

import argparse 
from dataclasses import dataclass
from enum import Enum

from utils import *


TMP_GV_FILE = "get_value.smt2"

@dataclass 
class Lit:
    boolvar_id: int     # ID in the assigndump trace
    sign: bool          # True if sign is negative
    sexpr: str          # pretty printed expression

class Val(Enum):
    TRUE = 1
    FALSE = 2
    NON_EVAL = 3        # The value of expressions that are not fully evaluable in the failing branch

def identify_conflict_lits(log):
    conflict_lines = []
    with open(log) as f:
        in_conflict = False
        done = False
        for line in f:
            if line.strip().startswith("--- conflict"):
                assert(not done) # sanity check: we assume there is a single conflict in the log
                in_conflict = True
                continue
            if line.strip().startswith("--- end of conflict"):
                in_conflict = False
                done = True
                continue
            if in_conflict:
                conflict_lines.append(line)

    # Make sure we have a justification for false:
    assert(conflict_lines[0].strip() == "--- justification lits for -0 ---")

    lit_ids = conflict_lines[1].strip().split()
    exprs = [s.strip() for s in conflict_lines[2:-1]]
    assert(len(lit_ids) == len(exprs))
    return [Lit(abs(int(id)), int(id) < 0, expr) for id, expr in zip(lit_ids, exprs)]

def get_failing_branch_assignments(unknown_mutant, lits: list[Lit]):
    gv = TMP_GV_FILE

    copy_file(unknown_mutant, gv)
    append_line(gv, "(get-value (")
    for lit in lits:
        append_line(gv, lit.sexpr)
    append_line(gv, "))")

    res = run_z3(gv)
    
    # -- Parse z3 output --
    assert(res.startswith("unknown\n"))
    res = res[len("unknown\n"):]
    assert(res[0] == "(" and res[-1] == ")")
    res = [l.strip() for l in res[1:-1].strip().splitlines()]
    assert(len(res) == len(lits))
    out=[]
    for lit, line in zip(lits, res):
        assert(line[0] == "(" and line[-1] == ")")
        l = len(lit.sexpr)
        assert(line[1:1+l] == lit.sexpr)
        assert(line[1+l] == " ")
        v = line[1+l+1:-1]
        if v == "true":
            out.append(Val.TRUE)
        elif v == "false":
            out.append(Val.FALSE)
        else:
            out.append(Val.NON_EVAL)

    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unknown-mutant", required=True)
    parser.add_argument("--assigndump-log", required=True)

    args = parser.parse_args()

    # TODO: ensure uknown_mutant really is unknown
    # TODO: ensure assigndump_log does not branch

    log = args.assigndump_log
    conflict_lits = identify_conflict_lits(log)
    
    print(get_failing_branch_assignments(args.unknown_mutant, conflict_lits))

if __name__ == "__main__":
    main()