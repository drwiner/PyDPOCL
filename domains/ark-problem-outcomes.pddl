(define (problem get-ark)
  (:domain indiana-jones-ark)
  (:objects indiana nazis army - character
            usa tanis - place
            ark - ark
            money - money
            gun - weapon)
  (:init (burried ark tanis)
         (alive indiana)
         (at indiana usa)
         (knows-location indiana ark tanis)
         (alive army)
         (at army usa)
         (alive nazis)
         (at nazis tanis)
         (has nazis money)
         (allies indiana army)
         (allies army indiana)
         (has nazis gun))
  (:goal (and
              (not (alive nazis))
              (has army ark)
              ))

  )