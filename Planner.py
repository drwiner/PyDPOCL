from Flaws import *
#from pddlToGraphs import *


"""
	Algorithm for Plan-Space search of Story Plan
"""

"""
	(1) Read PDDL Domain and Problem (in another file, make test case)
	(2) Create dummy initial and goal steps
	(3) Create open precondition flaws for each element in goal
	(4) Select Flaw based on heuristic
	(5) Support the following operations pertaining to resolving open precondition flaws:
		(5.A) Determine if an operator graph has an effect which is consistent/can-absolve with precondition in flaw
		(5.B) Determine if an existing step has an effect which is consistent/can-absolve with precondition in flaw (if there is no ordering path from s_need to s_new)
	(6) Support the following operations pertaining to resolving a threatened causal link flaw:
		(6.A) Trivially, adding ordering edges
		(6.B) Not as trivially, add bindings to prevent effect from co-designating with precondition.
					Transform effect in E1 (condition) and preconditino in P1 (condition)
							[Quick reference: 	arguments are named only if they refer to constants
												arguments which are co-designated have the same ID
												TODO: for each argument, track a set of IDs for non-designations]
					For each matching outgoing-labeled edge sinks of E1 and P1, call them eA and pA, 
							skip if they are codesignated or assigned the same name
							otherwise, create deep copy of graph and add a non-codesignation relation
							search through all arguments to create graphs which prevent unification in every possible way
	(7) Detect Threatened Causal Link Flaws
	(8) Recursive Invocation (but, log status of plan first)
"""
import collections

