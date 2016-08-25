
(define (domain mini-indy-domain)
  (:types character location - object)
  (:predicates (alive ?character - character)
               (adj ?loc1 - location ?loc2 - location)
			   (at ?character - character ?location - location)
			   (equals ?anything1 - object ?anything2 - object)
			   (high-up ?location - location)
			   (occupied ?location - location))


  (:action move
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (not (high-up ?from))
                       (not (high-up ?to))
                       (at ?character ?from))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to))
    :agents       (?character))


  (:action move-from-high-place
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (at ?character ?from)
                       (not (high-up ?to))
                       (high-up ?from))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to)
                       (not (occupied ?from)))
    :agents       (?character))

    (:action move-to-high-place
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (at ?character ?from)
                       (not (high-up ?from))
                       (high-up ?to)
                       (not (occupied ?to)))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to)
                       (occupied ?to))
    :agents       (?character))

   (:action move-across-high-places
    :parameters   (?character - character ?from - location ?to - location)
	:precondition (and (not (equals ?from ?to))
					   (adj ?from ?to)
                       (alive ?character)
                       (at ?character ?from)
                       (high-up ?to)
                       (high-up ?from)
                       (not (occupied ?to)))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to)
                       (occupied ?to)
                       (not (occupied ?from)))
    :agents       (?character))

  (:action fall-from
    :parameters   (?victim - character ?from - location)
	:precondition (and (alive ?victim)
                       (at ?victim ?from)
					   (high-up ?from))
	:effect       (and (not (at ?victim ?from))
                       (not (alive ?victim))))


 )