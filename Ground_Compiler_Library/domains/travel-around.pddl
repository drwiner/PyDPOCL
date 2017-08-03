(define (problem travel-around)
    (:domain car-plane-world)
    
    (:objects david sara bea julie tbone stef - person
              raleigh la slc nyc - place
              accord saab mazda - car
              united southwest delta - plane)
              
    (:init
        (at sara la)
        (at david slc)
        (at julie raleigh)
        (at bea raleigh)
        (at tbone nyc)
        (at stef la)
        (at saab nyc)
        (at mazda slc)
        (at accord la)
        (at united nyc)
        (at southwest la)
        (at delta slc)
        )
        
    (:goal (and (at julie nyc) (at tbone slc) (at stef slc) (at sara raleigh) (at david slc) (at bea raleigh)
                )))