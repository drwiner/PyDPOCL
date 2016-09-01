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
			   (adj ?p1 - place ?p2 - place)
			   
			   ;guns
			   (armed ?character - character)
			   (deholstered ?g - gun)
			   (cocked ?g - gun)
			   (raised ?g - gun)
			   (loaded ?g - gun)
			   (aimed-at ?g - gun ?target - object)
			   (marksman ?c - character)
			   (hit-by-bullet ?ob - object)
			   
			   ;hands
			   (ready-to-grab ?c - character ?g - gun)
			   (hands-busy ?c - character)
			   
			   ;cognitive
			   (stare-at ?c - character ?ob - object)
			   (sees ?c - character ?it - item)
               
			   ;char states
			   (alive ?character - character)
			   (sitting ?c1 - character)
			   (tied-up ?c - character)
			   (cowboy ?c - character) ;cowboys can lasso
			   (angry ?c - character)
			   (scared ?c - character)
			   (drunk ?c - character)
			   (cowering ?c - character)
			   
			   ;item specific
			   (open ?door - door)
			   (on-horse ?c - character ?h - horse)
			   (smoking ?c - character ?cig - cig)
			   (drinking ?c - character ?bot - bottle)
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
	
	
  (:action sharpshoot
    :parameters   (?shooter - character ?gun - gun ?target - object ?p1 - place ?p2 - place)
	:precondition (and (alive ?shooter)
                       (at ?shooter ?p1)
                       (at ?target ?p2)
					   (adj ?p1 ?p2)
					   (has ?shooter ?gun)
					   (aimed-at ?gun ?target)
					   (cocked ?gun)
					   (loaded ?gun)
					   (marksman ?shooter)
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
	:effect       (and 
					(raised ?gun))
    :agents       (?shooter))
	
  (:action lower-gun
    :parameters   (?shooter - character ?gun - gun)
	:precondition (and (alive ?shooter)
                       (has ?shooter ?gun)
					   (raised ?gun)
                       )
	:effect       (and 
					(not (raised ?gun)))
    :agents       (?shooter))
	
  (:action cock-gun
    :parameters   (?shooter - character ?gun - gun)
	:precondition (and (alive ?shooter)
                       (has ?shooter ?gun)
                       )
	:effect       (and (cocked ?gun))
    :agents       (?shooter))
	
	(:action aim-gun
    :parameters   (?shooter - character ?gun - gun ?target)
	:precondition (and (alive ?shooter)
                       (has ?shooter ?gun)
					   (raised ?gun)
					   (sees ?shooter ?target)
                       )
	:effect       (and 
					(aimed-at ?gun ?target))
    :agents       (?shooter))
	
	(:action dodge-fire
		:parameters (?dodger - character ?shooter - character ?gun - gun)
		:precondition (and (alive ?dodger)
							(alive ?shooter)
							(has ?shooter ?gun)
							(sees ?dodger ?gun)
							(raised ?gun)
							(cocked ?gun)
							(aimed-at ?shooter ?dodger)
							(loaded ?gun))
		:effect (and (not (aimed-at ?shooter ?dodger)))
		:agents (?dodger))
		
	(:action dodge-fire-from-drunk
		:parameters (?dodger - character ?shooter - character ?gun - gun)
		:precondition (and (alive ?dodger)
							(alive ?shooter)
							(has ?shooter ?gun)
							(sees ?dodger ?gun)
							(raised ?gun)
							(cocked ?gun)
							(aimed-at ?shooter ?dodger)
							(drunk ?shooter)
							(loaded ?gun))
		:effect (and (not (aimed-at ?shooter ?dodger)))
		:agents (?dodger))
	
	(:action holster-gun
		:parameters (?carrier - character ?gun - gun)
		:precondition (and (has ?carrier ?gun)
						(deholstered ?gun)
						(alive ?carrier))
		:effect (and (not (deholstered ?gun))
					(not (hands-busy)))
		:agents (?carrier))
		
	(:action draw-gun
		:parameters (?drawer - character ?gun - gun)
		:precondition (and (has ?drawer ?gun)
							(not (deholstered ?gun))
							(not (hands-busy ?drawer))
							(alive ?drawer))
		:effect (and (deholstered ?gun)
					(hands-busy ?drawer))
		:agents (?drawer))
	

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


   (:action armed-axiom
     :parameters    (?character - character ?g - gun)
     :precondition (has ?character ?g)
     :effect (armed ?character))

    (:action unarmed-axiom
     :parameters    (?character - character ?g - gun)
     :precondition (not (has ?character ?g))
     :effect (not (armed ?character)))
	 
	(:action sees-adj-axiom
     :parameters    (?seer - character ?seee - object ?p1 - place ?p2 - place)
     :precondition (and (at ?seer ?p1) (at ?seee ?p2) (adj ?p1 ?p2))
     :effect (sees ?seer ?seee))
	 
	(:action sees-axiom
     :parameters    (?seer - character ?seee - object ?p1 - place)
     :precondition (and (at ?seer ?p1) (at ?seee ?p1))
     :effect (sees ?seer ?seee))
	 
	(:action stare-at-drunk-axiom
     :parameters    (?starer - character ?seee - character ?p1 - place)
     :precondition (and (at ?seer ?p1) (at ?seee ?p1) (drunk ?starer))
     :effect (stare-at ?starer ?seee))
	 
	(:action drunk-gets-angry
     :parameters    (?starer - character ?drunk - character ?p1 - place)
     :precondition (and (at ?seer ?p1) (at ?seee ?p1) (stare-at ?starer ?drunk) (not (scared ?drunk)))
     :effect (angry ?drunk))
	 
	(:action gets-scared
     :parameters    (?weakling - character ?starer - character ?p1 - place)
     :precondition (and (at ?weakling ?p1) (at ?starer ?p1) (stare-at ?starer ?weakling))
     :effect (scared ?weakling))
	 
	(:action cowers
	:parameters (?scaredy-cat - character ?starer - charater ?gun - gun ?p - place)
	:precondition (and (at ?scaredy-cat ?p) (at ?starer ?p) (scared ?scaredy-cat) (stare-at ?starer ?scaredy-cat)
					(has ?starer ?gun)
					(deholstered ?gun))
	:effect (cowering ?scaredy-cat))
	
	(:action get-brave
	:parameters (?scaredy-cat - character ?bot - bottle)
	:precondition (and (scared ?scaredy-cat)
						(has ?scaredy-cat ?bot))
	:effect (and (not (scared ?scaredy-cat))
					(drunk ?scaredy-cat))
	:agents (?scaredy-cat))

)