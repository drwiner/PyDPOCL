from GPlan import GPlan
from Flaws import OPF, TCLF
from uuid import uuid4
import copy
from heapq import heappush, heappop


class Frontier:

	def __init__(self):
		self._frontier = []

	def __len__(self):
		return len(self._frontier)

	def __getitem__(self, position):
		return self._frontier[position]

	def pop(self):
		return heappop(self._frontier)

	def insert(self, plan):
		heappush(self._frontier, plan)

	def extend(self, itera):
		for item in itera:
			self.insert(item)

	def __repr__(self):
		k = 'frontier plans\n'
		for plan in self._frontier:
			'{}:{} c={} h={} steps:\n{}\n'.format(k, str(plan.ID), plan.cost, plan.heuristic, plan.steps)
		return k


class GPlanner:
	"""
	Plan space planner, only instantiate once per planner, starts with ground steps
	"""

	def __init__(self, gsteps):
		self.gsteps = gsteps
		self.ID = uuid4()
		self.h_step_dict = dict()
		self.h_lit_dict = dict()

		root_plan = GPlan(gsteps[-2].instantiate(), gsteps[-1].instantiate())
		root_plan.OrderingGraph.addOrdering(root_plan.dummy.init, root_plan.dummy.final)
		for p in root_plan.dummy.final.open_preconds:
			root_plan.flaws.insert(root_plan, OPF(root_plan.dummy.final, p))

		self._frontier = Frontier()
		self.insert(root_plan)
		self._h_visited = []

	# Private Hooks #

	def __len__(self):
		return len(self._frontier)

	def __getitem__(self, position):
		return self._frontier[position]

	# Methods #

	def pop(self):
		return self._frontier.pop()

	def insert(self, plan):
		plan.heuristic = self.h_plan(plan)
		self._frontier.insert(plan)

	def solve(self, k=4):
		# find k solutions to problem

		completed = []
		expanded = 0

		while len(self) > 0:
			plan = self.pop()
			expanded += 1
			if not plan.isInternallyConsistent():
				print('prune {}'.format(plan.ID))
				continue

			if len(plan.flaws) == 0:
				print('solution found at {} nodes expanded and {} nodes visited'.format(expanded, len(self)+expanded))
				completed.append(plan)
				for step in topoSort(plan):
					print(step)
				if len(completed) == k:
					return completed
				continue

			# Select Flaw
			flaw = plan.flaws.next()
			print('{} selected : {}\n'.format(flaw.name, flaw))

			if isinstance(flaw, TCLF):
				self.resolve_threat(plan, flaw)
			else:
				self.add_step(plan, flaw)
				self.reuse_step(plan, flaw)

		raise ValueError('FAIL: No more plans to visit with {} nodes expanded'.format(expanded))

	def add_step(self, plan, flaw):
		s_need, p = flaw.flaw
		cndts = s_need.cndt_map[p.ID]

		if len(cndts) == 0:
			return

		# need indices
		s_index = plan.index(s_need)
		p_index = s_need.preconds.index(p)
		for cndt in cndts:
			# cannot add a step which is the inital step
			if not self.gsteps[cndt].instantiable:
				continue
			# clone plan and new step
			new_plan = plan.instantiate()
			new_step = self.gsteps[cndt].instantiate()
			new_plan.insert(new_step)

			# operate on cloned plan
			mutable_s_need = new_plan[s_index]
			mutable_p = mutable_s_need.preconds[p_index]
			mutable_s_need.fulfill(mutable_p)
			mutable_s_need.update_choices(new_plan)
			# add orderings
			new_plan.OrderingGraph.addEdge(new_step, mutable_s_need)
			new_plan.OrderingGraph.addEdge(new_plan.dummy.init, new_step)
			new_plan.OrderingGraph.addEdge(new_step, new_plan.dummy.final)
			# add causal link
			c_link = new_plan.CausalLinkGraph.addEdge(new_step, mutable_s_need, mutable_p)

			# add open conditions for new step
			for pre in new_step.open_preconds:
				new_plan.flaws.insert(new_plan, OPF(new_step, pre))

			# check if this link is threatened
			ignore_these = {mutable_s_need.ID, new_step.ID}
			for step in new_plan.steps:
				if step.ID in ignore_these:
					continue
				if step.stepnum in mutable_s_need.threats:
					new_plan.flaws.insert(new_plan, TCLF(step, c_link))

			# check if adding this step threatens other causal links
			for cl in new_plan.CausalLinkGraph.edges:
				if cl == c_link:
					continue
				# if new_step.stepnum not in cl.sink.threats:
				# 	continue
				if new_step.stepnum not in cl.sink.threat_map[cl.label]:
					continue
				if new_plan.OrderingGraph.isPath(new_step, cl.source):
					continue
				if new_plan.OrderingGraph.isPath(cl.sink, new_step):
					continue
				new_plan.flaws.insert(new_plan, TCLF(new_step, cl))

			self.insert(new_plan)

	def reuse_step(self, plan, flaw):
		s_need, p = flaw.flaw
		choices = [step for step in plan.steps if step.stepnum in s_need.cndt_map[p.ID]]
		if len(choices) == 0:
			return

		# need indices
		s_index = plan.index(s_need)
		p_index = s_need.preconds.index(p)
		for choice in choices:
			# clone plan and new step
			new_plan = plan.instantiate()
			mutable_s_need = new_plan.steps[s_index]
			mutable_p = mutable_s_need.preconds[p_index]
			mutable_s_need.fulfill(mutable_p)
			mutable_s_need.update_choices(new_plan)

			old_step = new_plan.steps[plan.index(choice)]
			new_plan.OrderingGraph.addEdge(old_step, mutable_s_need)
			# add causal link
			c_link = new_plan.CausalLinkGraph.addEdge(old_step, mutable_s_need, mutable_p)

			# check if this link is threatened
			ignore_these = {mutable_s_need.ID, old_step.ID}
			for step in new_plan.steps:
				if step.ID in ignore_these:
					continue
				if step.stepnum not in mutable_s_need.threats:
					continue
				if new_plan.OrderingGraph.isPath(s_need, step):
					continue
				if new_plan.OrderingGraph.isPath(step, old_step):
					continue
				new_plan.flaws.insert(new_plan, TCLF(step, c_link))

			# check if adding this step threatens other causal links
			for cl in new_plan.CausalLinkGraph.edges:
				if cl == c_link:
					continue
				if old_step.stepnum not in cl.sink.threat_map[cl.label.ID]:
					continue
				if new_plan.OrderingGraph.isPath(old_step, cl.source):
					continue
				if new_plan.OrderingGraph.isPath(cl.sink, old_step):
					continue
				new_plan.flaws.insert(new_plan, TCLF(old_step, cl))

			self.insert(new_plan)

	def resolve_threat(self, plan, tclf):
		threat_index = plan.index(tclf.threat)
		src_index = plan.index(tclf.link.source)
		snk_index = plan.index(tclf.link.sink)

		# Promotion
		new_plan = plan.instantiate()
		threat = new_plan[threat_index]
		sink = new_plan[snk_index]
		new_plan.OrderingGraph.addEdge(sink, threat)
		self.insert(new_plan)

		# Demotion
		new_plan = plan.instantiate()
		threat = new_plan[threat_index]
		source = new_plan[src_index]
		new_plan.OrderingGraph.addEdge(threat, source)

		self.insert(new_plan)

	# Heuristic Methods #

	def h_condition(self, plan, stepnum, precond):
		if precond.is_static:
			return 0
		if precond in plan.init:
			return 0
		if precond in self.h_lit_dict.keys():
			return self.h_lit_dict[precond]
		if precond in self._h_visited:
			return 0

		self._h_visited.append(precond)

		min_so_far = float('inf')
		for cndt in self.gsteps[stepnum].cndt_map[precond.ID]:
			cndt_heuristic = self.h_step(plan, cndt)
			if cndt_heuristic < min_so_far:
				min_so_far = cndt_heuristic

		self.h_lit_dict[precond] = min_so_far
		return min_so_far

	def h_step(self, plan, stepnum):
		if stepnum in self.h_step_dict.keys():
			return self.h_step_dict[stepnum]
		if stepnum == plan.dummy.init.stepnum:
			return 1
		if stepnum in self._h_visited:
			return 1

		self._h_visited.append(stepnum)
		sumo = 1
		for pre in self.gsteps[stepnum].preconds:
			sumo += self.h_condition(plan, stepnum, pre)

		self.h_step_dict[stepnum] = sumo
		return sumo

	def h_plan(self, plan):
		sumo = 0

		self._h_visited = []
		for flaw in plan.flaws.OCs():
			exists_choice = False
			if len(flaw.s_need.choices) > 0:
				exists_choice = True

			if len(flaw.s_need.choices) == 0 or not exists_choice:
				sumo += self.h_condition(plan, flaw.s_need.stepnum, flaw.p)

		return sumo

def topoSort(plan):
	OG = copy.deepcopy(plan.OrderingGraph)
	L =[]
	S = {plan.dummy.init}
	while len(S) > 0:
		n = S.pop()
		L.append(n)
		for m_edge in OG.getIncidentEdges(n):
			OG.edges.remove(m_edge)
			if len({edge for edge in OG.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	return L

if __name__ == '__main__':
	pass