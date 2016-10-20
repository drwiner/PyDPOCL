from pddlToGraphs import parseDomAndProb
from PlanElementGraph import PlanElementGraph, Action, Condition
from Flaws import Flaw
from heapq import heappush, heappop
from clockdeco import clock
from Ground import reload, GLib
from Graph import Edge, isIdenticalElmsInArgs, retargetElmsInArgs, retargetArgs

import copy

"""
	Algorithm for Plan-Graph-Space search of Story Plan
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

	def __repr__(self):
		k = str('\nfrontier plans\n')
		for plan in self._frontier:
			k += '\n' + str(plan.ID) + ' c=' + str(plan.cost) + ' h=' + str(plan.heuristic) + ' ' + str(
				plan.Step_Graphs)
		return k


class PlanSpacePlanner:

	def __init__(self, GL):
		#Assumes these parameters are already read from file

		self.objects = GL.objects
		self.GL = GL

		SP = self.setup('story')
		self._frontier = Frontier()
		self._frontier.insert(SP)

	def __len__(self):
		return len(self._frontier)

	def pop(self):
		return self._frontier.pop()

	def __getitem__(self, position):
		return self._frontier[position]

	def __setitem__(self, plan, position):
		self._frontier[position] = plan

	def insert(self, plan):
		self._frontier.insert(plan)

	def setup(self, plan_name):
		"""
			Create step typed element DI, with effect edges to each condition of start_set
			Create step typed element DG, with precondition edges to each condition of end_set
			Add ordering from DI to DG
		"""

		s_init = copy.deepcopy(self.GL[-2])
		s_init.replaceInternals()
		s_goal = copy.deepcopy(self.GL[-1])
		s_goal.replaceInternals()

		s_init_plan = PlanElementGraph(name=plan_name, Elements=self.objects|s_init.elements|s_goal.elements,
									   Edges=s_init.edges|s_goal.edges)

		s_init_plan.initial_dummy_step = s_init.root
		s_init_plan.final_dummy_step = s_goal.root

		s_init_plan.OrderingGraph.addOrdering(s_init.root, s_goal.root)

		#Add initial Open precondition flaws for dummy step
		#init_flaws = (Flaw((s_goal.root, prec), 'opf') for prec in s_goal.Preconditions)
		#for flaw in init_flaws:
		for prec in s_goal.Preconditions:
			s_init_plan.flaws.insert(self.GL, s_init_plan, Flaw((s_goal.root, prec), 'opf'))
		return s_init_plan


	#@clock
	def newStep(self, plan, flaw):
		"""
		@param plan:
		@param flaw:
		@return:
		"""

		results = set()
		s_need, precondition = flaw.flaw
		antecedents = self.GL.pre_dict[precondition.replaced_ID]

		for ante in antecedents:
			if ante.stepnumber == plan.initial_dummy_step.stepnumber:
				continue

			#step 1 - make a copy
			antestep = ante.deepcopy(replace_internals=True)
			eff = self.GL.getConsistentEffect(antestep, precondition)
			eff_link = antestep.RemoveSubgraph(eff)

			#step 2 - make a copy of the plan
			new_plan = plan.deepcopy()

			#step 3 - set sink before replace internals
			temp = eff.replaced_ID
			eff_link.sink = new_plan.getElementById(precondition.ID)
			eff_link.sink.replaced_ID = temp
			new_plan.edges.add(eff_link)

			#step 4 - add new stuff to new plan
			new_plan.elements.update(antestep.elements)
			new_plan.edges.update(antestep.edges)

			#step 5 - update orderings and causal links, add flaws
			self.addStep(new_plan,
						 s_add=antestep,
						 s_need=new_plan.getElementById(s_need.ID),
						 condition=Condition.subgraph(new_plan, eff_link.sink),
						 new=True)
			new_plan.flaws.addCndtsAndRisks(self.GL, antestep.root)

			#step 6 - add new_plan to open list
			results.add(new_plan)

		return results

	#@clock
	def reuse(self, plan, flaw):
		results = set()
		s_need, precondition = flaw.flaw

		#antecedents - a set of stepnumbers
		antecedents = self.GL.id_dict[precondition.replaced_ID]
		if len(antecedents) == 0:
			return set()

		for s_old in plan.Step_Graphs:
			if s_old.stepnumber not in antecedents:
				continue
			if s_old.root == s_need:
				continue

			#step 1 - make a copy of the plan, also replaces the plan number
			new_plan = plan.deepcopy()

			#step 2 - Actionize the steps from new_plan
			s_need_new = new_plan.getElementById(s_need.ID)

			#step 3-4 retarget precondition to be s_old effect
			pre_link_sink = self.RetargetPrecondition(self.GL, new_plan, s_old, precondition)
			Old = Action.subgraph(new_plan, new_plan.getElementById(s_old.ID))

			#step 5 - add orderings, causal links, and create flaws
			self.addStep(new_plan, Old, s_need_new,
						 condition=Condition.subgraph(new_plan, pre_link_sink),
						 new=False)

			#step 6 - add new plan to open list
			results.add(new_plan)

		return results

	def RetargetPrecondition(self, GL, plan, S_Old, precondition):
		effect_token = GL.getConsistentEffect(S_Old, precondition)

		if S_Old.is_decomp:
			Eff = list(Condition.subgraph(S_Old, effect_token).Args)
			Pre = precondition.Args
			if not isIdenticalElmsInArgs(Pre, Eff):
				return False

		# for Eff in S_Old.Effects:
		# 	if Eff.Args == precondition.Args:
		# 		effect_token = Eff.root
		# 		break
		#effect_token = GL.getConsistentEffect(S_Old, precondition)

		pre_link = plan.RemoveSubgraph(precondition.root)
		#push
		plan.edges.remove(pre_link)
		#mutate
		pre_link.sink = effect_token
		#pop
		plan.edges.add(pre_link)

		return pre_link.sink

	def addStep(self, plan, s_add, s_need, condition, new=None):
		"""
			when a step is added/reused,
			add causal link and ordering edges (including to dummy steps)
			If step is new, add open precondition flaws for each precondition
		"""
		if new is None:
			new = False

		if s_add.stepnumber != plan.initial_dummy_step.stepnumber:
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_add.root)
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_need)

		if s_need.stepnumber != plan.final_dummy_step.stepnumber:
			plan.OrderingGraph.addEdge(s_add.root, plan.final_dummy_step)
			plan.OrderingGraph.addEdge(s_need, plan.final_dummy_step)

		#Always add this ordering
		plan.OrderingGraph.addEdge(s_add.root, s_need)
		plan.CausalLinkGraph.addEdge(s_add.root, s_need, condition)

		if new:
			for Prec in s_add.Preconditions:
				plan.flaws.insert(self.GL, plan, Flaw((s_add.root, Prec), 'opf'))
		plan.lastAdded = s_add
		s_add.Effects

		return plan

	#@clock
	def resolveThreatenedCausalLinkFlaw(self, plan, flaw):
		"""
			Promotion: Add ordering from sink to threat, and check if cycle
			Demotion: Add ordering from threat to source, and check if cycle
		"""
		results = set()
		threat, causal_link = flaw.flaw

		#Promotion
		promotion = plan.deepcopy()
		promotion.OrderingGraph.addEdge(causal_link.sink, threat)
		if promotion.OrderingGraph.isInternallyConsistent():
			results.add(promotion)


		#Demotion
		demotion = plan.deepcopy()
		demotion.OrderingGraph.addEdge(threat, causal_link.source)
		if demotion.OrderingGraph.isInternallyConsistent():
			results.add(demotion)

		return results

	def generateChildren(self, plan, flaw):

		if flaw.name == 'opf':
			results = self.reuse(plan, flaw)
			results.update(self.newStep(plan, flaw))
		elif flaw.name == 'tclf':
			results = self.resolveThreatenedCausalLinkFlaw(plan, flaw)
			return results
		else:
			raise ValueError('whose flaw is it anyway {}?'.format(flaw))

		#if len(results) == 0:
		#	print(flaw)

		for result in results:
			new_flaws = result.detectThreatenedCausalLinks(self.GL)
			for nf in new_flaws:
				result.flaws.insert(self.GL, result, nf)

		return results


	@clock
	def POCL(self, num_plans=5):
		completed = []
		visited = 0

		while len(self) > 0:

			print(visited, len(self)+visited)
			#Select child
			#print(self._frontier)

			plan = self.pop()
			#print('\n selecting plan: {}'.format(plan))
			#print(plan.flaws)

			visited += 1

			if not plan.isInternallyConsistent():
				continue

			if len(plan.flaws) == 0:
				print('\nsolution found at {} nodes expanded and {} nodes visited'.format(visited, len(self)+visited))
				completed.append(plan)
				if len(completed) == num_plans:
					print('\n')
					return completed
				for step in topoSort(plan):
					print(Action.subgraph(plan, step))
				continue

			#Select Flaw
			flaw = plan.flaws.next()
#			print('{} selected : {}\n'.format(flaw.name, flaw))
		#	if flaw.name == 'tclf':
		#		print('{} selected : {}\n'.format(flaw.name, flaw))
			#	print(plan.flaws)

			#Add children to Open List
			children = self.generateChildren(plan, flaw)

			#print('generated children: {}'.format(len(children)))
			for child in children:
				self.insert(child)


def topoSort(graph):
	OG = copy.deepcopy(graph.OrderingGraph)
	L =[]
	S = {graph.initial_dummy_step}
	while len(S) > 0:
		n = S.pop()
		L.append(n)
		for m_edge in OG.getIncidentEdges(n):
			OG.edges.remove(m_edge)
			if len({edge for edge in OG.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	return L


import unittest
class TestPlanner(unittest.TestCase):

	def testPlanner(self):
		from GlobalContainer import GC

		#domain = 'domains/ark-domain-decomp.pddl'
		#problem = 'domains/ark-problem-decomp.pddl'
		domain = 'domains/ark-domain.pddl'
		problem = 'domains/ark-problem.pddl'

		print('Reading {} and {}'.format(domain, problem))

		try:
			SGL = reload(domain + problem)
			GC.SGL = SGL
		except:
			SGL = GLib(domain, problem)
			GC.SGL = SGL

		pypocl = PlanSpacePlanner(SGL)
		results = pypocl.POCL(1)
		for R in results:
			print(R)
			for step in topoSort(R):
				print(Action.subgraph(R, step))

		print('\n\n')

if __name__ == '__main__':
	unittest.main()