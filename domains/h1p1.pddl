(define (problem get-ark)
  (:domain indiana-jones-ark)
  (:objects indiana nazis army - character
            usa tanis - place
            ark - ark
            money - item
            gun - weapon)
  (:init (burried ark tanis)
         (alive indiana)
         (at indiana usa)
         (knows-location indiana ark tanis)
         (alive army)
         (at army usa)
         (alive nazis)
         (has army money)
         (at nazis tanis)
         (has nazis gun))
  (:goal (and
              (not (alive nazis))
              (cold-blooded army)
              ;(resourceful ark)
              ;(has army ark)
              )))