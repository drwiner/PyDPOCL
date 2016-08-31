(define (domain western-duel)
  (:requirements)
  (:types character place item - object
          gun horse lasso door bottle cig tnt - item
		  )
  (:predicates 	   
			   (has ?c - character ?it - item)
			   (at ?object - object ?place - place)
			   (has ?character - character ?item - item)
			   (= ?obj - object ?obj2 - object)
			   
			   ;guns
			   (armed ?character - character)
			   (deholstered ?g1 - gun)
			   (cocked ?g1 - gun)
			   (raised ?g1 - gun)
			   (loaded ?g1 - gun)
			   (aimed-at ?g1 - gun ?target - object)
			   (marksman ?c - character)
			   (hit-by-bullet ?ob - object)
			   
			   ;hands
			   (ready-to-grab ?c - character ?g - gun)
			   (hands-busy ?c - character)
			   
			   ;cognitive
			   (stare-at ?c1 - character ?ob - object)
			   (sees ?c1 - character ?it - item)
               
			   ;char states
			   (alive ?character - character)
			   (sitting ?c1 - character)
			   (tied-up ?c - character)
			   (smoking ?c - character ?cig - cig)
			   (cowboy ?c - character)
			   (angry ?c - character)
			   (scared ?c - character)
			   (drunk ?c - character)
			   (cowering ?c1 - character)
			   
			   ;item specific
			   (open ?door - door)
			   (on-horse ?c1 - character ?h1 - horse)
			   )


  (:action grab-gun
    :parameters   (?grabber - character ?g1 - gun ?holder - character ?place - place)
	:precondition (and 
                       (alive ?grabber)
                       (at ?grabber ?place)
					   (at ?holder ?place)
					   (deholstered ?g1)
					   (sees-gun ?grabber ?g1)
					   (raised ?g1)
					   (has ?holder ?g1)
					   (not (hands-busy ?grabber))
					   )
	:effect       (and (has ?grabber ?g1)
						(not (has ?holder ?g1))
                       )
    :agents       (?grabber))


  (:action fire-gun
    :parameters   (?shooter - character ?gun - gun ?target - object ?place - place)
	:precondition (and (alive ?shooter)
                       (at ?shooter ?place)
                       (at ?target ?place)
					   (has ?shooter ?gun)
					   (aimed-at ?gun ?target)
					   (cocked ?gun)
					   (loaded ?gun)
					   (sees ?shooter ?target)
                       )
	:effect       (and (
                       (hit-by-bullet ?target))
    :agents       (?shooter))


  (:action raise-gun
    :parameters   (?shooter - character ?gun - gun)
	:precondition (and (alive ?shooter)
                       (has ?shooter ?gun)
					   (deholstered ?gun)
                       )
	:effect       (and (not (deholstered ?gun))
					(raised ?gun))
    :agents       (?shooter))
	
  (:action cock-gun
    :parameters   (?shooter - character ?gun - gun)
	:precondition (and (alive ?shooter)
                       (has ?shooter ?gun)
					   (deholstered ?gun)
                       )
	:effect       (and (not (deholstered ?gun))
					(raised ?gun))
    :agents       (?shooter))


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

)