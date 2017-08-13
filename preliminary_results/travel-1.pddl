(define (problem travel-to-la)
    (:domain car-plane-world)
    
    (:objects bob - person
              raleigh la - place
              accord - car
              747 - plane)
              
    (:init 
        (at bob raleigh)
        (at accord raleigh)
        (at 747 raleigh))
        
    (:goal (at bob la)))