(define (domain ark-discourse-tests)
  (:requirements)
  (:types step literal arg n name-str - object
            Action - step
            Condition - literal
          0 1 2 3 4 5 - n
          actor place item - arg)

  (:predicates (name ?obj - object ?name - name-str)
               (bel-occurs ?step - step)
               (bel-state ?lit - literal)
               (bel-linked ?source - step ?sink - step)
               (bel-consents ?actor - actor ?step - step)
               (bel-involved ?arg - arg ?step - step)
               (bel-effect ?lit - literal ?step - step)
               (bel-precond ?lit - literal ?step - step)
               (bel-precedes ?source - step ?sink - step)
               (bel-occured-when ?step - step ?literal - literal)
               (occurs ?step - step)
               (effect ?step - step ?lit - literal)
               (precond ?step - step ?lit - literal)
               (consents ?step - step ?actor - actor)
               (includes ?lit - literal ?arg - arg)
               (nth-step-arg ?n - n ?step - step ?arg - arg)
               (nth-lit-arg ?n - n ?lit - literal ?arg - arg)
               (= ?obj - object ?obj2 - object)
               (linked ?source - step ?sink - step)
               (< ?source - step ?sink - step)
               (linked-by ?source - step ?sink - step ?dependency - literal))

    (:action indy-excavates
     :parameters (?indy - actor ?excavate - step)
     :precondition ()
     :effect (bel-occurs ?excavate)
     :decomp (and (name ?excavate excavate)
                  (name ?indy indiana)
                  (nth-step-arg 0 ?excavate ?indy)))

    (:action indy-gets-ark
     :parameters (?indy - actor ?ark - item ?excavate - step ?state - literal)
     :precondition (bel-occurs ?excavate)
     :effect (and (bel-state ?state) (bel-effect ?state ?excavate))
     :decomp (and
                  (name ?indy indiana)
                  (name ?ark ark)
                  (name ?state has)
                  (nth-lit-arg 0 ?state ?indy)
                  (nth-lit-arg 1 ?state ?ark)
                  (effect ?excavate ?state)))

    (:action link-excavate-steal
     :parameters (?excavate - step ?steal - step ?state - literal ?stolen - item)
     :precondition (and (bel-effect ?state ?excavate)
                (bel-occurs ?excavate) (bel-effect ?state ?excavate) (not (= ?excavate ?steal)))
     :effect (and (bel-linked ?excavate ?steal) (bel-occurs ?steal))
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (linked-by ?excavate ?steal ?state)))

)