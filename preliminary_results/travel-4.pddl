(define (problem travel-4)
    (:domain car-plane-world)
    
    (:objects bob sara - person
              raleigh la - place
              accord - car
              747 - plane)
              
    (:init 
        (at bob raleigh)
		(at sara la)
        (at accord raleigh)
        (at 747 raleigh))
        
    (:goal (at sara raleigh) (at bob la)))