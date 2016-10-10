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

	def __init__(self, story_objs, story_GL, disc_objects=None, disc_GL=None):
		#Assumes these parameters are already read from file

		self.story_objs = story_objs
		self.story_GL = story_GL

		SP = self.setup(self.story_GL, 'story')
		self.Open = Frontier()
		if disc_objects is not None:
			self.disc_GL = disc_GL
			self.disc_objects = disc_objects
			Discourse_Plans = self.multiGoalSetup(self.disc_GL, disc_objects)
			for DP in Discourse_Plans:
				self.Open.insert(BiPlan(SP.deepcopy(), DP))
		else:
			self.Open.insert(SP)

	def __len__(self):
		return len(self._frontier)

	def __getitem__(self, position):
		return self._frontier[position]

	def __setitem__(self, plan, position):
		self._frontier[position] = plan

	def setup(self, GL, plan_name):
		"""
			Create step typed element DI, with effect edges to each condition of start_set
			Create step typed element DG, with precondition edges to each condition of end_set
			Add ordering from DI to DG
		"""

		s_init = copy.deepcopy(GL[-2])
		s_init.replaceInternals()
		s_goal = copy.deepcopy(GL[-1])
		s_goal.replaceInternals()

		s_init_plan = PlanElementGraph(uid(0), name=plan_name, Elements=self.story_objs|s_init.elements|s_goal.elements,
									   Edges=s_init.edges|s_goal.edges)

		s_init_plan.initial_dummy_step = s_init.root
		s_init_plan.final_dummy_step = s_goal.root

		s_init_plan.OrderingGraph.addOrdering(s_init.root, s_goal.root)

		#Add initial Open precondition flaws for dummy step
		init_flaws = (Flaw((s_goal.root, prec), 'opf') for prec in s_goal.preconditions)
		for flaw in init_flaws:
			s_init_plan.flaws.insert(GL, s_init_plan, flaw)
		return s_init_plan

	def multiGoalSetup(self, GL, disc_objects):
		#s_init is in the back for a multi-goal setup
		init = copy.deepcopy(GL[-1])
		init.replaceInternals()
		DPlans = []
		for GA in GL.Goal_Actions:
			s_goal = copy.deepcopy(GA)
			s_init = copy.deepcopy(init)
			DPlan = PlanElementGraph(uid(0), name='disc',
									 Elements=s_init.elements | s_goal.elements | self.story_objs | disc_objects,
									 Edges=s_init.edges | s_goal.edges)

			DPlan.initial_dummy_step = s_init.root
			DPlan.final_dummy_step = s_goal.root
			DPlan.OrderingGraph.addOrdering(s_init.root, s_goal.root)
			init_flaws = (Flaw((s_goal.root, prec), 'opf') for prec in s_goal.preconditions)
			for flaw in init_flaws:
				DPlan.flaws.insert(GL, DPlan, flaw)
			DPlans.append(DPlan)
		return DPlans


	#@clock
	def newStep(self, plan, flaw, GL):
		"""
		@param plan:
		@param flaw:
		@return:
		"""

		results = set()
		s_need, precondition = flaw.flaw

		#antecedent is of the form (antecedent_action_with_missing_eff_link, eff_link)
		antecedents = GL.pre_dict[precondition.replaced_ID]
		#print('flaw precondition.replaced_ID: {}'.format(precondition.replaced_ID))
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
			preserve_original_id = eff_link.sink.replaced_ID #original
			#anteaction.assign(eff_link.sink, new_plan.getElementById(precondition.ID)) #new
			eff_link.sink.replaced_ID = preserve_original_id #original
			eff_link.sink = new_plan.getElementById(precondition.ID)
			new_plan.edges.add(eff_link)
			# check: eff_link.sink should till be precondition of s_need

			#step 5 - add new stuff to new plan
			new_plan.elements.update(anteaction.elements)
			new_plan.edges.update(anteaction.edges)

			#step 6 - update orderings and causal links, add flaws
			self.addStep(new_plan, anteaction.root, new_plan.getElementById(s_need.ID), eff_link.sink, GL, new=True)
			try:
				new_plan.flaws.addCndtsAndRisks(GL, anteaction.root)
			except:
				print('ok')

			#step 7 - add new_plan to open list
			results.add(new_plan)

		return results

	#@clock
	def reuse(self, plan, flaw, GL):
		results = set()
		s_need, precondition = flaw.flaw

		#antecedents - a set of stepnumbers
		antecedents = GL.id_dict[precondition.replaced_ID]
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
			pre_link_sink = self.RetargetPrecondition(GL, new_plan, S_Old, precondition)

			#step 5 - add orderings, causal links, and create flaws
			self.addStep(new_plan, S_Old.root, S_Need.root, pre_link_sink, GL, new=False)

			#step 6 - add new plan to open list
			results.add(new_plan)

		return results

	def RetargetPrecondition(self, GL, plan, S_Old, precondition):
		effect_token = GL.getConsistentEffect(S_Old, precondition)
		pre_link = plan.RemoveSubgraph(precondition)
		#plan.assign(pre_link.sink, effect_token) #new
		plan.edges.remove(pre_link)
		pre_link.sink = effect_token
		plan.edges.add(pre_link)
		return pre_link.sink

	def addStep(self, plan, s_add, s_need, condition, GL, new=None):
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
				plan.flaws.insert(GL, plan, Flaw((s_add, prec.sink), 'opf'))

		if plan.name == 'disc':
			plan.flaws.insert(GL, plan, Flaw(s_add.stepnumber, 'dcf'))

		#Good time as ever to updatePlan
		#plan.updatePlan()
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


	def generateChildren(self, plan, k, flaw):
		#results = set()
		if k == 0:
			kplan = plan.S
			other = plan.D
			GL = self.story_GL
		else:
			kplan = plan.D
			other = plan.S
			GL = self.disc_GL

		if flaw.name == 'opf':
			results = self.reuse(kplan, flaw, GL)
			results.update(self.newStep(kplan, flaw, GL))
		elif flaw.name == 'tclf':
			results = self.resolveThreatenedCausalLinkFlaw(kplan, flaw)
		elif flaw.name == 'dcf':
			results = other.Integrate(GL[flaw.flaw].ground_subplan.deepcopy())
			GL = self.story_GL
			other = plan.D
		else:
			raise ValueError('whose flaw is it anyway {}?'.format(flaw))

		nBiPlans = set()
		for result in results:
			new_flaws = result.detectThreatenedCausalLinks(GL)
			result.flaws.threats.update(new_flaws)
			nBiPlans.add(BiPlan(result, other.deepcopy()))

		return nBiPlans


	@clock
	def POCL(self, num_plans = 5):
		Completed = []
		visited = 0
		#Visited = []

		while len(self.Open) > 0:

			#Select child
			plan = self.Open.pop()

			visited+=1

			if not plan.isInternallyConsistent():
				#print('branch terminated')
				continue

			#for step in topoSort(plan):
				#print(Action.subgraph(plan, step))

			if plan.num_flaws() == 0:
				print('story + disc solution found at {} nodes visited and {} nodes expanded'.format(visited,
																								len(self.Open)))
				Completed.append(plan)
				if len(Completed) == num_plans:
					return Completed
				continue
			elif len(plan.S.flaws) == 0:
				print('story solution found at {} nodes visited and {} nodes expanded'.format(visited, len(self.Open)))
			elif len(plan.D.flaws) == 0:
				print('disc solution found at {} nodes visited and {} nodes expanded'.format(visited, len(self.Open)))

			#print(plan)
			#print(plan.flaws)

			#Select Flaw
			k, flaw = plan.next_flaw()
			#print('selected : {}\n'.format(flaw))

			#Add children to Open List
			children = self.generateChildren(plan, k, flaw)

			#print('generated children: {}'.format(len(children)))
			for child in children:
				self.Open.insert(child)

			#print('open list number: {}'.format(len(self.Open)))
			#print('\n')


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
		operators, objects, initAction, goalAction = parseDomAndProb(domain_file, problem_file)
		obtypes = Argument.object_types


		print('preprocessing...')
		preprocess=False
		if preprocess:
			GL = GLib(op_graphs, objects, obtypes, initAction, goalAction)
			print(len(GL))
		else:
			try:
				print('try to reload:')
				GL = reload('SGL')
				print(len(GL))
			except:
				print('could not reload')
				GL = GLib(op_graphs, objects,obtypes, initAction, goalAction)

		planner = PlanSpacePlanner(operators, objects, GL)

		n = 6
		print('\nRunning Story Planner on ark-domain and problem to find {} solutions'.format(n))

		results = planner.POCL(n)
		assert len(results) == n
		for result in results:
			print('\n')
			print('Story')
			for step in topoSort(S):
				print(Action.subgraph(S, step))
			print('Discourse')
			for step in topoSort(D):
				print(Action.subgraph(D, step))
		print('\n\n')
		pass



	def testDecomp(self):
		from GlobalContainer import GC

		print('Reading ark-domain and ark-problem')
		story = parseDomAndProb('domains/ark-domain.pddl', 'domains/ark-problem.pddl')
		# (op_graphs, objects, GC.object_types, init, goal)

		try:
			SGL = reload('SGL')
			GC.SGL = SGL
		except:
			SGL = GLib(*story)
			GC.SGL = SGL

		print('Reading ark-requirements-domain and ark-requirements-problem')
		disc = parseDomAndProb('domains/ark-requirements-domain.pddl', 'domains/ark-requirements-problem.pddl')
		# (op_graphs, objects, GC.object_types, init, goal)

		try:
			DGL = reload('DGL')
			GC.DGL = DGL
		except:
			DGL = GLib(*disc, storyGL=SGL)
			GC.DGL = DGL

		bi = PlanSpacePlanner(story[1], SGL, disc[1], DGL)
		results = bi.POCL(5)
		for R in results:
			S = R.S
			D = R.D
			print('\n')
			print('Story')
			for step in topoSort(S):
				print(Action.subgraph(S, step))
			print('Discourse')
			for step in topoSort(D):
				print(Action.subgraph(D, step))

		print('\n\n')

if __name__ ==  '__main__':
	tp = TestPlanner()
	tp.testDecomp()
	#unittest.testDecomp()
	#unittest.main()