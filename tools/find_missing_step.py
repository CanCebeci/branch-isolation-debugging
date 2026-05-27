#!/usr/bin/env python3

import argparse 
import re

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

    header = conflict_lines[0].strip()
    match = re.fullmatch(r"--- justification lits for (-?\d+) ---", header)
    assert(match is not None)
    conflict_lit_id = int(match.group(1))


    lit_ids = conflict_lines[1].strip().split()
    exprs = [s.strip() for s in conflict_lines[2:-1]]
    assert(len(lit_ids) == len(exprs))

    # We'll worry about justifications later
    jst=""

    return [Lit(int(id), expr) for id, expr in zip(lit_ids, exprs)], jst, conflict_lit_id

# We should have a more robust 'contains quantifier' function
def is_quantifier(sexpr):
    return sexpr.startswith("(forall ") or sexpr.startswith("(exists ")

def get_failing_branch_assignments(unknown_mutant, lits: list[Lit]):
    if len(lits) == 0:
        return []
    gv = TMP_GV_FILE

    copy_file(unknown_mutant, gv)
    append_line(gv, "(get-value (")
    for lit in lits:
        if is_quantifier(lit.sexpr):
            append_line(gv, 'true') # Skip quantifiers
        else:
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
        if is_quantifier(lit.sexpr):
            out.append(Val.NON_EVAL)  # Did not evaluate quantifiers
            continue

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

def get_failing_branch_assignment(unknown_mutant, l: Lit):
    vals = get_failing_branch_assignments(unknown_mutant, [l])
    return vals[0] if vals else None

def find_missing_lit(lits, vals):
    qt_candidate = None
    for l, v in zip(lits, vals):
        if v != Val.TRUE:
            # Avoid quantifiers if we can. We can't evaluate them.
            if is_quantifier(l.sexpr):
                qt_candidate = (l, v)
                continue
            return l, v
    if qt_candidate:
        return qt_candidate
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

    ant_ids = [int(n) for n in assign_line[idx:] if int(n) != l.id]
    if jst == "clause":
        ant_ids = [-n for n in ant_ids]

    antecedents = [Lit(n, "") for n in ant_ids]
    for i in range(len(antecedents)):
        antecedents[i].sexpr = find_sexpr(log, antecedents[i])

    is_input = len(antecedents) == 0 and jst == "justification -1:"

    return Propagation(l, antecedents, jst, None, is_input, None)

def negate_sexpr(s):
    if s.startswith("(not "):
        return s[5:-1]
    else:
        return f"(not {s})"

def negate_lit(l: Lit):
    return Lit(-l.id, negate_sexpr(l.sexpr))

def find_sexpr(log, l: Lit):
    with open(log) as f:
        found_assign_pos = False
        found_assign_neg = False
        for line in f:
            if found_assign_pos:
                return line.strip()
            if found_assign_neg:
                return negate_sexpr(line.strip())
            
            if line.startswith(f"[assign] {l.id}"):
                found_assign_pos = True
            if line.startswith(f"[assign] {-l.id}"):
                found_assign_neg = True 

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
        print(subset)
        raise Exception("Could not find clause")

    # Prefer stricter match quality; tie-break on smaller clause, then first seen.
    candidates.sort(key=lambda c: (len(c[1]), c[0]))
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

    # TODO: see if we have already created the clause.
    return Clause([Lit(id, "") for id in cls], instance_hash,[])

def find_instance(log, cls: Clause):
    # For now, assuming instance_hash is unique in the log.
    qid=None
    match=[]
    with open(log) as f:
        read_match=False
        for line in f:
            if line.startswith(f"[new-match] {cls.instance_hash}"):
                qid = line.split()[4]
                read_match = True
                continue
            if read_match:
                if line.startswith(" ;"):
                    break # done
                
                # For now match[0] is the matching terms, and match[1:] contain substitution pairs.
                # This is broken, as substitution pairs aren't logged correctly right now.
                # Also, we would idealy not put the pairs in Term structs, which are supposed to hold sexprs.
                #! tmp: skip subsitutions 
                if len(match) > 0:
                    continue
                match.append(line.strip())

    # TODO: see if we have already created the quantifier, or any of the terms
    return Quantifier(qid, 0, [cls]), [Term(t, [cls]) for t in match]

def handle_conflict_lit(unknown_mutant, log,  conflict_lit_id):
    conflict_lit = Lit(conflict_lit_id, "")
    conflict_lit.sexpr = find_sexpr(log, conflict_lit)
    
    return conflict_lit, get_failing_branch_assignment(unknown_mutant, conflict_lit)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unknown-mutant", required=True)
    parser.add_argument("--assigndump-log", required=True)

    args = parser.parse_args()

    # TODO: ensure uknown_mutant really is unknown
    # TODO: ensure assigndump_log does not branch
    # For now, agents separately ensure these.
    props=[]; clauses=[]; quantifiers=[]; terms=[]
    lvl=1

    log = args.assigndump_log
    antecedents, conflict_jst, conflict_lit_id = parse_conflict(log)

    false_lit = Lit(-0,"false")

    if conflict_lit_id == 0:
        p = Propagation(false_lit, antecedents, conflict_jst, Val.FALSE, False, 0)
        props.append(p)
    else:
        conflict_lit, v = handle_conflict_lit(args.unknown_mutant, log, conflict_lit_id)
        
        props.append(Propagation(false_lit, [conflict_lit, negate_lit(conflict_lit)], "", Val.FALSE, False, 0))
        if v == Val.TRUE:
            conflict_lit = negate_lit(conflict_lit)
            p = parse_propagation(log, conflict_lit)
            antecedents = p.antecedents
            conflict_jst = p.justification
        p = Propagation(conflict_lit, antecedents, conflict_jst, Val.FALSE, False, 1)
        props.append(p)
        props.append(Propagation(negate_lit(conflict_lit), [], conflict_jst, Val.TRUE, False, 1))
        lvl += 1
    
    while True:
        vals = get_failing_branch_assignments(args.unknown_mutant, antecedents)
        new_missing_lit, new_missing_lit_val = find_missing_lit(antecedents, vals)
        if new_missing_lit is None:
            break
        missing_lit = new_missing_lit
        missing_lit_val = new_missing_lit_val

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
            qt, ts = find_instance(log, cls)
            quantifiers.append(qt)
            terms += ts
        lvl += 1

        antecedents = p.antecedents
        

    # Create truncated propagation nodes for all antecedents
    for l, v in zip(antecedents, vals):
        props.append(Propagation(l, [], "", v, False, lvl))

    visualize(props, clauses, quantifiers, terms)

    # Summary of what seems to be the problem
    print("")
    print("=== Problem Summary ===")
    print(f"Boolean term missing from the failing branch of unknown query: {missing_lit}")
    print(f"In the branch-isolated query, this term was deduced with justification '{intelligible_jst(p)}' from the following antecedents: {p.antecedents}")
    if p.justification == "clause" or p.justification == "bin":
        print(f"The clause that led to this deduction is: {find_clause(log, p.antecedents, p.consequent)}")
        qt, ts = find_instance(log, cls)
        print(f"The quantifier that instantiated this clause is: {qt}")
        print(f"The terms that instantiated this clause are: {ts}")


if __name__ == "__main__":
    main()