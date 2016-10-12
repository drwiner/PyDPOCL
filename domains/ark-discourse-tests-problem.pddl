(define (problem ark-discourse)
  (:domain ark-discourse-tests)
  (:objects steal - step
            excavate - step
            has-ark - literal
            ark - item
            indy - actor)


  (:init )

  (:action dummy_goal

     ; // these parameters become objects
     :parameters (?excavate - step ?steal - step ?has-ark - literal ?ark - item ?indy - actor)

     ; // preconditions are goals
     :precondition (and (bel-effect ?has-ark ?excavate) (bel-occurs ?steal)
                (bel-occurs ?excavate) (bel-effect ?has-ark ?excavate))

     ; // keep this here for now, should be empty though
     :effect ()

     ; // this forms the initial ingredients for the elements in the plan.
     :decomp (and (name ?excavate excavate)
                  (name ?steal steal)
                  (linked-by ?excavate ?steal ?has-ark)
                  (nth-lit-ark 0 ?has-ark ?indy)
                  (nth-lit-ark 1 ?has-ark ?ark)
                  (name ?ark ark)
                  (name ?indy indiana)))
 )