(define (domain indiana-jones-ark)
  (:requirements)
  (:types step arg literal name-str - object
          n - name-str
          0 1 2 3 4 5 - n
          character place item - arg
          weapon - item
		  money - item
		  ark - item
		  ;adding these is a hack that should be done elsewhere:
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
               (nth-lit-arg ?n - n ?lit - literal ?arg - arg)
               (effect ?step - step ?lit - literal)
               (linked-by ?source - step ?sink - step ?dependency - literal)
               (cold-blooded ?char - character)
               (resourceful ?char - character))


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


   (:action trade
	:parameters (?trader - character ?trader-2 - character ?item - item ?item-2  - item ?place - place ?give1 - step ?give2 - step)
	:precondition(and
	        (not (= ?give1 ?give2))
	        (not (= ?trader ?trader-2)) (not (= ?item ?item-2)))
	:effect (and (has ?trader-2 ?item-2) (has ?trader ?item))
	:decomp (and
	            (name ?give1 give)
	            (name ?give2 give)
	            (nth-step-arg 0 ?give1 ?trader)
	            (nth-step-arg 1 ?give1 ?item-2)
	            (nth-step-arg 2 ?give1 ?trader-2)
	            (nth-step-arg 3 ?give1 ?place)
	            (nth-step-arg 0 ?give2 ?trader-2)
	            (nth-step-arg 1 ?give2 ?item)
	            (nth-step-arg 2 ?give2 ?trader)
	            (nth-step-arg 3 ?give2 ?place))
	)


   (:action kill-take
     :parameters (?taker - character ?victim - character ?item - item ?kill - step ?take - step)
     :precondition (and (not (= ?taker ?victim)) (not (= ?kill ?take)))
     :effect (and (has ?taker ?item) (not (alive ?victim)) (cold-blooded ?taker))
     :decomp (and
                  (name ?take take-from-corpse)
                  (name ?kill kill)
				  (nth-step-arg 0 ?kill ?taker)
				  (nth-step-arg 2 ?kill ?victim)
				  (nth-step-arg 0 ?take ?taker)
				  (nth-step-arg 1 ?take ?item)
				  (nth-step-arg 2 ?take ?victim)
				  (effect ?kill (not (alive ?victim)))
				  (effect ?take (has ?taker ?item))
				  (effect ?take (not (has ?victim ?item)))
				  (linked-by ?kill ?take (not (alive ?victim)))
                ))
				 
;   (:action get-item-for-trade
;	:parameters (?doer - character ?item-has - item ?item-want - item ?haver - character ?get - step ?trade - step)
;	:precondition (and
;						(not (= ?get ?trade))
;						(not (= ?doer ?haver))
;						(not (= ?item-has ?item-want)))
;	:effect (and (has ?doer ?item-want) (has ?haver ?item-has)
;				 (resourceful ?doer))
;	:decomp (and
;				 (effect ?trade (has ?doer ?item-want))
;				 (precond ?trade (has ?doer ?item-has))
;				 (precond ?trade (has ?haver ?item-want))
;				 (effect ?trade (has ?haver ?item-has))
;				 (nth-step-arg 0 ?get ?doer)
;				 (linked-by ?get ?trade (has ?doer ?item-has))
;				))

)