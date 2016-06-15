(define (problem danger-problem)
    (:domain danger_domain)
    
    (:objects Hero - actor 
			fall-from - step 
			move - step)
     
    (:init
        (is-hero Hero))
        
    (:goal 
		(bel-in-danger Hero)
		))