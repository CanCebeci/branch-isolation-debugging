In order to use `(get-value)` properly to investigate the assignments of the failing branch, we need to disable model completion.

To observe the effects this has on get-value,
* run `partial_model_bool.smt2` without any flags, then with `model_completion=false`
* run `partial_model_func.smt2` with all combinations of `model_completion=<true/false>` and `smt.complete_partial_funcs=<true/false>`

`model_completion=false` only affects how `(get-value)` behaves.
`smt.complete_partial_funcs=false`, however, is generally not safe to use. I have not experimented with it but I am pretty sure it would break MBQI.