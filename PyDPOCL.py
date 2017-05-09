from GPlan import GPlan
from Flaws import OPF, TCLF
from uuid import uuid4
import copy
from heapq import heappush, heappop

LOG = 0


def log_message(message):
	if LOG:
		print(message)


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

		root_plan = GPlan(gsteps[-2], gsteps[-1])
		root_plan.OrderingGraph.addOrdering(root_plan.dummy.init, root_plan.dummy.final)
		for p in root_plan.dummy.final.open_preconds:
			root_plan.flaws.insert(root_plan, OPF(root_plan.dummy.final, p))

		self._frontier = Frontier()
		self.insert(root_plan)
		self._h_visited = []
		self.plan_num = 0

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
				log_message('prune {}'.format(plan.name))
				continue

			log_message('Plan {} selected cost={} heuristic={}'.format(plan.name, plan.cost, plan.heuristic))

			if len(plan.flaws) == 0:
				print('solution {} found at {} nodes expanded and {} nodes visited'.format(plan.name, expanded, len(self)+expanded))
				completed.append(plan)
				for step in plan.OrderingGraph.topoSort():
					print(step)
				print('\n')
				if len(completed) in {8,4}:
					print('l')
				if len(completed) == k:
					return completed
				continue

			# Select Flaw
			flaw = plan.flaws.next()
			log_message('{} selected : {}\n'.format(flaw.name, flaw))

			self.plan_num = 0

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

			new_plan = plan.instantiate(str(self.plan_num))
			self.plan_num += 1

			# use indices befoer inserting new steps
			mutable_s_need = new_plan[s_index]
			mutable_p = mutable_s_need.preconds[p_index]

			# instantiate new step
			new_step = self.gsteps[cndt].instantiate()

			# recursively insert new step and substeps into plan, adding orderings and flaws
			new_plan.insert(new_step)
			log_message('Add step {} to plan {}\n'.format(str(new_step), new_plan.name))

			# resolve s_need with the new step
			new_plan.resolve(new_step, mutable_s_need, mutable_p)

			# insert our new mutated plan into the frontier
			self.insert(new_plan)

	def reuse_step(self, plan, flaw):
		s_need, p = flaw.flaw

		choices = [step for step in plan.steps if step.stepnum in s_need.cndt_map[p.ID] and not plan.OrderingGraph.isPath(s_need, step)]
		if len(choices) == 0:
			return

		# need indices
		s_index = plan.index(s_need)
		p_index = s_need.preconds.index(p)
		for choice in choices:
			# clone plan and new step
			new_plan = plan.instantiate(str(self.plan_num))
			self.plan_num += 1

			# use indices befoer inserting new steps
			mutable_s_need = new_plan[s_index]
			mutable_p = mutable_s_need.preconds[p_index]

			# use index to find old step
			old_step = new_plan.steps[plan.index(choice)]
			log_message('Reuse step {} to plan {}\n'.format(str(old_step), new_plan.name))

			# resolve open condition with old step
			new_plan.resolve(old_step, mutable_s_need, mutable_p)

			# insert mutated plan into frontier
			self.insert(new_plan)

	def resolve_threat(self, plan, tclf):
		threat_index = plan.index(tclf.threat)
		src_index = plan.index(tclf.link.source)
		snk_index = plan.index(tclf.link.sink)

		# Promotion
		new_plan = plan.instantiate(str(self.plan_num))
		self.plan_num += 1
		threat = new_plan[threat_index]
		sink = new_plan[snk_index]
		new_plan.OrderingGraph.addEdge(sink, threat)
		if hasattr(threat, 'sibling'):
			new_plan.OrderingGraph.addEdge(sink, threat.sibling)
		if hasattr(sink, 'sibling'):
			new_plan.OrderingGraph.addEdge(sink.sibling, threat)
		threat.update_choices(new_plan)
		self.insert(new_plan)
		log_message('promote {} in front of {} in plan {}'.format(threat, sink, new_plan.name))

		# Demotion
		new_plan = plan.instantiate(str(self.plan_num))
		self.plan_num += 1
		threat = new_plan[threat_index]
		source = new_plan[src_index]
		new_plan.OrderingGraph.addEdge(threat, source)
		if hasattr(threat, 'sibling'):
			new_plan.OrderingGraph.addEdge(source, threat.sibling)
		if hasattr(source, 'sibling'):
			new_plan.OrderingGraph.addEdge(source.sibling, threat)
		threat.update_choices(new_plan)
		self.insert(new_plan)
		log_message('demotion {} behind {} in plan {}'.format(threat, source, new_plan.name))

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
		# if the following is true, then we have an "sub-init" step in our mist
		if len(self.gsteps[stepnum].cndts) == 0:
			stepnum += 2

		for cndt in self.gsteps[stepnum].cndt_map[precond.ID]:
			if not self.gsteps[cndt].instantiable:
				continue
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

	def h_subplan(self, subplan):
		pass

import sys
import pickle
import Ground_Compiler_Library

if __name__ == '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		domain_file = 'Ground_Compiler_Library//domains/travel_domain.pddl'
		problem_file = 'Ground_Compiler_Library//domains/travel-to-la.pddl'
	d_name = domain_file.split('/')[-1].split('.')[0]
	p_name = problem_file.split('/')[-1].split('.')[0]
	uploadable_ground_step_library_name = 'Ground_Compiler_Library//' + d_name + '.' + p_name


	RELOAD = 1
	if RELOAD:
		GL = Ground_Compiler_Library.Ground.GLib(domain_file, problem_file)
		with open('ground_steps.txt', 'w') as gs:
			for step in GL:
				gs.write(str(step))
				gs.write('\n')
		ground_step_list = Ground_Compiler_Library.deelementize_ground_library(GL)
		with open('ground_steps.txt', 'a') as gs:
			gs.write('\n\n')
			for step in ground_step_list:
				gs.write(str(step))
				gs.write('\n')
		Ground_Compiler_Library.Ground.upload(ground_step_list, uploadable_ground_step_library_name)

	ground_steps = pickle.load(open(uploadable_ground_step_library_name, 'rb'))
	planner = GPlanner(ground_steps)
	planner.solve(k=15)