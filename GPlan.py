from Ground_Compiler_Library.GElm import GLiteral, GStep
from uuid import uuid4
from Flaws import FlawLib
from Ground_Compiler_Library.OrderingGraph import OrderingGraph, CausalLinkGraph
import copy


from collections import namedtuple, defaultdict

dummyTuple = namedtuple('dummyTuple', ['init', 'final'])


class GPlan:

	def __init__(self, ground_step_list):
		self.ID = uuid4()
		self.OrderingGraph = OrderingGraph()
		self.CausalLinkGraph = CausalLinkGraph()
		self.flaws = FlawLib()
		self.solved = False
		self.dummy = dummyTuple(ground_step_list[-2].step_num, ground_step_list[-1].step_num)

		self.init = self.dummy.init.preconds
		self.goal = self.dummy.final.preconds
		self.steps = [self.dummy.init, self.dummy.final]
		self.cndt_map = None
		self.threat_map = None
		self.gstep_lib = ground_step_list

		self.h_step_dict = dict()


	def instantiate(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		# refresh attributes
		return new_self


	# precondiion hueristic: 0 if p holds initially, minimum step heuristic (use cndt_map)
	# step heuristic: 1 + sum of precondition heuristic

	def h_condition(self, step_num, precond):
		if precond.is_static:
			return 0
		if precond in self.init:
			return 0

		min_so_far = float('inf')
		for cndt in self.gstep_lib[step_num].cndt_map[precond.ID]:
			cndt_heuristic = self.h_step(cndt)
			if cndt_heuristic < min_so_far:
				min_so_far = cndt_heuristic
		return min_so_far


	def h_step(self, step_num):
		if step_num in self.h_step_dict.keys():
			return self.h_step_dict[step_num]

		sumo = 1
		for pre in self.gstep_lib[step_num].preconds:
			sumo += self.h_condition(step_num, pre)

		self.h_step_dict[step_num] = sumo
		return sumo

	def h_plan(self):
		sumo = 0
		for oc in self.flaws.OCs():
			s_need, p = oc.flaw

			exists_choice = False
			for choice in s_need.choices:
				if self.OrderingGraph.isPath(s_need, choice):
					exists_choice = True

			if len(s_need.choices) == 0 or not exists_choice:
				sumo += self.h_condition(s_need.step_num, p)

		return sumo

	@property
	def heuristic(self):
		return self.h_plan()

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


if __name__ == '__main__':
	pass