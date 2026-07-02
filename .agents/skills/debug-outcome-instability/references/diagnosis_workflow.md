1. Call input `orig_query.smt2`
2. Confirm outcome instability and get unknown mutant.
  - Run `tools/get_unknown_mutant.py`
  - Make sure mariposa_res.csv is created and contains both unsat (result_code == 2) and unknown results (result_code == 4). If not, report and stop.
  - Make sure `unknown_mutant.smt2` is created and that Z3 returns unknown for it.
3. Isolate the failing branch of the unknown mutant.
  - Run `tools/get_assigndump.py unknown_mutant.smt2`
  - Make sure `assigndump.smt2` is created and that it does not branch. (`z3 assigndump.smt2 trace=true tactic.defualt_tactic=smt smt.reduce_assertions=false` should create a z3.log without any decisons)
  - If `assigndump.smt2` is unknown, stop following these steps and figure out what axioms/assertions are missing, based on the fact that the query has unsat mutants.
  - If it is unsat, continue with the next step.
4. Find the missing propagation in the unknown mutant.
  - Save the trace resulting from `z3 assigndump.smt2 trace=true tactic.defualt_tactic=smt smt.reduce_assertions=false` at `assigndump.log`
  - Run `tools/find_missing_step.py --unknown-mutant unknown_mutant.smt2 --assigndump-log assigndump.log`
  - Use the produced output to understand the missing propagation. Follow `references/debug_missing_propagation.md`