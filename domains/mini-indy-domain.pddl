
(define (domain mini-indy-domain)
  (:types character location - object)
  (:predicates (alive ?character - character)
               (adj ?loc1 - location ?loc2 - location)
			   (at ?character - character ?location - location)
			   (equals ?anything1 ?anything2)
			   (high-up ?location - location))

  (:action move
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
                       (alive ?character)
                       (at ?character ?from))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to))
    :agents       (?character))

  (:action fall-from
    :parameters   (?victim - character ?from - location)
	:precondition (and (alive ?victim)
                       (at ?victim ?from)
					   (high-up ?from))
	:effect       (and (not (at ?victim ?from))
                       (not (alive ?victim)))))