class PlanSpacePlanner:

	def __init__(self, op_graphs, objects, init_action, goal_action):
		#Assumes these parameters are already read from file
		
		self.op_graphs = op_graphs
		self.objects = objects
		
		
		init_graph = PlanElementGraph(uuid.uuid1(0), Elements = objects | init_action.elements | goal_action.elements, Edges = init_action.edges | goal_action.edges)
		init_graph.initial_dummy_step = init_action.root
		init_graph.final_dummy_step = goal_action.root
		
		#create special dummy step for init_graph and add to graphs {}		
		self.setup(init_graph, init_action, goal_action)
		self._frontier = [init_graph]
		
	def __len__(self):
		return len(self._frontier)
	
	def __getitem__(self, position):
		return self._frontier[position]
		
	def __setitem__(self, graph, position):
		self._frontier[position] = graph
	
	def setup(self, graph, start_action, end_action):
		"""
			Create step typed element DI, with effect edges to each condition of start_set
			Create step typed element DG, with precondition edges to each condition of end_set
			Add ordering from DI to DG
		"""
		
		dummy_start = start_action.root
		dummy_final = end_action.root
			
		graph.OrderingGraph.addOrdering(dummy_start, dummy_final)
		
		#Add initial Open precondition flaws for dummy step
		graph.flaws += (Flaw((dummy_final, prec), 'opf') for prec in graph.getNeighborsByLabel(dummy_final, 'precond-of'))
		
		
	def newStep(self, graph, flaw):
		"""
			iterates through all operators, instantiating a step with effect that can absolve precondition of step in flaw
			returns set of graphs which resolve the flaw
			
			method details:
				"get instantiations": given two graphs, returns a set of unifications by accounting-for/absolving all edges in second with edges in first
				"mergeGraph": 	given two graphs where the second had replaced some of the elements of the first,
								the first graph merges the second one back in, tracking the elements it replaced
		"""
		
		s_need, precondition = flaw.flaw
		Precondition = graph.getElementGraphFromElementID(precondition.ID, Condition)
		results = set()
		
		#Then try new Step
		for op in self.op_graphs:
			print(op)
			for eff in op.getNeighborsByLabel(op.root, 'effect-of'):
				print(eff)
				#Condition graph of operator
				Effect = op.getElementGraphFromElementID(eff.ID, Condition)
				
				#Can all edges in Precondition be matched to a consistent edge in Effect, without replacement
				if Effect.canAbsolve(Precondition):
					print('legal eff')
					
					#nei : new element id, to easily access element from graph
					step_op, nei = op.makeCopyFromID(start_from = 1,old_element_id = eff.ID)
					
					#Condition graph of copied operator for Effect
					Effect  = step_op.getElementGraphFromElementID(nei, Condition)
					
					#could be more than one way to unify effect with precondition
					#Effect_absorbtions' graphs' elements' replaced_ids assigned Precondition's ids
					Effect_absorbtions = Effect.getInstantiations(Precondition)
			
					for eff_abs in Effect_absorbtions: 
						print('effect absorbs flaw')
						print(eff_abs)
						graph_copy = copy.deepcopy(graph)
						
						#First, find elements of Precondition (in graph_copy) and mergeFrom elements of eff_abs
						#Also, add elements in eff_abs not present in Precondition
						graph_copy.mergeGraph(eff_abs)
						
						new_step_op = copy.deepcopy(step_op)
						graph_elms = {elm for elm in graph_copy.elements if hasattr(elm, 'replaced_ID')}
						
						for step_elm in new_step_op.elements:
							for graph_elm in graph_elms:
								if graph_elm.replaced_ID == step_elm.ID:
									step_elm.replaced_ID = graph_elm.ID
									graph_elms.remove(graph_elm)
									break
						
						#Second, find elements of eff_abs in graph_copy, which have ids from Effect 
						#		and merge elements of new_step's Effect (which have same ids has Effect)
						#Also, add elements in new_step_op which are not Effect
						graph_copy.mergeGraph(new_step_op)
						
						self.addStep(graph_copy, new_step_op.root, s_need, eff_abs.root, new = True) #adds causal link and ordering constraints
						results.add(graph_copy)
						#add graph to children
		return results
	
		
	def reuse(self, graph, flaw):
		"""
			returns set of graphs which resolve flaw by reusing a step in the plan, if possible
			iterates through existing steps, and effects of those steps, and asks if any can absolve the precondition of the flaw
		"""
		s_need, pre = flaw.flaw
		Precondition = graph.getElementGraphFromElementID(pre.ID,Condition)
		results = set()
		for step in graph.Steps: 
			print(step)
			if step == s_need:
				continue
			if graph.OrderingGraph.isPath(s_need, step):
				#step cannot be ordered before s_need
				continue
			print('legal step')
			for eff in graph.getNeighborsByLabel(step, 'effect-of'):
				print(eff)
				Effect = graph.getElementGraphFromElementID(eff.ID, Condition)
				if Effect.canAbsolve(Precondition):
					print('legal eff')
					Effect_absorbtions = Effect.getInstantiations(Precondition)
					for eff_abs in Effect_absorbtions: 
						print('effect absorbs flaw')
						print(eff_abs)
						"""	for each effect which can absolve the precondition, 
							and each possible way to unify the effect and precondition,
								1) Create a new child graph.
								2) Replace effect with eff_abs, which is unified with the precondition
								3) "Redirect" all edges going to precondition, to go to effect instead
						"""
						#1 Create new child graph
						graph_copy = copy.deepcopy(graph)
						#2 Replace effect with eff_abs, which is unified with the precondition
						graph_copy.mergeGraph(eff_abs, no_add = True)
						
						#3) "Redirect Task"": find all edges where the sink has a replaced_id in replace_ids

						precondition_IDs = {element.ID for element in Precondition.elements}
						eff_abs_IDs = {elm.ID for elm in eff_abs.elements}
						#Get elm IDS for elms which were in Precondition...

						''' incoming is all edges in graph_copy with sink in Precondition'''
						incoming = {edge for edge in graph_copy.edges if hasattr(edge.sink, 'replaced_ID')}
						incoming = {edge for edge in incoming if edge.sink.ID in precondition_IDs}
						''' minus edges which have a source in Precondition'''
						rmv = {edge for edge in incoming if hasattr(edge.source, 'replaced_ID')}
						rmv = {edge for edge in rmv if edge.source.replaced_ID in precondition_IDs}
						incoming -= rmv
						''' leaving just those edges which have sinks in Precondition but not sources in Precondition'''
						rmv = {edge for edge in incoming if edge.sink in eff_abs_IDs}
						''' minus edges whose sinks carried over with eff_abs '''

						
						#cddts = {edge for edge in graph_copy.edges if 'replaced_ID' in edge.sink.__dict__.keys() and not edge.sink.replaced_ID == edge.sink.ID}
						''' for each edge in graphy_copy with sink in Precondition,
								if there exists an elm in eff_abs s.t. elm.replaced_ID == edge.sink.ID
									if elm.ID != elm.replaced_ID:
										then replace edge.sink with elm
						'''
						#incoming = {edge for edge in graph_copy.edges if edge.sink.replaced_ID in replace_ids and not edge.sink.replaced_ID == edge.sink.ID and not edge.source.ID in replace_ids}	
						uniqueSinks = {edge.sink for edge in incoming}

						for snk in uniqueSinks:
							new_sink = eff_abs.getElementByReplacedId(snk.ID)
							if new_sink is None:
								print(eff_abs)
								print(snk.replaced_ID)
							graph_copy.replaceWith(snk,new_sink)
							
						self.addStep(graph_copy, step, s_need, eff_abs.root, new = False)
						results.add(graph_copy)
		return results
	
		
	def addStep(self, graph, s_add, s_need, condition, new=None):
		"""
			when a step is added/reused, 
			add causal link and ordering edges (including to dummy steps)
			If step is new, add open precondition flaws for each precondition
		"""
		if new == None:
			new = False
			
		if not s_add == graph.initial_dummy_step:
			graph.OrderingGraph.addEdge(graph.initial_dummy_step, s_add)
			graph.OrderingGraph.addEdge(graph.initial_dummy_step, s_need)
			
		if not s_need == graph.final_dummy_step:
			graph.OrderingGraph.addEdge(s_add, graph.final_dummy_step)
			graph.OrderingGraph.addEdge(s_need, graph.final_dummy_step)
			
		#Always add this ordering
		graph.OrderingGraph.addEdge(s_add,s_need)
		graph.CausalLinkGraph.addEdge(s_add, s_need, condition)

		if new:
			prc_edges = graph.getIncidentEdgesByLabel(s_add, 'precond-of')
			#preconditions = graph.getNeighborsByLabel(s_add, 'precond-of')
			equalNames = {'equals', 'equal', '='}
			noncodesg = {prec for prec in prc_edges if prec.sink.name in equalNames and not prec.sink.truth}
			for prec in noncodesg:
				item1Edge, item2Edge = tuple(graph.getIncidentEdges(prec.sink))
				#item1, item2 = tuple(graph.getNeighbors(prec.sink))

				#This constraint/restriction prevents item1Edge.sink and item2Edge.sink from becoming a legal merge
				graph.constraints.add(Edge(item1Edge.source, item2Edge.sink, item1Edge.label))
				
				#Remove outgoing edges and '=' Literal element
				graph.edges.remove(item1Edge)
				graph.edges.remove(item2Edge)
				graph.elements.remove(prec.sink)
				
			#Remove equality precondition edges
			graph.edges -= noncodesg

			graph.flaws += (Flaw((s_add, prec.sink), 'opf') for prec in prc_edges if not prec in noncodesg)
				
		#Good time as ever to updatePlan
		graph.updatePlan()
		return graph
		
	def resolveThreatenedCausalLinkFlaw(self, graph, flaw):
		"""
			Promotion: Add ordering from sink to threat, and check if cycle
			Demotion: Add ordering from threat to source, and check if cycle
			Restriction: Add non-codesignation constraints to prevent unification of effect with condition of causal link
		"""
		results = set()
		threat, effect, causal_link = flaw.flaw
		
		#Promotion
		promotion = copy.deepcopy(graph)
		promotion.OrderingGraph.addEdge(causal_link.sink, threat)
		if promotion.OrderingGraph.isInternallyConsistent():
			results.add(promotion)
			
		#Demotion
		demotion = copy.deepcopy(graph)
		demotion.OrderingGraph.addEdge(threat, causal_link.source)
		if demotion.OrderingGraph.isInternallyConsistent():
			results.add(demotion)
			
		#Restriction
		"""
			1) find literal of causal link based on causal_link.id, to compare to ?effect
			2) For each consistent but not equivalent edge, 
				for each non-equivalent attribute,
					create new child where child has a "non-codesignation constraint" (keep a list in the plan of consistent neqs)
					Can this be represented as a constraint so that if its detected, we can fail?
					This is something that requires elaborating on constraints
		"""
		restriction = copy.deepcopy(graph)
		restriction.addNonCodesignationConstraints(effect, causal_link.label)
			#TODO: method addNonCodesignationConstraints
			#Whenever a possible merge, disclude candidates if non-codesignation constraint.
		results.add(restriction)
		return results
		

	def rPOCL(self, graph):
		"""
			Recursively, given graph, 
				for each flaw, 
				for each way to resolve flaw, 
				create new graphs and rPOCL on it
		"""
		print(graph)
		print('num flaws: {} '.format(len(graph.flaws)))
		#BASE CASES
		if not graph.isInternallyConsistent():
			return None
		if len(graph.flaws) == 0:
			return graph
			
		#INDUCTION
		#flaw = graph.flaws.pop() 
		for flaw in graph.flaws:
		
			if flaw.name == 'opf':
				print('opf')
				#s_need, pre = flaw.flaw
				#print(graph.getElementGraphFromElement(s_need,Action))
				#print(graph.getElementGraphFromElement(pre,Condition))
				results = self.reuse(graph, flaw)
				print('reuse results: {} '.format(len(results)))
				results.update(self.newStep(graph, flaw))
				print('newStep results: {} '.format(len(results)))
				if len(results) == 0:
					print('could not resolve opf')
					return None
				
			if flaw.name == 'tclf':
				results = self.resolveThreatenedCausalLinkFlaw(graph, flaw)
				
			for result in results:
				new_flaws = detectThreatenedCausalLinks(result)
				result.flaws += new_flaws
				print('detected tclfs: {} '.format(len(new_flaws)))

			#self._frontier += results
			
			#replace this with choosing highest ranked graph
			#new_results = set()
			for g in results:
				#print('rPOCLing')
				#print(g)
				#result = self._frontier.pop()
				g.flaws.remove(flaw)
				result = self.rPOCL(g)
				#print(result)
				if not result is None:
					#new_results.add(result)
					return result
			results = set()
		#for nr in new_results:
			
		
		print('no solutions found')
		print('for debugging: \n')
		for g in results:
			print(g)
		print('end debugging \n')
		return None
		

import sys	
if __name__ ==  '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]		
	else:
		domain_file = 'domains/mini-indy-domain.pddl'
		problem_file = 'domains/mini-indy-problem.pddl'
	
	operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
	planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
	graph = planner[0]
	result = planner.rPOCL(graph)
	print('\n\n\n')
	print(result)
	