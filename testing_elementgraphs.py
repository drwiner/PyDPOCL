from PlanElementGraph import *

excavate = Operator(id = 1, type = 'Action', name = 'excavate', num_args = 3)

p1 = Literal(id=2, type='Condition', name= 'alive', 			num_args = 1, truth = True)
p2 = Literal(id=3, type='Condition', name= 'at', 				num_args = 2, truth = True)
p3 = Literal(id=4, type='Condition', name= 'burried', 			num_args = 2, truth = True)
p4 = Literal(id=5, type='Condition', name= 'knows-location', 	num_args = 3, truth = True)

e1 = Literal(id=6, type='Condition', name='burried',	num_args=2,	 truth = False)
e2 = Literal(id=7, type='Condition', name='has', 		num_args=2,	 truth = True)

consent = 	Argument(id=8,	 	type='actor',	 arg_pos_dict = {excavate.id :	1})
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

example_p1 =		Literal(id=211, 		type='Condition', 		name='alive', 			truth = True)
example_e1 = 		Literal(id=311, 		type = 'Condition', 	name='has', 			truth = True)
example_e3 = 		Literal(id=911, 		type = 'Condition', 	name='has', 			truth = True)
ex_const_element = 	Literal(id=611, 		type ='Condition',		name='knows-location', 	truth = True)
example_actor = 	Argument(id=411, 		type='actor',			arg_pos_dict={example.id : 1})
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
Excavate_graph = Action(	id = 0,\
							graph_type = 'Action', \
							name = 'excavate', \
							Elements = excavate_elements, \
							root_element = excavate,\
							Edges = excavate_edges)

Example_graph =	 Action(	id = 1111, \
							graph_type='Action', \
							Elements = example_elements, \
							root_element = example,\
							Edges = example_edges, \
							Constraints = example_constraints)

Excavate_graph_A = Excavate_graph.copyGen()
Example_graph_A  = Example_graph.copyGen()
Excavate_graph.print_graph()
Example_graph.print_graph()

""" Test Clone"""
print("\n \t TEST Clone \n")
print('num_elements in excavate Before Clone Example:')
print(len(Excavate_graph.elements))
print('num_edges in excavate Before Clone Example:')
print(len(Excavate_graph.edges))
print("\n")	

excavate_clone = Excavate_graph.copyGen()

print('num_elements in excavate After Clone Example:')
print(len(excavate_clone.elements))
print('num_edges in excavate After Clone Example:')
print(len(excavate_clone.edges))
print("\n")	

print('rGetDescendantEdges test real vs clone edges \n')

print(len(Excavate_graph.rGetDescendantEdges(p1)))

#print(len(excavate_clone.rGetDescendantEdges(p1)))
p1_prime = excavate_clone.getElementById(p1.id)
print(len(excavate_clone.rGetDescendantEdges(p1_prime)))

""" Test Absolve"""
print("\n \t TEST Absolve \n")
print('num_elements in excavate Before Absolve Example:')
print(len(Excavate_graph.elements))
print('num_edges in excavate Before Absolve Example:')
print(len(Excavate_graph.edges))
print("\n")		

print('Absolves ->:',	 Excavate_graph.canAbsolve(Example_graph))

print("\n")
print('num_elements in excavate After Absolve Example:')
print(len(Excavate_graph.elements))
print('num_edges in excavate After Absolve Example:')
print(len(Excavate_graph.edges))

print("\n")
print('Absolves <-: ', Example_graph.canAbsolve(Excavate_graph))
""" Not True because, consistency 
"""

#print("Operators", example.isConsistent(excavate))

#print(item.isConsistent(place))
#consistent_merges = Example_graph.Merge(Excavate_graph)
#for i in consistent_merges:
#	print(i.id)



""" Test elementGraph """
print("\n \t TEST add elements and edges \n")
example_clone = Example_graph.copyGen()
print(example_clone.id)
print('num_elements:')
print(len(example_clone.elements))
print('num_edges:')
print(len(example_clone.edges))
example_clone.elements.add(example_e3)
example_clone.edges.add(example_edge5)
print('num_elements After add:')
print(len(example_clone.elements))
print('num_edges After add:')
print(len(example_clone.edges))

"""Test Swap"""
example_clone2 = Example_graph.copyGen()
print("\n \t TEST Swap \n")
print('num_elements in example Before swap:')
b = len(Example_graph.elements)
print(len(Example_graph.elements))
print('num_edges in example Before swap:')
print(len(Example_graph.edges))
Example_graph.swap(Example_graph.root, example_clone)
print('num_elements in example After swap:')
a = len(Example_graph.elements)
print(len(Example_graph.elements))
print('num_edges in example After swap:')
print(len(Example_graph.edges))

