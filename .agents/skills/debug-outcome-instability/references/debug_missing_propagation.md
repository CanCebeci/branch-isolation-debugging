With what justification did the branch-isolated query deduce the missing propagation?
* 'clause'/'binary clause'
    * It is likely that the clause is missing from the unknown mutant. 
    * The output of `find_missing_step.py` should pinpoint which quantifier instance produced the missing clause, and which terms led to that instance. 
    * Check if those terms (or congruent ones) exist in the failing branch of the unknown mutant using the custom `(get-cgr-on-failure <term>)` command just before the `(check-sat)` in the unknown mutant
    * If the term does not exist:
        * examine Z3 logs for both queries to determine why the unknown mutant did not create the term the same way the assigndump query did.