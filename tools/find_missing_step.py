#!/usr/bin/env python3

import argparse 

from utils import *
from datatypes import *
from visualizer import visualize


TMP_GV_FILE = "get_value.smt2"

def parse_conflict(log):
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

    # We'll worry about justifications later
    jst=""

    return [Lit(int(id), expr) for id, expr in zip(lit_ids, exprs)], jst

def get_failing_branch_assignments(unknown_mutant, lits: list[Lit]):
    if len(lits) == 0:
        return []
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

def find_missing_lit(lits, vals):
    for l, v in zip(lits, vals):
        if v != Val.TRUE:
            return l, v
    return None, None

def parse_propagation(log, l: Lit):
    # TODO: clean this up
    assign_line = None
    with open(log) as f:
        found_assign = False
        for line in f:
            if found_assign:
                if l.sexpr == "":
                    # This must be redundant..
                    l.sexpr = line.strip()
                break
            if line.startswith(f"[assign] {l.id}"):
                assign_line = line
                found_assign = True
    assign_line = assign_line.strip().split()
    idx=3
    if l.id < 0:
        idx += 1 # account for "(not "
    jst = assign_line[idx]
    idx+=1
    if jst == "justification":
        jst += " " + assign_line[idx]
        idx+=1

    antecedents = [Lit(int(n), "") for n in assign_line[idx:]]

    is_input = len(antecedents) == 0 and jst == "-1:"

    return Propagation(l, antecedents, jst, None, is_input, None)

def find_sexpr(log, l: Lit):
    with open(log) as f:
        found_assign = False
        for line in f:
            if found_assign:
                return line.strip()
            if line.startswith(f"[assign] {l.id}"):
                found_assign = True

def find_clause(log, antecedents: list[Lit], consequent: Lit):
    # Target clause must have the following subset of lits
    subset = set([-l.id for l in antecedents])
    subset.add(consequent.id)

    candidates = []
    with open(log) as f:
        line_no=1
        for line in f:
            if line.startswith("[--- mk-clause ---]"):
                cls = set([int(l) for l in line[len("[--- mk-clause ---]"):].strip().split()])
                if subset <= cls:
                    candidates.append((line_no, cls))
            line_no+=1

    if len(candidates) == 0:
        raise Exception("Could not find clause")
    
    assert(len(candidates) == 1) # TODO: not sure how to choose between candidates yet.
    cls_line, cls = candidates[0]

    # Some kind of backwards search utility would significantly simplify and optimize this stuff..
    
    # Figure out the source quantifier
    instance_line = None
    instance_hash = None
    with open(log) as f:
        line_no=1
        for line in f:
            if line_no == cls_line:
                break
            if line.startswith("[instance]"):
                instance_line = line_no
                instance_hash = line.split()[1]
            if line.startswith("[end-of-instance]"):
                instance_line = None
                instance_hash = None
            line_no+=1
    if not instance_hash:
        raise Exception("Clause not created while instantiating quantifier")

    return Clause([Lit(id, "") for id in cls], instance_hash,[])



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unknown-mutant", required=True)
    parser.add_argument("--assigndump-log", required=True)

    args = parser.parse_args()

    # TODO: ensure uknown_mutant really is unknown
    # TODO: ensure assigndump_log does not branch
    props=[]
    clauses=[]
    quantifiers=[]
    lvl=1

    log = args.assigndump_log
    antecedents, conflict_jst = parse_conflict(log)

    false_lit = Lit(-0,"false")
    props.append(Propagation(false_lit, antecedents, conflict_jst, Val.FALSE, False, 0))
    
    vals = get_failing_branch_assignments(args.unknown_mutant, antecedents)
    missing_lit, missing_lit_val = find_missing_lit(antecedents, vals)
    while missing_lit != None:
        # Create truncated propagation nodes for all antecedents but l
        for l, v in zip(antecedents, vals):
            if l != missing_lit:
                props.append(Propagation(l, [], "", v, False, lvl))
        
        # create propagation node for l
        p = parse_propagation(log, missing_lit)
        p.consequent_val = missing_lit_val
        p.distance = lvl
        props.append(p)

        if p.justification == "clause" or p.justification == "bin":
            cls = find_clause(log, p.antecedents, p.consequent)
            cls.props.append(p)
            clauses.append(cls)
        lvl += 1

        antecedents = p.antecedents
        for i in range(len(antecedents)):
            if antecedents[i].sexpr == "":
                antecedents[i].sexpr = find_sexpr(log, antecedents[i])
        vals = get_failing_branch_assignments(args.unknown_mutant, antecedents)
        missing_lit, missing_lit_val = find_missing_lit(antecedents, vals)
        

    # Create truncated propagation nodes for all antecedents
    for l, v in zip(antecedents, vals):
        props.append(Propagation(l, [], "", v, False, lvl))

    visualize(props,clauses)

if __name__ == "__main__":
    main()