from Ground_Compiler_Library.GElm import GLiteral, GStep
from uuid import uuid4
from Flaws import FlawLib
from Ground_Compiler_Library.OrderingGraph import OrderingGraph, CausalLinkGraph
import copy


from collections import namedtuple, defaultdict

dummyTuple = namedtuple('dummyTuple', ['init', 'final'])


class GPlan:

	def __init__(self, dummy_init_constructor, dummy_goal_constructor):
		self.ID = uuid4()
		self.OrderingGraph = OrderingGraph()
		self.CausalLinkGraph = CausalLinkGraph()
		self.flaws = FlawLib()
		self.solved = False
		self.dummy = dummyTuple(dummy_init_constructor.instantiate(), dummy_goal_constructor.instantiate())


		self.init = self.dummy.init.preconds
		self.goal = self.dummy.final.preconds
		self.steps = [self.dummy.init, self.dummy.final]

		# check if any existing steps are choices (instances of cndts of open conditions)
		self.dummy.final.update_choices(self.steps)

		self.cndt_map = None
		self.threat_map = None
		# self.gstep_lib = ground_step_list

		# self.h_step_dict = dict()

		self.heuristic = float('inf')

	def __len__(self):
		return len(self.steps)

	def __getitem__(self, pos):
		return self.steps[pos]

	def __setitem__(self, item, pos):
		self.steps[pos] = item

	def insert(self, step):
		self.steps.append(step)

	def instantiate(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		# refresh attributes
		return new_self


	# def h_condition(self, step_num, precond):
	# 	if precond.is_static:
	# 		return 0
	# 	if precond in self.init:
	# 		return 0
	#
	# 	min_so_far = float('inf')
	# 	for cndt in self.gstep_lib[step_num].cndt_map[precond.ID]:
	# 		cndt_heuristic = self.h_step(cndt)
	# 		if cndt_heuristic < min_so_far:
	# 			min_so_far = cndt_heuristic
	# 	return min_so_far
	#
	#
	# def h_step(self, step_num):
	# 	if step_num in self.h_step_dict.keys():
	# 		return self.h_step_dict[step_num]
	# 	if step_num == self.dummy.init.step_num:
	# 		return 1
	#
	# 	sumo = 1
	# 	for pre in self.gstep_lib[step_num].preconds:
	# 		sumo += self.h_condition(step_num, pre)
	#
	# 	self.h_step_dict[step_num] = sumo
	# 	return sumo
	#
	# def h_plan(self):
	# 	sumo = 0
	#
	# 	for s_need, p in self.flaws.OCs():
	#
	# 		exists_choice = False
	# 		for choice in s_need.choices:
	# 			if self.OrderingGraph.isPath(s_need, choice):
	# 				exists_choice = True
	#
	# 		if len(s_need.choices) == 0 or not exists_choice:
	# 			sumo += self.h_condition(s_need.step_num, p)
	#
	# 	return sumo

	# @property
	# def heuristic(self):
	# 	return self.h_plan()

	@property
	def cost(self):
		return len(self.steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent()

	def detectTCLFperCL(self, GL, causal_link):
		detectedThreatenedCausalLinks = set()
		for step in self.steps:
			self.testThreat(GL, self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def detectTCLFperStep(self, GL, step):
		detectedThreatenedCausalLinks = set()
		for causal_link in self.CausalLinkGraph.edges:
			self.testThreat(GL, self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def testThreat(self, nonThreats, causal_link, step, dTCLFs):
		if step in nonThreats[causal_link]:
			return
		if step == causal_link.source or step == causal_link.sink:
			nonThreats[causal_link].add(step)
			return
		if self.OrderingGraph.isPath(causal_link.sink, step):
			nonThreats[causal_link].add(step)
			return
		if self.OrderingGraph.isPath(step, causal_link.source):
			nonThreats[causal_link].add(step)
			return
		if step.stepnumber not in GL.threat_dict[causal_link.sink.stepnumber]:
			nonThreats[causal_link].add(step)
			return
		if test(Action.subgraph(self, step), causal_link):
			dTCLFs.add(TCLF((step, causal_link), 'tclf'))
		nonThreats[causal_link].add(step)

	#@clock
	def detectThreatenedCausalLinks(self):
		detectedThreatenedCausalLinks = set()
		for causal_link in self.CausalLinkGraph.edges:
			for step in self.steps:
				self.testThreat(self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def __lt__(self, other):
		if self.cost + self.heuristic != other.cost + other.heuristic:
			return (self.cost + self.heuristic) < (other.cost + other.heuristic)
		elif self.heuristic != other.heuristic:
			return self.heuristic < other.heuristic
		elif self.cost != other.cost:
			return self.cost < other.cost
		elif len(self.flaws) != len(other.flaws):
			return len(self.flaws) < len(other.flaws)
		else:
			return self.OrderingGraph < other.OrderingGraph

	def __str__(self):
		return 'GPlan{} c={} h={}\t'.format(self.ID, self.cost, self.heuristic) + \
				str(self.steps) + '\n' + str(self.OrderingGraph) + '\n' + str(self.CausalLinkGraph)

	def __repr__(self):
		return self.__str__()


def topoSort(ordering_graph):
	L =[]
	# ogr = copy.deepcopy(ordering_graph)
	ogr = OrderingGraph()
	init_dummy = GSte(name='init_dummy')
	ogr.elements.add(init_dummy)
	for elm in list(ordering_graph.elements):
		ogr.addOrdering(init_dummy, elm)
	S = {init_dummy}

	#L = list(graph.Steps)
	while len(S) > 0:
		n = S.pop()
		if n not in L:
			L.append(n)
		for m_edge in ogr.getIncidentEdges(n):
			ogr.edges.remove(m_edge)
			#if the sink has no other ordering sources, add it to the visited
			if len({edge for edge in ogr.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	return L

if __name__ == '__main__':
	pass