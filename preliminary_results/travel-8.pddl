(define (problem travel-8)
    (:domain car-plane-world)
    
    (:objects roger sara dave bob - person
              raleigh la slc ny - place
              accord - car
              747 - plane)
              
    (:init 
		(at roger slc)
		(at dave slc)
        (at bob raleigh)
		(at sara raleigh)
        (at accord raleigh)
        (at 747 raleigh))
        
    (:goal (at dave ny) (at roger la)))