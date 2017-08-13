(define (problem travel-6)
    (:domain car-plane-world)
    
    (:objects bob sara - person
              raleigh la slc - place
              accord - car
              747 - plane)
              
    (:init 
        (at bob raleigh)
		(at sara la)
        (at accord la)
        (at 747 raleigh))
        
    (:goal (at sara slc) (at bob slc)))