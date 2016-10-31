from pddlToGraphs import parseDomAndProb
from Plan import Plan, Action, Condition
from Flaws import Flaw, DCF
from heapq import heappush, heappop
from clockdeco import clock
from Ground import reload, GLib
from Graph import Edge, isIdenticalElmsInArgs, retargetElmsInArgs, retargetArgs
from Plannify import Unify
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

		s_init = self.GL[-2].deepcopy(replace_internals=True)
		s_goal = self.GL[-1].deepcopy(replace_internals=True)


		s_init_plan = Plan(name=plan_name)

		s_init_plan.initial_dummy_step = s_init.root
		s_init_plan.final_dummy_step = s_goal.root
		s_init_plan.append(s_init)
		s_init_plan.append(s_goal)


		s_init_plan.OrderingGraph.addOrdering(s_init.root, s_goal.root)

		#Add initial Open precondition flaws for dummy step
		#init_flaws = (Flaw((s_goal.root, prec), 'opf') for prec in s_goal.Preconditions)
		#for flaw in init_flaws:
		for prec in s_goal.Preconditions:
			s_init_plan.flaws.insert(self.GL, s_init_plan, Flaw((s_goal.root, prec), 'opf'))

		s_init_plan.flaws.addCndtsAndRisks(self.GL, s_init)
		return s_init_plan


	#@clock
	def newStep(self, plan, flaw):
		results = set()
		s_need, pre = flaw.flaw

		antecedents = self.GL.cndt_dict[pre.litnumber]
		for antenum in antecedents:
			ante = self.GL[antenum]
			if ante.stepnumber == plan.initial_dummy_step.stepnumber:
				continue

			new_plan = plan.deepcopy()
			s_add = ante.deepcopy(replace_internals=True)
			new_plan.append(s_add)
			if s_add.is_decomp:
				eff = s_add.getElmByRID(pre.replaced_ID)
				pass
				#eargs = list(eff.Args)
				#retargetArgs(antestep, eff.Args, pre.Args)
				#retargetElmsInArgs(antestep.ground_subplan, eff.Args, pre.Args)
			#eff = self.IntegrateNewStep(new_plan, antestep, precondition)

			#add step, orderings and causal links, add flaws
			new_s_need = new_plan[s_need.index]
			new_link_condition = new_s_need.Preconditions[pre.index]
			self.addStep(new_plan, s_add, new_s_need, new_link_condition, new=True)

			new_plan.flaws.addCndtsAndRisks(self.GL, s_add)

			results.add(new_plan)

		return results

	def IntegrateNewStep(self, new_plan, antestep, precondition):
		eff = self.GL.getConsistentEffect(antestep, precondition)

		if antestep.is_decomp:
			PArgs = list(precondition.Args)
			EArgs = list(Condition.subgraph(antestep, eff).Args)
			retargetArgs(antestep, EArgs, PArgs)
			retargetElmsInArgs(antestep.ground_subplan, EArgs, PArgs)
			to_add = set()
			for link in list(antestep.ground_subplan.CausalLinkGraph.edges):
				to_add.add(Edge(link.source, link.sink, Condition.subgraph(antestep.ground_subplan, link.label)))
			antestep.ground_subplan.CausalLinkGraph.edges = to_add
			new_plan.flaws.insert(self.GL, new_plan, DCF(antestep.ground_subplan, 'dcf'))

		eff_link = antestep.RemoveSubgraph(eff)
		eff_link.sink = new_plan.get_by_id(precondition.root.ID)
		eff_link.sink.replaced_ID = eff.replaced_ID
		new_plan.edges.add(eff_link)
		new_plan.elements.update(antestep.elements)
		new_plan.edges.update(antestep.edges)
		return eff_link.sink

	#@clock
	def reuse(self, plan, flaw):
		results = set()
		s_need, pre = flaw.flaw

		#antecedents - a set of stepnumbers
		antecedents = self.GL.cndt_dict[pre.litnumber]
		if len(antecedents) == 0:
			return set()

		for i, s_old in enumerate(plan.Steps):
			if s_old.stepnumber not in antecedents:
				continue
			if s_old == s_need:
				continue

			new_plan = plan.deepcopy()
			s_add = new_plan[i]
			#Old = Action.subgraph(new_plan, s_old)
			#effect_token = Old.getElmByRID(pre.replaced_ID)#self.GL.getConsistentEffect(Old, precondition)
			#joint_literal = self.RetargetPrecondition(self.GL, new_plan, Old, precondition)

			if s_add.is_decomp or s_need.is_decomp:
				eff = next(iter(eff for eff in s_add.Effects if eff.replaced_ID == pre.replaced_ID))
				if not isIdenticalElmsInArgs(pre.Args, eff.Args):
					continue
				else:
					print("not identical")

			#effect_edge = new_plan.ReplaceSubgraphs(precondition.root, effect_token)

			#add step, orderings, causal links, and create flaws
			new_s_need = new_plan[s_need.index]
			new_link_condition = new_s_need.Preconditions[pre.index]
			self.addStep(new_plan, s_add, new_s_need, new_link_condition, new=False)

			results.add(new_plan)

		return results

	def addStep(self, plan, s_add, s_need, condition, new=None):
		if new is None:
			new = False

		if s_add.stepnumber == 72:
			pass

		if s_add.stepnumber != plan.initial_dummy_step.stepnumber:
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_add.root)
			plan.OrderingGraph.addEdge(plan.initial_dummy_step, s_need.root)
		else:
			pass

		if s_need.stepnumber != plan.final_dummy_step.stepnumber:
			plan.OrderingGraph.addEdge(s_add.root, plan.final_dummy_step)
			plan.OrderingGraph.addEdge(s_need.root, plan.final_dummy_step)
		else:
			pass

		#Always add this ordering
		plan.OrderingGraph.addEdge(s_add.root, s_need.root)
		new_link = plan.CausalLinkGraph.addEdge(s_add.root, s_need.root, condition)
		new_tclfs = plan.detectTCLFperCL(self.GL, new_link)

		if new:

			for Prec in s_add.Preconditions:
				plan.flaws.insert(self.GL, plan, Flaw((s_add.root, Prec), 'opf'))
			#only detect for new steps if adding this step threatens causal link
			new_tclfs.update(plan.detectTCLFperStep(self.GL, s_add))

		for tclf in new_tclfs:
			plan.flaws.insert(self.GL, plan, tclf)

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
		elif flaw.name == 'dcf':
			results = Unify(plan, flaw.flaw, self.GL)
			for r in results:
				new_flaws = r.detectThreatenedCausalLinks(self.GL)
				for nf in new_flaws:
					r.flaws.insert(self.GL, r, nf)
		else:
			raise ValueError('whose flaw is it anyway {}?'.format(flaw))

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
			print(plan.cost, plan.heuristic)
			#print(plan)
			print(plan.flaws)
			#print('\n selecting plan: {}'.format(plan))
			#print(plan.flaws)

			visited += 1

			if not plan.isInternallyConsistent():
				print('pruned')
				print(plan)
				print(plan.flaws)
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
			print('{} selected : {}\n'.format(flaw.name, flaw))

		#	if flaw.name == 'tclf':
		#		print('{} selected : {}\n'.format(flaw.name, flaw))
			#	print(plan.flaws)

			#Add children to Open List
			children = self.generateChildren(plan, flaw)

			#print('generated children: {}'.format(len(children)))
			for child in children:
				self.insert(child)
		raise ValueError('Frontier is empty... no plan found')

