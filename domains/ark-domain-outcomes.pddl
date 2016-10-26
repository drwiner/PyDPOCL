(define (domain indiana-jones-ark)
  (:requirements)
  (:types step arg literal name-str - object
          n - name-str
          0 1 2 3 4 5 - n
          character place item - arg
          weapon - item
		  ark - item
		  money - item
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
               (precond ?step - step ?lit - literal)
               (allies ?c1 - character ?c2 - character)
              )


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
                       (allies ?giver ?receiver)
                       (at ?receiver ?place))
	:effect       (and (not (has ?giver ?item))
                       (has ?receiver ?item))
    :agents       (?giver ?receiver))


  (:action kill
    :parameters   (?killer - character ?weapon - weapon ?victim - character ?place - place)
    :precondition (and
                       (not (allies ?killer ?victim))
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
                       (not (allies ?taker ?victim))
                       (has ?victim ?item))
	:effect       (and (not (has ?victim ?item))
                       (has ?taker ?item))
    :agents       (?taker))


   ;(:action backstab-steal
   ;  :parameters (?p1 - character ?p2 - character ?item - item ?place - place)
   ;  :precondition (and (allies ?p1 ?p2)
   ;                     (has ?p1 ?item)
   ;                     (at ?p1 ?place)
   ;                     (at ?p2 ?place)
   ;                     (not (= ?p1 ?p2)))
   ;  :effect (and (not (allies ?indy ?item))
   ;               (has ?p2 ?item)
   ;               (not (has ?p1 ?item))))
	

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
        :parameters (?p1 - character ?p2 - character ?item1 - item ?item2 - item ?place - place)
        :precondition (and (has ?p1 ?item1)
                           (has ?p2 ?item2)
                           (at ?p1 ?place)
                           (at ?p2 ?place))
        :effect (and (has ?p1 ?item2)
                     (has ?p2 ?item1))
    )

   (:action betray-ally-fo-money
        :parameters (?traitor - character ?victim - character ?enemy - character ?ark - ark ?take - step ?trade - step ?money - money)
        :precondition (and  (not (= ?traitor ?victim))
                            (not (= ?take ?trade))
                            (not (= ?traitor ?enemy))
                            (not (= ?victim ?enemy))
                            (allies ?traitor ?victim)
                            (not (allies ?victim ?enemy))
                            (alive ?victim)
                            (alive ?traitor)
                            (alive ?enemy)
                            (has ?victim ?ark)
                            (has ?enemy ?money))
        :effect (and (not (alive ?victim))
                     (not (allies ?traitor ?victim))
                     (has ?enemy ?ark)
                     (has ?traitor ?money))
        :decomp (and
                  ;   (remove-precond ?take (not (allies ?trickster ?victim)))
                     (nth-step-arg 0 ?take ?traitor)
                     (nth-step-arg 2 ?take ?victim)
                     (effect ?take (has ?traitor ?ark))
                     (linked-by ?take ?trade (has ?traitor ?ark))
                     (name ?trade trade)
                     (effect ?trade (has ?traitor ?money))
                     (effect ?trade (has ?enemy ?ark))
                     ))

    (:action its-a-trap
     :parameters (?trickster - character ?victim - character ?ark - ark ?give - step ?kill - step ?take - step)
     :precondition (and
                     (not (= ?give ?kill))
                     (not (= ?give ?take))
                     (not (= ?take ?kill))
                     (not (= ?trickster ?victim))
                     (has ?trickster ?ark)
                     (not (allies ?trickster ?victim)))
     :effect (and (has ?trickster ?ark) (not (alive ?victim)))
     :decomp (and   (name ?kill kill)
                    (nth-step-arg 0 ?kill ?trickster)
                    (nth-step-arg 2 ?kill ?victim)
                    (effect ?take (has ?trickster ?ark))
                    (precond ?take (not (alive ?victim)))
                    (name ?give give)
                    (nth-step-arg 0 ?give ?trickster)
                    (effect ?give (has ?victim ?ark))
                    (linked ?give ?take)
                    (< ?give ?kill)
                    (linked ?kill ?take)))

)