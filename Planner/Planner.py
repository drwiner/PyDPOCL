from Flaws import *

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

class PlanSpacePlanner:

	graphs = {} #graphs, will be limited to fringe

	def __init__(self, start_set, end_set, op_graphs, objects):
		#Assumes these parameters are already read from file
		
		self.op_graphs = opgraphs
		
		init_graph = PlanElementGraph(uuid.uuid1(0)):
		
		#create special dummy step for init_graph and add to graphs {}		
		self.setup(init_graph, start_set, end_set)
		graphs.add(init_graph)
	
	def setup(self, graph, start_set, end_set):
		"""
			Create step typed element DI, with effect edges to each condition of start_set
			Create step typed element DG, with precondition edges to each condition of end_set
			Add ordering from DI to DG
		"""
		
		dummy_start = Operator(uuid.uuid1(1), type='Action', name='dummy start', is_orphan = False, executed = True, instantiated = True)
		graph.elements.add(dummy_start)
		for i in start_set:
			graph.edges.add(Edge(dummy_start, i, 'effect-of'))
		graph.initial_dummy_step = dummy_start
		
		dummy_final = Operator(uuid.uuid1(1), type='Action', name='dummy final', is_orphan = False, executed = True, instantiated = True)
		graph.elements.add(dummy_final)
		graph.final_dummy_step = dummy_final
		for g in end_set:
			graph.edges.add(Edge(dummy_final, g, 'precond-of'))
			
		graph.OrderingGraph.addOrdering(dummy_start, dummy_final)
		
		graph.flaws.append(addOpenPreconditionFlaws(graph, dummy_final))
		
	def goalPlanning(self, graph, flaw):
		results = self.reuse(graph, flaw)
		results.update(self.newStep(graph, flaw))
		return results
		
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
		Precondition = graph.getElementGraphFromElementId(precondition.id)
		results = set()
		
		#Then try new Step
		for op in self.op_graphs:
			for eff in op.getNeighborsByLabel(root, 'effect-of')
				Effect = op_graph.getElementGraphFromElementId(eff.id)
				if Effect.canAbsolve(Precondition):
					step_op, nei = op.makeCopyFromId(start_from = 1,old_element_id = eff.id)
					#nei : new element id, to easily access element from graph
					
					Effect  = step_op.getElementGraphFromElementId(nei)
					Effect_absorbtions = Effect.getInstantiations(Precondition)
					#could be more than one way to unify effect with precondition

					for eff_abs in Effect_absorptions: 
						graph_copy = copy.deepcopy(graph)
						graph_copy.mergeGraph(eff_abs) 
						
						new_step_op = copy.deepcopy(step_op)
						graph_copy.mergeGraph(new_step_op)
						self.addStep(graph_copy, new_step_op.root.id, s_need.id, eff_abs.id) #adds causal link and ordering constraints
						results.add(graph_copy)
						#add graph to children
		return results
	
		
	def reuse(self, graph, flaw):
		"""
			returns set of graphs which resolve flaw by reusing a step in the plan, if possible
			iterates through existing steps, and effects of those steps, and asks if any can absolve the precondition of the flaw
		"""
		s_need, pre = flaw.flaw
		Precondition = graph.getElementGraphFromElementId(pre.id)
		results = set()
		for step in graph.Steps:
			if graph.OrderingGraph.isPath(s_need, step):
				#step cannot be ordered before s_need
				continue
			for eff in graph.getNeighborsByLabel(step, 'effect-of'):
				Effect = graph.getElementGraphFromElementId(eff.id)
				if Effect.canAbsolve(Precondition):
					Effect_absorbtions = Effect.getInstantiations(Precondition)
					for eff_abs in Effect_absorptions: 
						"""	for each effect which can absolve the precondition, 
							and each possible way to unify the effect and precondition,
								1) Create a new child graph.
								2) Replace effect with eff_abs, which is unified with the precondition
								3) "Redirect" all edges going to precondition, to go to effect instead
						"""
						#1 Create new child graph
						graph_copy = copy.deepcopy(graph)
						#2 Replace effect with eff_abs, which is unified with the precondition
						graph_copy.mergeGraph(eff_abs)
						
						#3) "Redirect Task"": find all edges where the sink has a replaced_id in replace_ids

						replace_ids = {element.id for element in eff_abs}
						#All Edges which have sink whose id was not a replace_id nor whose id = its own replace id
						#May need to get element subgraph from step if step is not type Action
						incoming = {edge for edge in graph_copy.edges \
							if edge.sink.replaced_id in replace_ids \
							and not edge.sink.replaced_id == element.id\
							and not edge.source.id in replace_ids}					
						for edge in incoming:
							new_sink = graph_copy.getElementByReplacedId(edge.sink.id)
							graph_copy.elements.remove(edge.sink)
							graph_copy.replaceWith(edge.sink,new_sink)
							
						self.addStep(graph_copy, s_need.id, step.root.id, eff_abs.id)
						results.add(graph_copy)
		return results
	
		
	def addStep(self, graph, s_add_id, s_need_id, condition_id, new=None):
		"""
			when a step is added/reused, 
			add causal link and ordering edges (including to dummy steps)
			If step is new, add open precondition flaws for each precondition
				NOTE!	Open precondition flaws ought to reference the precondition "id", 
							and not contain itself a data structure
						Because, what if properties of the precondition are refined? 
		"""
		if new == None:
			new = False
		graph.OrderingGraph.addEdge(graph.initial_dummy_step.id, s_add_id)
		graph.OrderingGraph.addEdge(s_add_id, graph.final_dummy_step.id)
		graph.OrderingGraph.addEdge(graph.initial_dummy_step.id, s_need_id)
		graph.OrderingGraph.addEdge(s_need_id, graph.final_dummy_step.id)
		graph.OrderingGraph.addEdge(s_add_id,s_need_id)
		graph.CausalLinkGraph.addEdge(s_add_id, s_need_id, condition_id)
		if new:
			new_flaws = addOpenPreconditionFlaws(graph, graph.getElementById(s_add_id))
			graph.flaws.update(new_flaws)
				
		return graph
		
	def resolveThreatenedCausalLinkFlaw(graph, flaw):
		"""
			Promotion: Add ordering from sink to threat, and check if cycle
			Demotion: Add ordering from threat to source, and check if cycle
			Restriction: Add non-codesignation constraints to prevent unification of effect with condition.id of causal link
		"""
		results = set()
		threat, effect, causal_link = flaw.flaw
		
		#Promotion
		promotion = copy.deepcopy(graph)
		promotion.OrderinGraph.addEdge(causal_link.sink, threat)
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
		condition = graph.getElementById(causal_link.condition_id)
		restrictions = graph.addNonCodesignationConstraints(effect, condition)
			#TODO: method addNonCodesignationConstraints
		results.update(restrictions)
		return results
		
	def rPOCL(self, graph)
		"""
			Recursively, given graph, 
				for each flaw, 
				for each way to resolve flaw, 
				create new graphs and rPOCL on it
		"""
		
		#BASE CASES
		if not graph.isInternallyConsistent:
			return None
		if len(graph.flaws) == 0:
			return graph
			
		#INDUCTION
		flaw = graph.flaws.pop()
		if flaw.name = 'opf':
			results = goalPlanning(self, graph)
			for result in results:
				#Detect Threatened causal link flaws here.
				new_flaws = detectThreatenedCausalLinks(result)
				result.flaws.update(new_flaws)
				
		if flaw.name = 'tclf':
			"""
				Promotion: Add ordering from sink to threat, and check if cycle
				Demotion: Add ordering from threat to source, and check if cycle
				Restriction: Add non-codesignation constraints to prevent unification of effect with condition.id of causal link
			"""
			threat, effect, causal_link = flaw.flaw
			#Promotion
			#Demotion
			#Restriction
				
			pass
		
		for g in results:
			result = self.rPOCL(g) 
			if not result is None:
				return result
				
		print('no solutions found?')
		return None