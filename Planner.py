#from Flaws import *
from pddlToGraphs import *
import collections
from heapq import heappush, heappop
import itertools
from clockdeco import clock
from Ground import GLib


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


class PlanSpacePlanner:

	def __init__(self, story_objs, story_GL):
		#Assumes these parameters are already read from file

		self.story_objs = story_objs
		self.GL = story_GL

		SP = self.setup()
		self.Open = Frontier()
		self.Open.insert(SP)

	def __len__(self):
		return len(self._frontier)

	def __getitem__(self, position):
		return self._frontier[position]

	def __setitem__(self, plan, position):
		self._frontier[position] = plan

	def setup(self):
		"""
			Create step typed element DI, with effect edges to each condition of start_set
			Create step typed element DG, with precondition edges to each condition of end_set
			Add ordering from DI to DG
		"""

		s_init = copy.deepcopy(self.GL[-2])
		s_init.replaceInternals()
		s_goal = copy.deepcopy(self.GL[-1])
		s_goal.replaceInternals()

		s_init_plan = PlanElementGraph(uid(0), name='story', Elements=self.story_objs|s_init.elements|s_goal.elements,
									   Edges=s_init.edges|s_goal.edges)

		s_init_plan.initial_dummy_step = s_init.root
		s_init_plan.final_dummy_step = s_goal.root

		s_init_plan.OrderingGraph.addOrdering(s_init.root, s_goal.root)

		init_flaws = (Flaw((s_goal.root, prec), 'opf') for prec in s_goal.preconditions)
		for flaw in init_flaws:
			s_init_plan.flaws.insert(self.GL, s_init_plan, flaw)
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
			if ante.action.name == 'dummy_init':
				continue

			#step 1 - make a copy
			cndt = copy.deepcopy(ante)

			#step 2 - replace its internals, to distinguish from other identical antesteps
			(anteaction, eff_link) = cndt
			anteaction.replaceInternals()

			#step 3 - make a copy of the plan
			new_plan = plan.deepcopy()

			#step 4 - set sink before replace internals
			preserve_original_id = eff_link.sink.replaced_ID
			eff_link.sink.replaced_ID = preserve_original_id
			eff_link.sink = new_plan.getElementById(precondition.ID)
			new_plan.edges.add(eff_link)

			#step 5 - add new stuff to new plan
			new_plan.elements.update(anteaction.elements)
			new_plan.edges.update(anteaction.edges)

			#step 6 - update orderings and causal links, add flaws
			self.addStep(new_plan, anteaction.root, new_plan.getElementById(s_need.ID), eff_link.sink, new=True)
			new_plan.flaws.addCndtsAndRisks(self.GL, anteaction.root)

			#step 7 - add new_plan to open list
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

		for s_old in plan.Steps:
			if not s_old.stepnumber in antecedents:
				continue
			if s_old == s_need:
				continue

			#step 1 - make a copy of the plan, also replaces the plan number
			new_plan = plan.deepcopy()

			#step 2 - Actionize the steps from new_plan
			S_Old = Action.subgraph(new_plan, s_old)
			S_Need = Action.subgraph(new_plan, s_need)

			#step 3-4 retarget precondition to be s_old effect
			pre_link_sink = self.RetargetPrecondition(new_plan, S_Old, precondition)

			#step 5 - add orderings, causal links, and create flaws
			self.addStep(new_plan, S_Old.root, S_Need.root, pre_link_sink, new=False)

			#step 6 - add new plan to open list
			results.add(new_plan)

		return results

	#@clock
	def RetargetPrecondition(self, plan, S_Old, precondition):
		effect_token = self.GL.getConsistentEffect(S_Old, precondition)
		pre_link = plan.RemoveSubgraph(precondition)
		plan.edges.remove(pre_link)
		pre_link.sink = effect_token
		plan.edges.add(pre_link)
		return pre_link.sink

	#@clock
	def addStep(self, plan, s_add, s_need, condition, new=None):
		"""
			when a step is added/reused, 
			add causal link and ordering edges (including to dummy steps)
			If step is new, add open precondition flaws for each precondition
		"""
		if new is None:
			new = False

		if s_add != plan.initial_dummy_step:
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_add)
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_need)

		if s_need != plan.final_dummy_step:
			plan.OrderingGraph.addEdge(s_add, plan.final_dummy_step)
			plan.OrderingGraph.addEdge(s_need, plan.final_dummy_step)

		#Always add this ordering
		plan.OrderingGraph.addEdge(s_add, s_need)
		plan.CausalLinkGraph.addEdge(s_add, s_need, condition)

		if new:
			for prec in plan.getIncidentEdgesByLabel(s_add, 'precond-of'):
				plan.flaws.insert(self.GL, plan, Flaw((s_add, prec.sink), 'opf'))

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
		results.add(promotion)


		#Demotion
		demotion = plan.deepcopy()
		demotion.OrderingGraph.addEdge(threat, causal_link.source)
		results.add(demotion)

		return results

	#@clock
	def generateChildren(self, plan, flaw):
		if flaw.name == 'opf':
			results = self.reuse(plan, flaw)
			results.update(self.newStep(plan, flaw))
		elif flaw.name == 'tclf':
			results = self.resolveThreatenedCausalLinkFlaw(plan, flaw)
		else:
			raise ValueError('whose flaw is it anyway {}?'.format(flaw))

		for result in results:
			new_flaws = result.detectThreatenedCausalLinks(self.GL)
			result.flaws.threats.update(new_flaws)

		return results


	@clock
	def POCL(self, num_plans=5):
		Completed = []
		visited = 0
		#Visited = []

		while len(self.Open) > 0:

			#Select child
			plan = self.Open.pop()

			visited+=1

			if not plan.isInternallyConsistent():
				continue


			if len(plan.flaws) == 0:
				print('solution found at {} nodes expanded and {} nodes visited'.format(visited,
																						len(self.Open)+visited))
				Completed.append(plan)
				if len(Completed) == num_plans:
					return Completed
				continue

			#Select Flaw
			#print(plan.flaws)
			flaw = plan.flaws.next()
			#print('{} selected : {}\n'.format(flaw.name, flaw))

			#Add children to Open List
			children = self.generateChildren(plan, flaw)

			#print('generated children: {}'.format(len(children)))
			for child in children:
				self.Open.insert(child)
			#print('open:', len(self.Open))


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


import unittest

from Ground import reload, GLib
class TestPlanner(unittest.TestCase):
	def testArk(self):
		domain_file = 'domains/ark-domain.pddl'
		problem_file = 'domains/ark-problem.pddl'
		operators, objects, obtypes, initAction, goalAction = parseDomAndProb(domain_file, problem_file)

		print('preprocessing...')
		preprocess=False
		if preprocess:
			GL = GLib(operators, objects, obtypes, initAction, goalAction)
			print(len(GL))
		else:
			try:
				print('try to reload:')
				GL = reload('SGL')
				print(len(GL))
			except:
				print('could not reload')
				GL = GLib(operators, objects, obtypes, initAction, goalAction)
		from GlobalContainer import GC
		GC.SGL = GL
		planner = PlanSpacePlanner(objects, GL)

		n = 1
		print('\nRunning Story Planner on ark-domain and problem to find {} solutions'.format(n))

		results = planner.POCL(n)
		assert len(results) == n
		for result in results:
			print('\n')
			for step in topoSort(result):
				print(Action.subgraph(result, step))
		print('\n\n')
		pass

if __name__ ==  '__main__':
	unittest.main()