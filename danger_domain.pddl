(define (domain danger_domain)
    
    (:types step actor - var predicate-name state valence)
    
    (:constants ALIVE - predicate-name AT - predicate-name TRUE - valence FALSE - valence)
    
    (:predicates (effect-of ?step - step ?state - state)
                 (not-effect-of ?step - step ?state - state)
				 (precond-of ?step - step ?state - state)
				 (not-precond-of ?step - step ?state - state)
				 (executed ?step - step ?valence - valence)
				 (truth ?state - state ?valence - valence)
				 (has-executed-status ?step - step)
				 (has-valence ?state - state)
				 (has-predicate-name ?state - state)
				 (has-first-term ?state - state)
				 (has-sec-term ?state - state)	
				 (predicate-of ?state - state ?var - predicate-name)
				 (first-term-of ?state - state ?var - var)
				 (sec-term-of ?state - state ?var - var)
				 (bel-danger-at ?var - var)
				 (bel-in-danger ?actor - actor)
				 (is-hero ?actor - actor)
				 (bel-state-1-var ?valence - valence ?pred-name - predicate-name ?var - var)
				 (bel-state-2-var ?valence - valence ?pred-name - predicate-name ?var1 - var ?var2 - var))
    
    (:action convey-danger-at
        :parameters (?loc - var ?deathstep - step ?victim - actor ?dstate - state ?loc-state - state)
        :abstract f
        :precondition (and (effect-of ?deathstep ?dstate)
							(precond-of ?deathstep ?loc-state)
							(executed ?deathstep TRUE)
							(truth ?dstate FALSE)
							(predicate-of ?dstate ALIVE)
							(first-term-of ?dstate ?victim)
							(predicate-of ?loc-state AT)
							(first-term-of ?loc-state ?victim)
							(sec-term-of ?loc-state ?loc)
							(truth ?loc-state TRUE))
        :effect (and (bel-danger-at ?loc)(bel-state-1-var FALSE ALIVE ?victim)))
		
	(:action convey-in-danger
        :parameters (?hero - actor ?dloc - var ?move - step ?dstate - state)
        :abstract f
        :precondition (and (effect-of ?move ?dstate)
							(executed ?move TRUE)
							(truth ?dstate TRUE)
							(predicate-of ?dstate AT)
							(first-term-of ?dstate ?hero)
							(sec-term-of ?dstate ?dloc)
							(bel-danger-at ?dloc)
							(not (bel-state-1-var FALSE ALIVE ?hero)))
        :effect (bel-in-danger ?hero))
		
	(:action assign-execution
		:parameters (?step - step ?valence - valence)
		:abstract f
		:precondition (not (has-executed-status ?step))
		:effect (and (executed ?step ?valence) (has-executed-status ?step)))
		
	(:action assign-valence
		:parameters (?state - state ?valence - valence)
		:abstract f
		:precondition (not (has-valence ?state))
		:effect (and (truth ?state ?valence) (has-valence ?state)))
		
		
	(:action assign-predicate
		:parameters (?state - state ?pred-name - predicate-name)
		:abstract f
		:precondition (not (has-predicate-name ?state))
		:effect (and (has-predicate-name ?state)(predicate-of ?state ?pred-name)))

	(:action assign-first-term
		:parameters (?state - state ?term-name - var)
		:abstract f
		:precondition (not (has-first-term ?state))
		:effect (and (has-first-term ?state)(first-term-of ?state ?term-name)))
		
	(:action assign-sec-term
		:parameters (?state - state ?term-name - var)
		:abstract f
		:precondition (not (has-sec-term ?state))
		:effect (and (has-sec-term ?state)(sec-term-of ?state ?term-name)))
		
	(:action assign-effect
		:parameters (?step - step ?state - state)
		:abstract f
		:precondition (and (not (effect-of ?step ?state)) 
							(not (not-effect-of ?step ?state)))
		:effect (effect-of ?step ?state))
		
	(:action assign-precond
		:parameters (?step - step ?state - state)
		:abstract f
		:precondition (and (not (precond-of ?step ?state)) 
							(not (not-precond-of ?step ?state)))
		:effect (precond-of ?step ?state))
    )