`branch-isolation-instrumentation` is a clean, retroactively reorganized branch that holds all the instrumentation.

cherry-pick the branch's four commits onto the commit you want. Run this inside z3:

```
git fetch origin
git checkout -b instr-at-<name> <target-commit>
git cherry-pick b8c098f00..origin/branch-isolation-instrumentation
````

`b`8c098f00 is the commit the branch is based on, so that range is exactly the four instrumentation commits. Instead of a hash you can write it as `origin/branch-isolation-instrumentation~4..origin/branch-isolation-instrumentation`