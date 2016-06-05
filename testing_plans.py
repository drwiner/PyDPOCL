from PlanElementGraph import *

excavate = Operator(id = 1, type = 'Action', name = 'excavate', num_args = 3)

p1 = Literal(id=2, type='Condition', name= 'alive', 			num_args = 1, truth = True)
p2 = Literal(id=3, type='Condition', name= 'at', 				num_args = 2, truth = True)
p3 = Literal(id=4, type='Condition', name= 'burried', 			num_args = 2, truth = True)
p4 = Literal(id=5, type='Condition', name= 'knows-location', 	num_args = 3, truth = True)

e1 = Literal(id=6, type='Condition', name='burried',	num_args=2,	 truth = False)
e2 = Literal(id=7, type='Condition', name='has', 		num_args=2,	 truth = True)

consent = 	Actor(id=8,	 	type='actor',	 arg_pos_dict = {excavate.id :	1})
item = 		Argument(id = 9, 	type='var',		 arg_pos_dict=	{excavate.id :  2})
place = 	Argument(id = 10, 	type='var',		 arg_pos_dict=	{excavate.id :  3})

edge0 = Edge(excavate, consent, 'actor-of')
edge1 = Edge(excavate, p1,	 	'precond-of')
edge2 = Edge(excavate, p2, 		'precond-of')
edge3 = Edge(excavate, p3, 		'precond-of')
edge4 = Edge(excavate, p4, 		'precond-of')

edge5 = Edge(excavate, e1, 'effect-of')
edge6 = Edge(excavate, e2, 'effect-of')

edge7 = Edge(	p1, consent, 'first-arg')
edge8 = Edge(	p2, consent, 'first-arg')
edge9 = Edge(	p4, consent, 'first-arg')
edge10 = Edge(	e2, consent, 'first-arg')

edge12 = Edge(p2, item, 'sec-arg')
edge13 = Edge(p3, item, 'first-arg')
edge14 = Edge(p4, item, 'sec-arg')
edge15 = Edge(e1, item, 'first-arg')
edge16 = Edge(e2, item, 'sec-arg')

edge17 = Edge(p2, place, 'sec-arg')
edge18 = Edge(p3, place, 'sec-arg')
edge19 = Edge(p4, place, 'third-arg')
edge20 = Edge(e1, place, 'sec-arg')

excavate_elements = {excavate, p1, p2, p3, p4, e1, e2, consent, item, place}
excavate_edges = {edge0, edge1, edge2, edge3, edge4, edge5, edge6, edge7, edge8, edge9, edge10, \
					edge12, edge13, edge14,edge15, edge16,edge17, edge18, edge19, edge20}
					


	
example = Operator(id = 111, type= 'Action')

example_p1 =		Literal(id=211, 		type='Condition', 		name='alive', 		num_args = 1,	truth = True)
example_e1 = 		Literal(id=311, 		type = 'Condition', 	name='has', 	num_args = 2,		truth = True)
example_e3 = 		Literal(id=911, 		type = 'Condition', 	name='has', 			truth = True)
ex_const_element = 	Literal(id=611, 		type ='Condition',		name='knows-location', 	truth = True)
example_actor = 	Actor(id=411, 		type='actor',			arg_pos_dict={example.id : 1})
example_item = 		Argument(id=511,		type='var', 			arg_pos_dict={})
#arg_pos_dict={example.id : 0})

example_edge0 = Edge(example,	 example_p1, 	'precond-of')
example_edge1 = Edge(example,	 example_e1, 	'effect-of')
example_edge2 = Edge(example_p1, example_actor, 'first-arg')
example_edge3 = Edge(example_e1, example_actor, 'first-arg')
example_edge4 = Edge(example_e1, example_item, 	'sec-arg')

example_edge5 = Edge(example,	 example_e3, 	'effect-of')

#Cannot have a precondition with name 'knows-location', first-arg is actor, sec-arg is item
#Since we know this is precondition of excavate, the example_graph should not be consistent


example_constraint_edge0 = Edge(ex_const_element, example_actor,	'first-arg')
example_constraint_edge1 = Edge(ex_const_element, example_item, 	'sec-arg')

example_elements = 	{	example, \
						example_p1, \
						example_e1, \
					#	example_e3,\
						example_actor, \
						example_item,\
						ex_const_element}
						
example_edges = 	{example_edge0,example_edge1,example_edge2,example_edge3,example_edge4}

						
example_constraints = {	example_constraint_edge0, \
						example_constraint_edge1}


####Operator - Domain Action
Excavate_operator =			Action(	id = 200,\
							graph_type = 'Action', \
							name = 'excavate', \
							Elements = excavate_elements, \
							root_element = excavate,\
							Edges = excavate_edges)

Example_step =	 			Action(	id = 1111, \
							graph_type='Action', \
							Elements = example_elements, \
							root_element = example,\
							Edges = example_edges, \
							Constraints = example_constraints)

Excavate_operator_A = Excavate_operator.copyGen()
Example_step_A  = Example_step.copyGen()

Excavate_operator_B = Excavate_operator.makeCopyFromID(9000,11)
#print(Excavate_graph_A.root.id)
Example_step_B  = Example_step.copyGen()

#print('\n\texcavate operator:')
#Excavate_operator_A.print_graph()


F	=	IntentionFrame(id = 2222, type_graph = 'IntentionFrame', name=None, \
		Elements=example_elements,\
		Edges=example_edges,\
		Constraints=example_constraints,\
		goal = example_e1,#change with example_p1 to fail\
		ms = None,\
		sat = example,\
		actor=None)
		
example_elements.add(F.root) #Intention Frame element

# example_elements.add(IntentionFrameElement(	id = 2222, type_graph = 'IntentionFrame', name=None, \
													# ms =None, \
													# motivation =None,\
													# intender = None,\
													# goal = example_e1,\
													# sat = example\
													# )

P1 = 	PlanElementGraph(id = 5432,\
		Elements=example_elements,\
		Edges=example_edges,\
		Constraints=example_constraints)


#print('\n\tintention_frame:')						
#print(len(F.Steps))
#F.print_frame()


print('\n\tPlan')
#print(len(P1.Steps))
#P1.print_plan()

s = next(iter(P1.Steps))
step = P1.getElementGraphFromElement(s, Action)
P1.print_plan()
new_plans = step.instantiate(Excavate_operator_A,P1)


print('num_consenting actors = {} in step {}'.format(len(P1.getConsistentActors(P1.Steps)),step.id))

#print(step.id)

print('num new plans: {}'.format(len(new_plans)))
for plan in new_plans:
	print('num_consenting actors = {} in steps'.format(len(plan.getConsistentActors(plan.Steps))))
#	plan.print_plan()
	#for element in plan.elements:
		#element.print_element()
		


""" Test whether Actions in F.Steps are equivalent to Actions created in isolation"""
""" Test rPickActorFromSteps when there are and are not consistent_actors"""

"""	Test adding step to an intention frame if already in plan. 
"""