#Should only add one element...
if b != a - 1:
	print('elements did not add right')
	for E in Example_graph.elements:
		found = False
		for element in example_clone2.elements:
			if E.id == element.id:
				found = True
		if not found:
			print(E.id)
	print("\n")
	for E in Example_graph.elements:
		print(E.id)

		
		
"""Test getElementGraphFromElement """
print("\n \t TEST getElementGraphFromElement \n")

print(len(Excavate_graph.rGetDescendantConstraints(p1_prime)))

#p1_graph = Action.makeElementGraph(excavate_clone, p1)


print('num_descendant elements in excavate Before getElementGraphFromElement:')
print(len(Excavate_graph.rGetDescendants(p1)))
print('num descendant edges in excavate Before getElementGraphFromElement:')
print(len(Excavate_graph.rGetDescendantEdges(p1)))

print('\n Literal with type Condition \n')
print(p1.id)
print(p1.type)
sub_graph = excavate_clone.getElementGraphFromElement(p1_prime,eval(p1_prime.type))
print('\n Condition \n')
print(sub_graph.id)
print(sub_graph.type)
print(' \n')
print('num_elements in excavate Condition After getElementGraphFromElement:')
print(len(sub_graph.elements))
print('num_edges in subgraph Condition After getElementGraphFromElement:')
print(len(sub_graph.edges))
print('descendant edges in original')
print(len(excavate_clone.rGetDescendantEdges(p1_prime)))
print('descendant edges in subgraph')
print(len(sub_graph.rGetDescendantEdges(p1_prime)))

""" Testing absolve """
print("\n \t TEST rCreateConsistentEdgeGraph \n")

print(len(Example_graph_A.edges))
print(len(Excavate_graph_A.edges))
Completed = Excavate_graph_A.absolve(Example_graph_A, Remaining = copy.deepcopy(Example_graph_A.edges), Available = Excavate_graph_A.edges)
print('merges')
print(len(Completed))

attempt = Completed.pop()
#attempt.print_graph()
example_clone3 = Example_graph_A.copyGen()
print('before')
print(len(Example_graph_A.edges))
print(len(Excavate_graph_A.edges))
merges = Excavate_graph_A.possible_mergers(Example_graph_A)
print('after')
print(len(Example_graph_A.edges))
print(len(Excavate_graph_A.edges))
print('merges')
print(len(merges))
#merges.pop().print_graph()


""" Testing Combine """
print("\n \t TEST Combine \n")

lit_1 = 		Literal(id=311, 		type = 'Condition', 	name='has', 			truth = True)
lit_2 = 		Literal(id=911, 		type = 'Condition', 	name='has', 	num_args = 25,	truth = None)

lit_2.combine(lit_1).print_element()
print(lit_2.num_args)

lit_1 = 		Literal(id=311, 		type = 'Condition', 	name='has', 			truth = True)
lit_2 = 		Literal(id=911, 		type = 'Condition', 	name='has', 	num_args = 25,	truth = None)

lit_1.combine(lit_2).print_element()
print(lit_1.num_args)

""" TESTING SWAP AGAIN"""
#print(len(Example_graph_A.edges))
#print(len(Excavate_graph_A.edges))


excavate_clone3 = Excavate_graph_A.copyGen()

#swapee= merges.pop()


print("\n \t TEST Swap \n")
print('num_elements in example Before swap:')

print(len(example_clone3.elements))
print('num_edges in example Before swap:')
print(len(example_clone3.edges))
example_clone3.swap(example_clone3.root,merges.pop())
print('num_elements in example After swap:')

print(len(example_clone3.elements))
print('num_edges in example After swap:')
print(len(example_clone3.edges))

#example_clone3.print_graph()

""" Test copy_with_new_ids"""

print("\n \t TEST copy_with_new_ids \n")

#excavate_clone3.print_graph()
new_clone = excavate_clone3.copyWithNewIDs(1000)
#new_clone.print_graph()

""" NEXT TESTS"""
#NEED TO TEST EXAMPLE WITH MULTIPLE CONSISTENT MERGES
#TEST WHETHER MERGE IS CONSISTENT IS INTERNALLY CONSISTENT GIVEN CONSTRAINTS
#TEST COMBINE
