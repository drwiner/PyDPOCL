#from Flaws import *
from pddlToGraphs import *



"""
	Algorithm for Plan-Graph-Space search of Story Plan
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

		for op in self.op_graphs:
			for eff in op.getNeighborsByLabel(op.root, 'effect-of'):

				if not eff.isConsistent(precondition):
					continue

				Effect = op.getElementGraphFromElementID(eff.ID, Condition)
				
				#Can all edges in Precondition be matched to a consistent edge in Effect, without replacement
				if Effect.canAbsolve(Precondition):
					
					#nei : new element id, to easily access element from graph
					step_op, nei = op.makeCopyFromID(start_from = 1,old_element_id = eff.ID)
					
					#Condition graph of copied operator for Effect
					Effect  = step_op.getElementGraphFromElementID(nei, Condition)
					
					#could be more than one way to unify effect with precondition
					#Effect_absorbtions' graphs' elements' replaced_ids assigned Precondition's ids
					Effect_absorbtions = Effect.getInstantiations(Precondition)
			
					for eff_abs in Effect_absorbtions:
						graph_copy = copy.deepcopy(graph)
						new_step_op = copy.deepcopy(step_op)

						#For each element 'e_a' in eff_abs which replaced an element 'e_p' in Precondition,
							# e_p.merge(e_a)
						#For each element 'e_a' introduced by eff_abs,
							# graph_copy.add(e_a)
						#For each edge (a --label --> b) in eff_abs, if not edge (p --label--> d) in Precondition
							# such that a.replaced_ID = p.ID and b.replaced_ID = d.ID, then graph_copy.add(edge)
						graph_copy.mergeGraph(eff_abs)

						#For each elm 'e_s' in new_step_op not in eff_abs,
							# graph_copy.add(e_s)
						untouched_step_elms = {elm for elm in new_step_op.elements if not elm.ID in {e.ID for e in
																						 eff_abs.elements}}
						for elm in new_step_op.elements:
							if elm in untouched_step_elms:
								graph_copy.elements.add(elm)

						# For each edge 'e1 --label--> e2 in new_step_op such that e1 not in eff_abs,
							# if exists some e_p s.t. e_p.merge(sink), replace edge sink
							# graph_copy.add(edge)
						for edge in new_step_op.edges:
							if edge.source in untouched_step_elms:
								if not edge.sink in untouched_step_elms:
									e_abs = eff_abs.getElementById(edge.sink.ID)
									edge.sink = graph_copy.getElementById(e_abs.replaced_ID)
								graph_copy.edges.add(edge)

						# adds causal link and ordering constraints
						condition = graph_copy.getElementById(Precondition.root.ID)
						self.addStep(graph_copy, new_step_op.root, s_need, condition, new = True)

						# add graph to children
						results.add((graph_copy, 'newStep'))

		return results

	def operateIfConsistent(graph, flaw, operation):
		s_need, pre = flaw.flaw
		Precondition = graph.getElementGraphFromElementID(pre.ID)
		for eff in graph.flawLib[flaw]:
			Effect = graph.getElementGraphFromElementID(eff.ID)
			if Effect.canAbsolve(Precondition):

		#suggestions = graph.flawLib[flaw]
		Precondition = graph.getElementGraphFromElementID(pre.ID)
		for edge in graph.edges:
			if edge.label != 'effect-of':
				continue
			eff = edge.sink
			step = edge.source
			if s_need == step:
				continue
			if graph.OrderingGraph.isPath(step, s_need):
				continue
			if not eff.isConsistent(pre):
				continue
			Effect = graph.getElementGraphFromElementID(eff.ID)
			if Effect.canAbsolve(Precondition):
				operation(eff)

	def getOrbs(self, graph, flaw, Precondition):
		eff_orbs = collections.defaultdict(set)
		num_orbs = collections.defaultdict(int)

		for eff in graph.flawLib[flaw]:
			Effect = graph.getElementGraphFromElementID(eff.ID)
			if Effect.canAbsolve(Precondition):
				# returns all possible ways to unify Effect with Precondition
				orbs = Effect.getInstantiations(Precondition)
				eff_orbs[eff].update(orbs)
				num_orbs[eff] += len(orbs)

		return sorted(num_orbs.keys(), key=num_orbs.values())
		
	def reuse(self, graph, flaw, cndt, id_match_set, orb):
		"""
			returns set of graphs which resolve flaw by reusing a step in the plan, if possible
			iterates through existing steps, and effects of those steps, and asks if any can absolve the precondition of the flaw
		"""
		#absorb_set = set()
		s_need, pre = flaw.flaw

		#rank effects by "effort" of resolving action (Most-Work-First)
		graph_copy = copy.deepcopy(graph)

		# 2 Replace effect with eff_abs, which is unified with the precondition
		graph_copy.mergeGraph(cndt, no_add=True)

		# 3) "Redirect Task""
		# Get elm for elms which were in eff_abs but not in precondition (were replaced)
		new_snk_cddts = {elm for elm in cndt.elements if not elm.ID in id_match_set}
		snk_swap_dict = {graph_copy.getElementById(elm.replaced_ID): graph_copy.getElementById(elm.ID) for elm in
						 new_snk_cddts}
		for old, new in snk_swap_dict.items():
			graph_copy.replaceWith(old, new)

		# adds causal link and ordering constraints
		condition = graph_copy.getElementById(cndt.root.ID)
		self.addStep(graph_copy, step, s_need, condition, new=False)

		return (graph_copy, 'reuse')


	# def oldReuse(self, graph, flaw):
	# 	results = set()
	# 	s_need, pre = flaw.flaw
	# 	Precondition = graph.getElementGraphFromElementID(pre.ID,Condition)
	# 	results = set()
	# 	for step in graph.Steps:
	#
	# 		if step == s_need:
	# 			continue
	# 		if graph.OrderingGraph.isPath(s_need, step):
	# 			#step cannot be ordered before s_need
	# 			continue
	#
	# 		for eff in graph.getNeighborsByLabel(step, 'effect-of'):
	#
	# 			if not eff.isConsistent(pre):
	# 				continue
	#
	# 			Effect = graph.getElementGraphFromElementID(eff.ID, Condition)
	#
	# 			if Effect.canAbsolve(Precondition):
	#
	# 				Effect_absorbtions = Effect.getInstantiations(Precondition)
	#
	# 				for eff_abs in Effect_absorbtions:
	# 					#1 Create new child graph
	# 					graph_copy = copy.deepcopy(graph)
	#
	# 					#2 Replace effect with eff_abs, which is unified with the precondition
	# 					graph_copy.mergeGraph(eff_abs, no_add = True)
	#
	# 					#3) "Redirect Task""
	#
	# 					# Get elm for elms which were in eff_abs but not in precondition (were replaced)
	# 					precondition_IDs = {element.ID for element in Precondition.elements}
	# 					new_snk_cddts = {elm for elm in eff_abs.elements if not elm.ID in precondition_IDs}
	# 					snk_swap_dict = {graph_copy.getElementById(elm.replaced_ID):graph_copy.getElementById(elm.ID) for elm in new_snk_cddts}
	# 					for old, new in snk_swap_dict.items():
	# 						graph_copy.replaceWith(old, new)
	#
	# 					# adds causal link and ordering constraints
	# 					condition = graph_copy.getElementById(eff_abs.root.ID)
	# 					self.addStep(graph_copy, step, s_need, condition, new = False)
	#
	# 					# add graph to children
	# 					results.add((graph_copy,'reuse'))
	# 	return results
	
		
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
				# item1, item2 = tuple(graph.getNeighbors(prec.sink))
				item1Edge, item2Edge = tuple(graph.getIncidentEdges(prec.sink))

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
			results.add((promotion, 'promotion'))
			
		#Demotion
		demotion = copy.deepcopy(graph)
		demotion.OrderingGraph.addEdge(threat, causal_link.source)
		if demotion.OrderingGraph.isInternallyConsistent():
			results.add((demotion, 'demotion'))

		#Restriction
		restriction = copy.deepcopy(graph)
		restriction.addNonCodesignationConstraints(effect, causal_link.label)
		results.add((restriction, 'restriction'))

		return results

	def rankFlaws(self, graph):
		tclfs = [flaw.flaw for flaw in graph.flaws if flaw.name == 'tclf']
		opfs = [flaw.flaw for flaw in graph.flaws if flaw.name == 'opf']
		#local open conditions--> belongs to most recently added action that still has open conditions
			#let open conditions form a LIFO stack.
		#unsafe open conditions --> there exists a step 's' with effect 'not (open condition)' and there is no
			# ordering 's_need' < 's'
		'''
			Implementation of MW-Loc-Conf = {n,s}LR / {u}MW_add / {l}MW_add (Younes & Simmons, 2003, VHPOP, JAIR)
			1, resolve all tclfs
			2, find all unsafe open conditions and rank them by most-work-additive heuristic
			3, find all local open conditions sorted and rank them by most-work-additive heuristic
		'''

		orderedOPFs = []
		for opf in opfs:
			s_need, pre = opf
			Precondition = graph.getElementGraphFromElementID(pre.ID, Condition)
			for step in graph.Steps:

				#exclude steps ordered after flaw.s_need
				if graph.OrderingGraph.isPath(s_need, step):
					continue

				for eff in graph.getNeighborsByLabel(step, 'effect-of'):
					if not eff.isConsistent(pre):
						continue

					Effect = graph.getElementGraphFromElementID(eff.ID, Condition)
					if not Effect.canAbsolve(Precondition):
						continue


	def PyPOCL(self, graph):
		pass
		#(1) select Flaw
		#(2) select plan


	def rPOCL(self, graph, seeBranches = None, fl = None):
		"""
			Recursively, given graph, 
				for each flaw, 
				for each way to resolve flaw, 
				create new graphs and rPOCL on it
		"""

		if seeBranches == True:
			print(graph)

		if not fl is None:
			fl.write('\n\n\n\n\n\n\n\n')
			fl.write(str(graph))
			numOPFs = len([1 for flaw in graph.flaws if flaw.name == 'opf'])
			numTCLFs = len([1 for flaw in graph.flaws if flaw.name == 'tclf'])
			fl.write('\nnum_flaws: {}'.format(len(graph.flaws)))
			fl.write('\nnum_OPFs: {}'.format(numOPFs))
			fl.write('\nnum_TCLFs: {}'.format(numTCLFs))
			for i, flaw in enumerate(graph.flaws):
				fl.write('\nflaw-{}: {}'.format(i, flaw))
			fl.write('\ninternally consistent: {}'.format(graph.isInternallyConsistent()))

		#print('num flaws: {} '.format(len(graph.flaws)))

		#BASE CASES
		if not graph.isInternallyConsistent():
			#print('branch terminated')
			return None

		if len(graph.flaws) == 0:
			#print('solution selected')
			return graph

		tclfs = [flaw for flaw in graph.flaws if flaw.name == 'tclf']
		opfs = [flaw for flaw in graph.flaws if flaw.name == 'opf']

		'''
		s_need, pre = flaw.flaw
		Precondition = graph.getElementGraphFromElementID(pre.ID)

		#Get all refinements
		cndts = self.getOrbs(graph, flaw, Precondition)

		for cndt in cndts:
			reuse(
		'''

		#INDUCTION
		for flaw in graph.flaws:

		
			if flaw.name == 'opf':
				results = self.reuse(graph, flaw)
				results.update(self.newStep(graph, flaw))
				if len(results) == 0:
					#print('could not resolve opf')
					return None
				
			if flaw.name == 'tclf':
				results = self.resolveThreatenedCausalLinkFlaw(graph, flaw)
				
			for result, res in results:
				new_flaws = result.detectThreatenedCausalLinks()
				result.flaws += new_flaws

			if not fl is None:
				fl.write('\n flaw: {}'.format(flaw))
				for g, res in results:
					fl.write('\n\n outcome via {}:\n {}'.format(res, g))
			for g, _ in results:
				g.flaws.remove(flaw)
				result = self.rPOCL(g,seeBranches, fl)
				if not result is None:
					return result
		
		print('branch terminated')
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

	f = open('workfile', 'w')
	operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
	planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
	graph = planner[0]
	result = planner.rPOCL(graph, seeBranches = None, fl = f)
	#print('\n\n\n')
	print(result)
	