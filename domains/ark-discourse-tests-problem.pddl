(define (problem ark-discourse)
  (:domain ark-discourse-tests)
  (:objects steal - step excavate - step)
  ;(:elements (and (steal - step) (name steal steal) (
  (:init )
  (:goal (and
             (bel-occurs steal)
             (bel-occurs excavate)
              )))