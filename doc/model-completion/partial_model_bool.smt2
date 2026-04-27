(set-option :auto_config false)

(declare-fun A (Int) Bool)
(declare-fun B (Int) Bool)

(assert (or (B 0) (A 0)))

(check-sat)
(get-value ((A 0)))
(get-value ((B 0)))
