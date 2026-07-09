(set-option :print-success false)
(set-info :smt-lib-version 2.6)
(set-option :auto_config false)
(set-option :type_check true)
(set-option :smt.case_split 3)
(set-option :smt.qi.eager_threshold 100)
(set-option :smt.delay_units true)
(set-option :smt.arith.solver 2)
(set-option :smt.mbqi false)
(set-option :model.compact false)
(set-option :model.v2 true)
(set-option :pp.bv_literals false)
(set-info :category "industrial")

(declare-fun f(Int) Int)

; This push is NOT optional if we want get-value to work.
(push 1)

(assert (forall ((x Int)) (! 
    (>= (f x) 0)
    :pattern ((f x))
)))

(assert (exists ((x Int)) (! 
    (= (f x) 0)
    :pattern ((f x))
    :qid hello
    :skolemid |10|
)))

(check-sat)

(declare-fun internal_sk!x!10!0 () Int)
(get-value (internal_sk!x!10!0))