def topoSort(graph):
	OG = copy.deepcopy(graph.OrderingGraph)
	L =[]
	S = {graph.initial_dummy_step}
	#L = list(graph.Steps)
	while len(S) > 0:
		n = S.pop()
		if n not in L:
			L.append(n)
		for m_edge in OG.getIncidentEdges(n):
			OG.edges.remove(m_edge)
			#if the sink has no other ordering sources, add it to the visited
			if len({edge for edge in OG.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)

	return L


import unittest
class TestPlanner(unittest.TestCase):

	def testPlanner(self):
		from GlobalContainer import GC

		domain = 'domains/ark-domain.pddl'
		problem = 'domains/ark-problem.pddl'
		#domain = 'domains/ark-domain-decomp.pddl'
		#problem = 'domains/ark-problem-decomp.pddl'
	#	domain = 'domains/ark-domain-decomp-two.pddl'
		#problem = 'domains/ark-problem-decomp-two.pddl'
		#domain = 'domains/ark-domain-decomp-three.pddl'
	#	problem = 'domains/ark-problem-outcomes.pddl'
	#	domain = 'domains/ark-domain-outcomes.pddl'
	#	domain = 'domains/h1.pddl'
	#	problem = 'domains/h1p1.pddl'

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
				print(R[step.index])

		print('\n\n')

if __name__ == '__main__':
	unittest.main()