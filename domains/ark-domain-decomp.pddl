(define (domain indiana-jones-ark)
  (:requirements)
  (:types step arg literal name-str - object
          n - name-str
          0 1 2 3 4 5 - n
          character place item - arg
          weapon - item
		  ark - item
		  Action - step
		  Condition - literal
		  )
  (:predicates (open ?ark - ark)
               (alive ?character - character)
               (armed ?character - character)
               (burried ?item - item ?place - place)
               (knows-location ?character - character ?item - item ?place - place)
               (at ?character - character ?place - place)
               (= ?obj - object ?obj2 - object)
               (has ?character - character ?item - item)
               (< ?source - step ?sink - step)
               (name ?obj - object ?name - name-str)
               (nth-step-arg ?n - n ?step - step ?arg - arg)
               (effect ?step - step ?lit - literal)
               (chases ?char - character ?char2 - character))


  (:action travel
    :parameters   (?character - character ?from - place ?to - place)
	:precondition (and
	                   (not (= ?from ?to))
                       (alive ?character)
                       (at ?character ?from))
	:effect       (and (not (at ?character ?from))
                       (at ?character ?to))
    :agents       (?character))


  (:action excavate
    :parameters   (?character - character ?item - item ?place - place)
	:precondition (and (alive ?character)
                       (at ?character ?place)
                       (burried ?item ?place)
                       (knows-location ?character ?item ?place))
	:effect       (and (not (burried ?item ?place))
                       (has ?character ?item))
    :agents       (?character))


  (:action give
    :parameters   (?giver - character ?item - item ?receiver - character ?place - place)
	:precondition (and
	                   (not (= ?giver ?receiver))
                       (alive ?giver)
                       (at ?giver ?place)
                       (has ?giver ?item)
                       (alive ?receiver)
                       (at ?receiver ?place))
	:effect       (and (not (has ?giver ?item))
                       (has ?receiver ?item))
    :agents       (?giver ?receiver))


  (:action kill
    :parameters   (?killer - character ?weapon - weapon ?victim - character ?place - place)
    :precondition (and
                       (not (= ?killer ?victim))
                       (alive ?killer)
                       (at ?killer ?place)
                       (has ?killer ?weapon)
                       (alive ?victim)
                       (at ?victim ?place))
    :effect       (not (alive ?victim))
    :agents       (?killer))
  

  (:action steal
    :parameters   (?taker - character ?item - item ?victim - character ?place - place)
	:precondition (and
	                   (not (= ?taker ?victim))
                       (alive ?taker)
                       (at ?taker ?place)
                       (armed ?taker)
                       (not (armed ?victim))
                       (at ?victim ?place)
                       (has ?victim ?item))
	:effect       (and (not (has ?victim ?item))
                       (has ?taker ?item))
    :agents       (?taker))
	

  (:action take-from-corpse
    :parameters   (?taker - character ?item - item ?victim - character ?place - place)
	:precondition (and
	                   (not (= ?taker ?victim))
                       (alive ?taker)
                       (at ?taker ?place)
                       (not (alive ?victim))
                       (at ?victim ?place)
                       (has ?victim ?item))
	:effect       (and (not (has ?victim ?item))
                       (has ?taker ?item))
    :agents       (?taker))


  (:action open-ark
    :parameters   (?character - character ?ark - ark)
	:precondition (and (alive ?character)
                       (has ?character ?ark))
	:effect       (and (open ?ark)
                       (not (alive ?character)))
    :agents       (?character))


  (:action close-ark
	:parameters (?ark - ark)
	:precondition (open ?ark)
	:effect       (not (open ?ark)))


     ;; When a character has a weapon, they are armed.
   (:action armed-axiom
     :parameters    (?character - character ?w - weapon)
     :precondition (has ?character ?w)
     :effect (armed ?character))

    (:action unarmed-axiom
     :parameters    (?character - character ?w - weapon)
     :precondition (not (has ?character ?w))
     :effect (not (armed ?character)))

    (:action chase-scene
        :parameters (?c1 - character ?c2 - character
                    ?t1 - step ?t2 - step ?t3 - step
                    ?t4 - step ?t5 - step ?t6 - step
                    ?place1 - place ?place2 - place)
        :precondition (and (at ?c1 ?place1) (at ?c2 ?place1) (not (= ?c1 ?c2)))
        :effect (and (chases ?c2 ?c1) (at ?c1 ?place2) (at ?c2 ?place2))
        :decomp (and (name ?t1 travel) (name ?t2 travel) (name ?t3 travel)
                (name ?t4 travel) (name ?t5 travel) (name ?t6 travel)
                (< ?t1 ?t2) (< ?t2 ?t3) (< ?t3 ?t4) (< ?t4 ?t5) (< ?t5 ?t6)
                (nth-step-arg 0 ?t1 ?c1) (nth-step-arg 0 ?t3 ?c1) (nth-step-arg 0 ?t5 ?c1)
                (nth-step-arg 0 ?t2 ?c2) (nth-step-arg 0 ?t4 ?c2) (nth-step-arg 0 ?t6 ?c2)
                ))

)