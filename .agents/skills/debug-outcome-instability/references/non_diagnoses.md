The following kinds of diagnoses are not satisfactory:
* Diagnosis: "The query is unstable because mutants explore different branches and diverge."
    - It is normal for mutants to explore different branches. What is not normal is for one of the branches to lead to unknown when the query itself is unsat. You need to figure out how unsat mutants refute the same portion of the search space while the unknown mutant fails/runs out of resources. This is why the branch isolation workflow is useful.
