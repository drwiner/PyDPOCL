
(define (domain mini-indy-domain)
  (:types character location - object)
  (:predicates (alive ?character - character)
               (adj ?loc1 - location ?loc2 - location)
			   (at ?character - character ?location - location)
			   (equals ?anything1 ?anything2)
			   (high-up ?location - location)
			   (occupied ?location - location))

  (:axiom occupation
     :vars    (?location - location)
     :context (exists (?c - character)
                (at ?c ?location))
     :implies (occupied ?location))


  (:action move
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
	                   (not (high-up ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (at ?character ?from))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to))
    :agents       (?character))


  (:action move-balance
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (at ?character ?from)
                       (high-up ?to)
                       (not (occupied ?to)))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to))
    :agents       (?character))

  (:action fall-from
    :parameters   (?victim - character ?from - location)
	:precondition (and (alive ?victim)
                       (at ?victim ?from)
					   (high-up ?from))
	:effect       (and (not (at ?victim ?from))
                       (not (alive ?victim))))


 )