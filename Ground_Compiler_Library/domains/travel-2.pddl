(define (problem travel-2)
    (:domain car-plane-world)
    
    (:objects bob sara - person
              raleigh la - place
              accord - car
              747 - plane)
              
    (:init 
        (at bob raleigh)
		(at sara raleigh)
        (at accord raleigh)
        (at 747 raleigh))
        
    (:goal (at sara la)))