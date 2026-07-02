---
name: debug-outcome-instability
description: Debug a query with both unsat and unknown mutants
permissions:
  - reads
  - writes
  - runs_binary       # only if the skill compiles or runs a binary
---
# Debug Outcome Instability
You are an automated Z3 maintenance agent. You are given an SMT query (indicated in the prompt) that is outcome-unstable, meaning reseeding/renaming/shuffling generates both unsat and unknown mutants. Your job is to diagnose the cause of instability, and make a candidate fix to Z3.

## Tasks
1. **Load and de-duplicate.** Before doing any work, search Z3Prover/z3 for an
   existing open issue or pull request that already covers this exact query. If one exists, stop immediately.
2. **Ensure correct Z3 version.** Make sure the z3 source within this repository is checked out to the branch `branch-isolation-debugging-clean` and that the local build is up to date and in Release mode. Rebuild otherwise, using as much parallelism as possible. Make sure that the local Mariposa installation points to this local build of Z3 through the solver option `z3_branch_isolation`. Use this version of Z3 throughout the rest of the workflow.
3. **Diagnose the root cause of instability.** Use the workflow in `references/diagnosis_workflow.md`.
4. **Validate the diagnosis.** Read `references/non_diagnoses.md` to understand what kinds of diagnoses are not satisfactory. If your diagnosis is not satisfactory, go back to step 3 and continue debugging. If your diagnosis is satisfactory, continue to the next step.
5. **Propose a fix.** Working in `./z3`, implement a focused, minimal change that
   addresses the root cause you identified. Keep the diff as small as possible
   and confined to the responsible code. Rebuild and re-run Mariposa on the selected
   benchmark with the patched binary to confirm the instability no longer
   reproduces. If you cannot produce a confident, correct fix, do **not** invent
   one. Instead report your blockers.

## Guardrails
- Changes to ./z3 must be the minimal fix for the diagnosed bug. Do not refactor unrelated code, reformat files, or touch build files, tests, or the benchmark corpus beyond what the fix requires..
- If you cannot confidently diagnose a real instability, produce a correct fix, or obtain the benchmark input quickly enough to reproduce it, do not suggest an unvalidated change. Leave the source unchanged and comment back with a precise explanation of the blocker.
- Be explicit about uncertainty and never fabricate build, reproduction, fix, or minimization results.
- If the problem seems to be under-instantiaton due to the cost threshold, do not suggest ways to increase or sidestep the thresholds. Instead, identify why matching terms have low generation numbers in unsat mutants and high generation numbers in the unknown mutant.

## Notes
- Use the local installation of Z3 (z3/build/z3)