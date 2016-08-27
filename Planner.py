#from Flaws import *
from pddlToGraphs import *
import collections
from heapq import heappush, heappop

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

class Frontier:
	def __init__(self):
		self._frontier = []

	def __len__(self):
		return len(self._frontier)

	def pop(self):
		return heappop(self._frontier)

	def insert(self, plan):
		heappush(self._frontier, plan)

	def __getitem__(self, position):
		return self._frontier[position]

	def extend(self, itera):
		for item in itera:
			self.insert(item)



class PlanSpacePlanner:

	def __init__(self, op_graphs, objects, init_action, goal_action):
		#Assumes these parameters are already read from file

		self.op_graphs = op_graphs
		self.objects = objects

		init_graph = PlanElementGraph(uuid.uuid1(0), Elements = objects | init_action.elements |
																goal_action.elements, Edges = init_action.edges |
																							  goal_action.edges)
		init_graph.initial_dummy_step = init_action.root
		init_graph.final_dummy_step = goal_action.root

		#create special dummy step for init_graph and add to graphs {}
		self.setup(init_graph, init_action, goal_action)
		self.Open =  Frontier()
		self.Open.insert(init_graph)

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
		init_flaws = (Flaw((dummy_final, prec), 'opf') for prec in graph.getNeighborsByLabel(dummy_final, 'precond-of'))
		for flaw in init_flaws:
			graph.flaws.insert(graph, flaw)

		#For each flaw, determine candidate effects and risks, then insert into flawlib by bin
		#for flaw in init_flaws:
		#	graph.flaws.insert(graph,flaw)


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
		Precondition = graph.subgraph(precondition)

		results = set()
		if precondition.name == 'occupied':
			pass

		for op in self.op_graphs:
			for eff in op.getNeighborsByLabel(op.root, 'effect-of'):

				if not eff.isConsistent(precondition):
					continue

				Effect = op.getElementGraphFromElement(eff,Condition)
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
						graph_copy = graph.deepcopy()
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


						#for edge in new_step_op.edges:
						#	if edge.source in untouched_step_elms:
						#		graph_copy.elements.add(elm)
						#	if edge.sink in untouched_step_elms:
						#		graph_copy.elements.add(elm)

						# For each edge 'e1 --label--> e2 in new_step_op such that e1 not in eff_abs,
							# if exists some e_p s.t. e_p.merge(sink), replace edge sink
							# graph_copy.add(edge)
						for edge in new_step_op.edges:
							if edge.source in untouched_step_elms:
								#untouched_step_elms
								if not edge.sink in untouched_step_elms:
									e_abs = eff_abs.getElementById(edge.sink.ID)
									if e_abs is None:
										pass
									edge.sink = graph_copy.getElementById(e_abs.replaced_ID)#place here
									#untouched_step_elms.add(edge.sink)
								graph_copy.edges.add(edge)
								#to prevent same edge from being selected in this iteration of for-loop



						# adds causal link and ordering constraints
						condition = graph_copy.getElementById(Precondition.root.ID)
						self.addStep(graph_copy, new_step_op.root, s_need, condition, new = True)

						#Now that step is in plan, determine for which open conditions the step is a cndt/risk
						graph_copy.flaws.addCndtsAndRisks(graph_copy, new_step_op.root)
						#print('\ncreated child (newStep):\n')
						#print(graph_copy)
						#print('\n')

						results.add(graph_copy)
		return results


	def reuse(self, graph, flaw):
		results = set()
		s_need, pre = flaw.flaw
		Precondition = graph.subgraph(pre)

		#limit search significantly by only considering precompliled cndts
		for eff in graph.flaws.cndts[flaw]:
			if not eff.isConsistent(pre):
				continue
			Effect = graph.subgraph(eff)
			if not Effect.canAbsolve(Precondition):
				continue

			#step = next(iter(graph.getParents(eff)))
			step = graph.getEstablishingParent(eff)

			Effect_absorbtions = Effect.getInstantiations(Precondition)

			for eff_abs in Effect_absorbtions:
				# 1 Create new child graph
				graph_copy = graph.deepcopy()

				# 2 Replace effect with eff_abs, which is unified with the precondition
				graph_copy.mergeGraph(eff_abs, no_add=True)

				# 3) "Redirect Task""

				# Get elm for elms which were in eff_abs but not in precondition (were replaced)
				precondition_IDs = {element.ID for element in Precondition.elements}
				new_snk_cddts = {elm for elm in eff_abs.elements if not elm.ID in precondition_IDs}
				snk_swap_dict = {graph_copy.getElementById(elm.replaced_ID): graph_copy.getElementById(elm.ID)
								 for elm in new_snk_cddts}
				for old, new in snk_swap_dict.items():
					graph_copy.replaceWith(old, new)

				# adds causal link and ordering constraints
				condition = graph_copy.getElementById(eff_abs.root.ID)
				self.addStep(graph_copy, step, s_need, condition, new=False)
					#print('\ncreated child (reuse):\n')
					#print(graph_copy)
					#print('\n')
				# add graph to children
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
			#prcs = graph.getNeighborsByLabel(s_add, 'precond-of')
			#preconditions = graph.getNeighborsByLabel(s_add, 'precond-of')
			equalNames = {'equals', 'equal', '='}
			noncodesg = {prc for prc in prc_edges if prc.sink.name in equalNames and not prc.sink.truth}

			#Remove equality precondition edges
			graph.edges -= noncodesg
			new_flaws = (Flaw((s_add, prec.sink), 'opf') for prec in prc_edges if not prec in noncodesg)
			for flaw in new_flaws:
				graph.flaws.insert(graph,flaw)

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
		promotion = graph.deepcopy()
		promotion.OrderingGraph.addEdge(causal_link.sink, threat)
		if promotion.OrderingGraph.isInternallyConsistent():
			#results.add((promotion, 'promotion'))
			results.add(promotion)
			#print('\ncreated child (promotion):\n')
			#print(promotion)
			#print('\n')


		#Demotion
		demotion = graph.deepcopy()
		demotion.OrderingGraph.addEdge(threat, causal_link.source)
		if demotion.OrderingGraph.isInternallyConsistent():
			results.add(demotion)
			#print('\ncreated child (demotion):\n')
			#print(demotion)
			#print('\n')

		#Restriction
		restriction = graph.deepcopy()
		if restriction.preventThreatWithRestriction(condition=causal_link.label, threat=effect):
			results.add(restriction)
		#print('\ncreated child (restriction):\n')
		#print(restriction)
		#print('\n')
		#results.add((restriction, 'restriction'))

		return results


	def generateChildren(self, graph, flaw):
		results = set()
		if flaw.name == 'opf':
			results = self.reuse(graph, flaw)
			results.update(self.newStep(graph, flaw))
			if len(results) == 0:
				print('could not resolve opf')
				return results

		if flaw.name == 'tclf':
			results = self.resolveThreatenedCausalLinkFlaw(graph, flaw)
			if len(results) == 0:
				print('could not resolve tclf')
				return results

		#for result, res in results:
		for result in results:
			new_flaws = result.detectThreatenedCausalLinks()
			result.flaws.threats.update(new_flaws)

		return results

	def POCL(self):
		Visited = []
		while len(self.Open) > 0:

			#Select child
			graph = self.Open.pop()
			print(graph)
			if not graph.isInternallyConsistent():
				print('branch terminated')
				return None

			if len(graph.flaws) == 0:
				#print('solution selected')
				return graph
			print(graph.flaws)

			#Select Flaw
			flaw = graph.flaws.next()

			print('selected : {}\n'.format(flaw))

			#Add to Visited list, indicating that we've generated all its children
			Visited.append((graph,flaw))

			#Add children to Open List
			children = self.generateChildren(graph, flaw)

			print('generated children: {}'.format(len(children)))
			for child in children:
				self.Open.insert(child)

			print('open list number: {}'.format(len(self.Open)))
			print('\n')


def preprocessDomain(operators):
	#get all effect predicates
	pred_set = set()
	for op in operators:
		pred_set.update({eff.name for eff in  op.getNeighborsByLabel(op.root, 'effect-of')})
	return pred_set

def topoSort(graph):
	OG  = copy.deepcopy(graph.OrderingGraph)
	L =[]
	S = {graph.initial_dummy_step}
	while len(S) > 0:
		n = S.pop()
		L.append(n)
		for m_edge in OG.getIncidentEdges(n):
			OG.edges.remove(m_edge)
			if len({edge for edge in OG.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	if len(OG.edges) > 0:
		print('error')
		return
	return L

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

	#f = open('workfile', 'w')
	operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
	#non_static_preds = preprocessDomain(operators)
	FlawLib.non_static_preds = preprocessDomain(operators)
	planner = PlanSpacePlanner(operators, objects, initAction, goalAction)

	result = planner.POCL()

	totOrdering = topoSort(result)
	print('\n\n\n')
	for step in totOrdering:
		#Step = result.subgraph(step, Action)
		print(result.subgraph(step, Action))

	#print('\n\n\n')
	#print(result)
