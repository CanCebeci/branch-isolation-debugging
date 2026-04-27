(declare-fun f (Int) Int)

(assert (= (f 5) 13))

(check-sat)
(get-value ((f 5)))
(get-value ((f 3)))