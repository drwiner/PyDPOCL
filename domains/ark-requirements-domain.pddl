(define (domain ark-requirements-domain)
  (:requirements)
  (:types step literal arg n name-str - object
          actor - arg
          1 2 3 4 5 - n)

  (:predicates (name ?obj - object ?name - name-str)
               (bel-occurs ?step - step)
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
                  (name ?indy indy)
                  (nth-step-arg 1 ?excavate ?indy)))

    (:action indy-gets-ark
     :parameters (?indy - actor ?ark - arg ?excavate - step)
     :precondition ()
     :effect (bel-occurs ?excavate)
     :decomp (and
                  (name ?indy indy)
                  (name ?ark ark)
                  (effect ?excavate (has ?indy ?ark))))

    (:action indy-excavates-ark-tanis
     :parameters (?indy - actor ?ark - arg ?tanis - arg ?excavate - step)
     :precondition ()
     :effect (bel-occurs ?excavate)
     :decomp (and (name ?excavate excavate)
                  (name ?indy indy)
                  (name ?ark - ark)
                  (name ?tanis - tanis)
                  (occurs ?excavate ?indy ?ark ?tanis)))

    (:action link-excavate-steal
     :parameters (?excavate - step ?steal - step)
     :precondition ()
     :effect (bel-linked ?excavate ?steal)
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (linked ?excavate ?steal)))


    (:action steal-before-excavate
     :parameters (?excavate - step ?steal - step)
     :precondition ()
     :effect (bel-precedes ?steal ?excavate)
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (< ?steal ?excavate)))

    (:action impossible-sequence
     :parameters (?excavate - step ?steal - step)
     :precondition ()
     :effect (and (bel-linked ?excavate ?steal) (bel-precedes ?steal ?excavate))
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (linked ?excavate ?steal)
                  (< ?excavate ?steal)))
)