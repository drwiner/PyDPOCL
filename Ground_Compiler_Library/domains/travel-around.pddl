(define (problem travel-around)
    (:domain car-plane-world)
    
    (:objects david sara bea - person
              raleigh slc - place
              mazda - car
              united delta - plane)
              
    (:init
        (at sara slc)
        (at david slc)
        (at bea raleigh)
        (at mazda slc)
        (at united nyc)
        (at delta slc)
        )
        
    (:goal (and  (at sara raleigh) (at david raleigh) (at bea raleigh)
                )))