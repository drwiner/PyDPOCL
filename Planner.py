#from Flaws import *
from pddlToGraphs import *
import collections
from heapq import heappush, heappop
import itertools
from clockdeco import clock

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

	@clock
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
		Precondition = graph.subgraph(precondition, Condition)
		Precondition.updateArgs()
		results = set()

		for op in self.op_graphs:
			for eff in op.getNeighborsByLabel(op.root, 'effect-of'):

				if not eff.isConsistent(precondition):
					continue

				Effect = op.subgraph(eff, Condition)

				#Can all edges in Precondition be matched to a consistent edge in Effect, without replacement
				if not Effect.isConsistentSubgraph(Precondition):
					continue

				graph_copy = graph.deepcopy()

				#precondition = precondition
				#condition = graph_copy.getElementById(Precondition.root.ID)

				#nei : new element id, to easily access element from graph
				step_op, nei = op.instantiateOperator(old_element_id=eff.ID)
				effect_token = step_op.getElementById(nei)
				Effect = step_op.subgraph(effect_token, Condition)

				## Bookkeeping for replacing effect of step_op with precondition
				arg_labels = step_op.getArgLabels(tuple(Effect.Args))
				step_op.edges = {edge for edge in step_op.edges if edge.sink != effect_token and edge.source !=
							 effect_token}
				step_op.elements = {elm for elm in step_op.elements if elm != effect_token}
				step_op.updateArgs()
				step_op.replaceArgsFromLabels(Precondition.Args, arg_labels)
				###


				step_op.edges.add(Edge(step_op.root, precondition, 'effect-of'))
				graph_copy.edges.update(step_op.edges)
				graph_copy.elements.update(step_op.elements)

				self.addStep(graph_copy, step_op.root, s_need, precondition, new=True)
				graph_copy.flaws.addCndtsAndRisks(graph_copy, step_op.root)
				# print('\ncreated child (newStep):\n')
				# print(graph_copy)
				# print('\n')
				results.add(graph_copy)

		return results

	@clock
	def reuse(self, graph, flaw):
		results = set()
		s_need, pre = flaw.flaw
		Precondition = graph.subgraph(pre)
		#limit search significantly by only considering precompliled cndts
		for eff in graph.flaws.cndts[flaw]:

			if not eff.isConsistent(pre):
				continue

			Effect = graph.subgraph(eff)
			if not Effect.isConsistentSubgraph(Precondition):
				continue

			graph_copy = graph.deepcopy()
			#eff_token = graph_copy.getElementById(eff.ID)
			#pre_token = graph_copy.getElementById(pre.ID)

			arg_mapping = graph_copy.createArgMapping(eff, pre)
			removable = {edge for edge in graph_copy.edges if edge.sink == pre or edge.source == pre}
			graph_copy.edges -= removable
			graph_copy.edges.add(Edge(s_need, eff, 'precond-of'))
			graph_copy.elements -= {pre}
			graph_copy.Unify(arg_mapping)
			establishing_step = graph_copy.getEstablishingParent(eff)


			self.addStep(graph_copy, establishing_step, s_need, eff, new=False)
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

			#just edges of label 'precond'
			noncodesg = {prc for prc in prc_edges if prc.sink.name in equalNames and not prc.sink.truth}

			if len(noncodesg) > 0:
				graph.edges -= noncodesg
				if not graph.addNonEqualityRestrictions({nonco.sink for nonco in noncodesg}):
					print('problem with adding nonequality restrictions')

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

		#	print(restriction)
		#	print('\n')
		#results.add((restriction, 'restriction'))

		return results


	def generateChildren(self, graph, flaw):
		results = set()
		if flaw.name == 'opf':
			results = self.reuse(graph, flaw)
			results.update(self.newStep(graph, flaw))
			if len(results) == 0:
				#print('could not resolve opf')
				return results

		if flaw.name == 'tclf':
			results = self.resolveThreatenedCausalLinkFlaw(graph, flaw)
			if len(results) == 0:
				#print('could not resolve tclf')
				return results

		#for result, res in results:
		for result in results:
			new_flaws = result.detectThreatenedCausalLinks()
			result.flaws.threats.update(new_flaws)

		return results

	@clock
	def POCL(self):
		Visited = []
		while len(self.Open) > 0:
			#Select child
			graph = self.Open.pop()
			#print(graph)
			if not graph.isInternallyConsistent():
				print('branch terminated')
				continue


			if len(graph.flaws) == 0:
				#print('solution selected')
				return graph
			#print(graph.flaws)

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

def obTypesDict(object_types):
	obtypes = defaultdict(set)
	for t in object_types:
		obtypes[t.name].add(t.parent)
		accumulated = set()
		rFollowHierarchy(object_types, t.parent, accumulated)
		obtypes[t.name].update(accumulated)
	return obtypes


def rFollowHierarchy(object_types, child_name, accumulated = set()):
	for ob in object_types:
		if not ob.name in accumulated:
			if ob.name == child_name:
				accumulated.add(ob.parent)
				rFollowHierarchy(object_types, ob.parent, accumulated)

def groundStepList(operators, objects):
	gsteps = []
	for op in operators:
		op.updateArgs()
		cndts = [[obj for obj in objects if arg.typ == obj.typ or arg.typ in obtypes[obj.typ]] for arg in op.Args]
		tuples = itertools.product(*cndts)
		for t in tuples:
			gstep = copy.deepcopy(op)
			gstep.replaceArgs(t)
			gsteps.append(gstep)
	return gsteps


import sys


if __name__ ==  '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		#domain_file = 'domains/mini-indy-domain.pddl'
		#problem_file = 'domains/mini-indy-problem.pddl'
		domain_file = 'domains/ark-domain.pddl'
		problem_file = 'domains/ark-problem.pddl'

	#f = open('workfile', 'w')
	operators, objects, object_types, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
	#non_static_preds = preprocessDomain(operators)
	FlawLib.non_static_preds = preprocessDomain(operators)
	obtypes = obTypesDict(object_types)

	Argument.object_types = obtypes
	planner = PlanSpacePlanner(operators, objects, initAction, goalAction)

	###
	#Task: create list of fully ground steps given domain actions (operators), and arguments (objects)
	#gsteps = groundStepList(operators, objects)
	#for g in gsteps:
#		print(g)
	#
	###
	result = planner.POCL()

	totOrdering = topoSort(result)
	print('\n\n\n')
	for step in totOrdering:
		#Step = result.subgraph(step, Action)
		print(result.subgraph(step, Action))

	#print('\n\n\n')
	#print(result)
