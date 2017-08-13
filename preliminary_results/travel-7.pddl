(define (problem travel-7)
    (:domain car-plane-world)
    
    (:objects bob - person
              raleigh la - place
              accord mazda - car
              747 - plane)
              
    (:init 
        (at bob raleigh)
        (at accord raleigh)
        (at 747 raleigh))
        
    (:goal (at bob la)))