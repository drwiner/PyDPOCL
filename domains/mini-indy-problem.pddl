
(define (problem bridge-example)
  (:domain mini-indy-domain)
  (:objects Indy Sapito - character
            cliff1 cliff2 bridge - location)
  (:init (at Indy cliff1)
		 (at Sapito cliff1)
		 (adj cliff1 bridge)
		 (adj bridge cliff2)
		 (alive Indy)
		 (alive Sapito)
		 (high-up bridge)
        )
  (:goal (at Indy cliff2)))