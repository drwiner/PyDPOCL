(define (domain movie-strips)
  (:predicates (movie-rewound)
               (counter-at-two-hours)
			   (counter-at-other-than-two-hours)
               (counter-at-zero)
               (have-chips)
               (have-dip)
               (have-pop)
               (have-cheese)
               (have-crackers)
               (chips ?x)
               (dip ?x)
               (pop ?x)
               (cheese ?x)
               (crackers ?x))
  
  (:action rewind-movie-2
           :parameters ()
		   :precondition (counter-at-two-hours)
           :effect (movie-rewound)
		   :prerequisite (chips ?x))
  
  (:action rewind-movie
           :parameters ()
		   :precondition (counter-at-other-than-two-hours)
           :effect (and (movie-rewound)
                        ;; Let's assume that the movie is 2 hours long
                        (not (counter-at-zero)))
		   :prerequisite (?x))

  (:action reset-counter
           :parameters ()
           :precondition (and)
           :effect (counter-at-zero)
		   :prerequisite (not))

  ;;; Get the food and snacks for the movie
  (:action get-chips

           :parameters (?x)
           :precondition (chips ?x)
           :effect (have-chips)
		   :prerequisite (chips ?x))
  
  (:action get-dip
           :parameters (?x)
           :precondition (dip ?x)
           :effect (have-dip)
		   :prerequisite (chips ?x))

  (:action get-pop
           :parameters (?x)
           :precondition (pop ?x)
           :effect (have-pop)
		   :prerequisite (chips ?x))
  
  (:action get-cheese
           :parameters (?x)
           :precondition (cheese ?x)
           :effect (have-cheese)
		   :prerequisite (chips ?x))
  
  (:action get-crackers
           :parameters (?x)
           :precondition (crackers ?x)
           :effect (have-crackers)
		   :prerequisite (chips ?x)))