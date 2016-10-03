(define (domain ark-requirements-domain)
  (:requirements)
  (:types step literal arg n name-str - object
          0 1 2 3 4 5 - n
          actor place item - arg)

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
                  (name ?indy indiana)
                  (nth-step-arg 0 ?excavate ?indy)))

    (:action indy-gets-ark
     :parameters (?indy - actor ?ark - item ?excavate - step)
     :precondition ()
     :effect (bel-occurs ?excavate)
     :decomp (and
                  (name ?indy indiana)
                  (name ?ark ark)
                  (effect ?excavate (has ?indy ?ark))))

    (:action indy-excavates-ark-tanis
     :parameters (?indy - actor ?ark - item ?tanis - place ?excavate - step)
     :precondition ()
     :effect (bel-occurs ?excavate)
     :decomp (and (name ?excavate excavate)
                  (name ?indy indiana)
                  (name ?ark ark)
                  (name ?tanis tanis)
                  (occurs (?excavate ?indy ?ark ?tanis))))

    (:action link-excavate-steal
     :parameters (?excavate - step ?steal - step ?stolen - item)
     :precondition (not (= ?excavate ?steal))
     :effect (bel-linked ?excavate ?steal)
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (nth-step-arg 1 ?excavate ?stolen)
                  (nth-step-arg 1 ?steal ?stolen)
                  (linked ?excavate ?steal)))

   (:action linked-by-has-indy-ark
     :parameters (?excavate - step ?steal - step ?indy - actor ?ark - item)
     :precondition (not (= ?excavate ?steal))
     :effect (bel-linked ?excavate ?steal)
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (name ?ark ark)
                  (name ?indy indiana)
                  (linked-by ?excavate ?steal (has ?indy ?ark))))

; there's a lot, so I'm not including it
  ;  (:action steal-before-excavate
   ;  :parameters (?excavate - step ?steal - step)
    ; :precondition (not (= ?excavate ?steal))
     ;:effect (bel-precedes ?steal ?excavate)
     ;:decomp (and (name ?excavate excavate)
      ;            (name ?steal steal)
       ;           (< ?steal ?excavate)))

    (:action impossible-sequence
     :parameters (?excavate - step ?steal - step)
     :precondition (not (= ?excavate ?steal))
     :effect (and (bel-linked ?excavate ?steal) (bel-precedes ?steal ?excavate))
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (linked ?excavate ?steal)
                  (< ?steal ?excavate)))

    (:action multi-sink
     :parameters (?excavate - step ?steal - step ?travel - step)
     :precondition (and (not (= ?excavate ?steal)) (not (= ?excavate ?travel)) (not (= ?steal ?travel)))
     :effect (and (bel-linked ?excavate ?steal) (bel-linked ?travel ?steal))
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (name ?travel travel)
                  (linked ?travel ?steal)
                  (linked ?excavate ?steal)))

    (:action multi-source
     :parameters (?excavate - step ?steal - step ?open-ark - step)
     :precondition (and (not (= ?excavate ?steal)) (not (= ?excavate ?open-ark)) (not (= ?steal ?open-ark)))
     :effect (and (bel-linked ?excavate ?open-ark) (bel-linked ?excavate ?steal))
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (name ?open-ark open-ark)
                  (linked ?excavate ?steal)
                  (linked ?excavate ?open-ark)))
)