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
		(5.A) Determine if an operator graph has an effect which is consistent with precondition in flaw
		(5.B) Determine if an existing step has an effect which is consistent with precondition in flaw (if there is no ordering path from s_need to s_new)
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
			
		dummy_final = Operator(uuid.uuid1(1), type='Action', name='dummy final', is_orphan = False, executed = True, instantiated = True)
		graph.elements.add(dummy_final)
		for g in end_set:
			graph.edges.add(Edge(dummy_final, g, 'precond-of'))
			
		graph.OrderingGraph.addOrdering(dummy_start, dummy_final)
		
		graph.flaws.append(addOpenPreconditionFlaws(graph, dummy_final))
		
	def goalPlanning(self, graph, flaw):
		results = self.reuse(graph, flaw)
		results.update(self.newStep(graph, flaw))
		return results
		
	def newStep(self, graph, flaw):
		s_need, precondition = flaw.flaw
		Precondition = graph.getElementGraphFromElementId(precondition.id)
		results = set()
		
		#Then try new Step
		for op in self.op_graphs:
			for eff in op.getNeighborsByLabel(root, 'effect-of')
				Effect = op_graph.getElementGraphFromElementId(eff.id)
				if Effect.canAbsolve(Precondition):
					""" TODO: make easy instantiate operator graph as step, """
					
					
					step_op, nei = op.makeCopyFromId(start_from = 1,old_element_id = eff.id)
					#nei : new element id, to easily access element from graph
					
					Effect  = step_op.getElementGraphFromElementId(nei)
					Effect_absorbtions = Effect.getInstantiations(Precondition)
					#could be more than one way to unify effect with precondition
					new_step_prospects = set()
					for eff_abs in Effect_absorptions: 
						new_step_op = copy.deepcopy(step_op)
						new_step_op.mergeGraph(eff_abs)
						new_step_prospects.add(new_step_op)
						
						#new step instance (from operator) is ready to be included in graph_copy
						graph_copy = copy.deepcopy(graph)
						
						
					"""
						Challenge: 
							effect absolves the precondition (i.e., all possible unifications)
							merge/swap precondition with effect, repoint all outoing/incoming edges
								Make sure to indicate which elements are replaced
							Add remaining elements and edges of new_step_op
							
						Then, remember to add causal link and ordering edges
							also add ordering edges from dummy source and to dummy sink
					"""
					
					
					for element in new_step_op.elements:
						graph_copy.elements.add(element)
					# for edge in new_steop_op.edges:
						# if edge.sink is effect:
							# graph_copy.edges.add(Edge(edge.source, precondition, edge.label))
						# elif edge.source is effect:
							# graph_copy.edges.add(Edge(precondition, edge.sink, edge.label))
						# else:
							# graph_copy.edges.add(edge)
							
					
					graph_copy.edges.add(CausalLink(new_step_op, s_need, precondition))
					#graph_copy.OrderingGraph.addEdge(new_step_op, dumm)
					fringe.add(new_step_op)
		
	def reuse(self, graph, flaw):
		s_need, pre = flaw.flaw
		for step in graph.Steps:
			if graph.OrderingGraph.isPath()
	
	def selectFlaw(self, graph)
		return graph.flaws.pop()
		
	def rPOCL(self, graph)
		"""
			Recursively, given graph, for each flaw, for each way to resolve flaw, create new graphs and rPOCL on it
		"""
		
		#BASE CASES
		if not graph.isInternallyConsistent:
			return
		if len(graph.flaws) == 0:
			return graph
			
		#INDUCTION
		flaw = self.selectFlaw(graph)
		if flaw.name = 'opf':
			graphs = goalPlanning(self, graph)
		if flaw.name = 'tclf':
			pass
		
		for g in graphs:
			self.rPOCL(g)
		