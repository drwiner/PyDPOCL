#from pddlToGraphs import *
import collections
import bisect
from Graph import isConsistentEdgeSet

#from PlanElementGraph import Condition
#import PlanElementGraph
"""
	Flaws for plan element graphs
"""

class Flaw:
	def __init__(self, tuple, name):
		self.name = name
		self.flaw = tuple
		self.cndts = 0
		self.risks = 0
		self.criteria = self.cndts

	def __hash__(self):
		return hash(self.flaw)
		
	def __eq__(self, other):
		return hash(self) == hash(other)

	#For comparison via bisect
	def __lt__(self, other):
		return self.criteria < other.criteria

	#switch to risks for unsafe flaws
	def switch(self):
		if self.criteria == self.cndts:
			self.criteria = self.risks
		else:
			self.criteria = self.cndts

		return self

		
	def __repr__(self):
		return 'Flaw(name={},tuple={})'.format(self.name, self.flaw)


class Flawque:
	""" A deque which pretends to be a set, and keeps everything sorted"""

	def __init__(self):
		self._flaws = collections.deque()

	def add(self, flaw):
		self.insert(flaw)
		#self._flaws.append(item)

	def update(self, iter):
		for flaw in iter:
			self.insert(flaw)

	def __contains__(self, item):
		return item in self._flaws

	def __len__(self):
		return len(self._flaws)

	def head(self):
		return self._flaws.popleft()

	def tail(self):
		return self._flaws.pop()

	def pop(self):
		return self._flaws.pop()

	def peek(self):
		return self._flaws[-1]

	def insert(self, flaw):
		index = bisect.bisect_left(self._flaws, flaw)
		self._flaws.rotate(-index)
		self._flaws.appendleft(flaw)
		self._flaws.rotate(index)

	def __getitem__(self, position):
		return self._flaws[position]

	def __repr__(self):
		return str(self._flaws)

class simpleQueueWrapper(collections.deque):
	def add(self, item):
		self.append(item)
	def pop(self):
		return self.popleft()
	def update(self, iter):
		for it in iter:
			self.append(it)

class FlawLib():
	non_static_preds = set()
	def __init__(self):
		"""TODO: need way to manage multiple sets which have preference ranking and different ordering criterion (
		 LR/MW-first/LIFO)"""

		#self.non_static_preds = non_static_preds

		#static = unchangeable (should do oldest first.)
		self.statics = simpleQueueWrapper()

		#init = established by initial state
		self.inits = simpleQueueWrapper()

		#threat = causal link dependency undone
		self.threats = simpleQueueWrapper()

		#unsafe = existing effect would undo
		#		sorted by number of cndts
		self.unsafe = Flawque()

		#reusable = open conditions consistent with at least one existing effect
		#		sorted by number of cndts
		self.reusable = Flawque()

		#nonreusable = open conditions inconsistent with existing effect
		#		sorted by number of cndts
		self.nonreusable = Flawque()

		self.typs = [self.statics, self.inits, self.threats, self.unsafe, self.reusable, self.nonreusable]
	#	self.typs = [self.sub_library, self.threats, self.unsafe, self.reusable, self.nonreusable]

		#cndts is a dictionary mapping open conditions to candidate action effects
		self.cndts = collections.defaultdict(set)

		#risks is a dictionary mapping open conditions to potential undoing (i.e., unsafe)
		# 		Can we use this to limit search for threatened causal link flaws?
		self.risks = collections.defaultdict(set)

	def __len__(self):
		return sum(len(flaw_set) for flaw_set in self.typs)
	#	return len(self.threats) + len(self.unsafe) + len(self.statics) + len(self.reusable) + len(self.nonreusable)

	def __contains__(self, flaw):
		for flaw_set in self.typs:
			if flaw in flaw_set:
				return True
		return False
	#	return flaw in self.threats or flaw in self.unsafe or flaw in self.nonreusable or flaw in self.reusable or \
	#		   flaw in self.statics

	def OCs(self):
		''' Generator for open conditions'''
		for flaw_set in self.typs:
			if flaw_set == self.threats:
				continue
			g = (flaw for flaw in flaw_set)
			yield(next(g))

	def next(self):
		''' Returns flaw with highest priority, and removes'''
		for flaw_set in self.typs:
			if len(flaw_set) > 0:
				return flaw_set.pop()
		return None

	def addCndtsAndRisks(self, graph, action):
		""" For each effect of Action, add to open-condition mapping if consistent"""

		for eff in graph.getNeighborsByLabel(action, 'effect-of'):
			Effect = graph.subgraph(eff)
			for oc in self.OCs():
				s_need, pre = oc.flaw

				# fogetaboutit if effect cannot be established before s_need
				if graph.OrderingGraph.isPath(s_need, action):
					continue

				# if not eff.isConsistent(pre), eval if not-eff is consistent with pre.
				if evalRisk(graph, eff, pre, Effect, self.risks[oc].add):
					continue

				# check if Effect can match edges with Precondition, check against restrictions
				Precondition = graph.subgraph(pre)
				if Effect.isConsistentSubgraph(Precondition):
					self.cndts[oc].add(eff)

	def insert(self, graph, flaw):
		''' for each effect of an existing step, check and update mapping to consistent effects'''

		if flaw.name == 'tclf':
			self.threats.add(flaw)
			return

		#First, determine if this flaw.flaw[1].name is in non_static_preds: if not, then let cndts be just those
		# initial states with same predicate
		s_need, pre = flaw.flaw
		if not pre.name in FlawLib.non_static_preds:
			self.cndts[flaw].update({g for g in graph.getNeighbors(graph.initial_dummy_step) if g.name == pre.name})
			flaw.cndts = len(self.cndts[flaw])
			self.statics.add(flaw)
			return

		#Determine existing Cdnts and Risks for this flaw
		Precondition = graph.subgraph(pre)
		Cndts = graph.getEdgesByLabel('effect-of')
		for edge in Cndts:

			if s_need == edge.source:
				continue

			#fogetaboutit if effect cannot be established before s_need
			if graph.OrderingGraph.isPath(s_need, edge.source):
				continue

			eff = edge.sink

			#if not eff.isConsistent(pre), eval if not-eff is consistent with pre.
			if evalRisk(graph, eff, pre, Precondition, self.risks[flaw].add):
				continue

			#check if Effect can match edges with Precondition, check against restrictions
			Effect = graph.subgraph(eff)
			if Effect.isConsistentSubgraph(Precondition):
				self.cndts[flaw].add(eff)

		#Bin flaw into right list
		flaw.cndts = len(self.cndts[flaw])
		flaw.risks = len(self.risks[flaw])

		# for any cndt, if establishing step is initial, then flaw is static {t}
		if flaw.cndts > 0:
			for eff in self.cndts[flaw]:
				parent = graph.getEstablishingParent(eff)
				if parent.name == 'dummy_init':
					if isConsistentEdgeSet(Rem = graph.subgraph(eff).edges, Avail = Precondition.edges):
						self.inits.add(flaw)
						return

		#if has risks, then unsafe
		if flaw.risks > 0:
			self.unsafe.insert(flaw.switch())
			return

		#if not static but has cndts, then reusable
		if flaw.cndts > 0:
			self.reusable.insert(flaw)
			return

		#last, must be nonreusable
		self.nonreusable.add(flaw)

	def __repr__(self):
		#flaw_str_list = [str([flaw for flaw in flaw_set]) for flaw_set in self.typs]

		statics = str([flaw for flaw in self.statics])
		inits = str([flaw for flaw in self.inits])
		threats = str([flaw for flaw in self.threats])
		unsafe = str([flaw for flaw in self.unsafe])
		reusable = str([flaw for flaw in self.reusable])
		nonreusable = str([flaw for flaw in self.nonreusable])
	#	return '\nFLAW LIBRARY: \n' + [flaw_set for flaw_set in flaw_str_list] + '\n'
		return '\nFLAW LIBRARY: \nstatics:  \n' + statics + '\ninits: \n' + inits + '\nthreats: \n' + threats + '\nunsafe: \n' +  unsafe + '\nreusable: \n' + reusable + '\nnonreusable: \n' + nonreusable + '\n'


def evalRisk(graph, eff, pre, ExistingGraph, operation):
	""" Returns True if not consistent, returns False if consistent"""

	if not eff.isConsistent(pre):

		#if its not consistent but has same name, then they have different truths
		if pre.name == eff.name:

			#Leverages the fact that there is an Existing Graph, instead of rebuilding
			if ExistingGraph.root == eff:
				R = graph.subgraph(pre)
			else:
				R = graph.subgraph(eff)

			#whichever it is, has to be opposite
			R.root.truth = not eff.truth

			#match edges if consistent, check against restrictions
			if R.isConsistentSubgraph(ExistingGraph):
				operation(eff)
		return True
	return False


# class FlawLibQue(collections.deque):
# 	""" A deque where each item is a flaw library"""
# 	@property
# 	def flaws(self):
# 		return sum(len(flaws) for flaws in self)
#
# 	@property
# 	def reusableFlaws(self):
# 		return sum(len(flaws.reusable) for flaws in self)
#
# 	@property
# 	def heuristic(self):
# 		return self.flaws + self.reusableFlaws
#
# 	def addCndtsAndRisks(self, graph, action):
# 		for flaws in self:
# 			flaws.addCndtsAndRisks(graph, action)

import unittest
class TestOrderingGraphMethods(unittest.TestCase):

	def test_flaw_counter(self):
		A = Flaw(('a'), 'A')
		A.cndts = 12
		B = Flaw(('b'), 'B')
		B.cndts = 11
		print(Flaw.counter) #0
		Flaw.counter+= 1
		print(Flaw.counter) #1
		print(B.counter) #0
		B.cndts = Flaw.counter
		B.cndts +=1
		print(B.cndts) #2
		print(Flaw.counter) #1


if __name__ ==  '__main__':
	unittest.main()


"""
An open precondition flaw is a tuple <step element, precondition element>
	where precondition element is a literal element,
	there is a precondition edge from the step element to the precondition element,
	and there is no causal link in the graph from another step to the precondition element with label 'effect'
	It's important to consider this last point
		because with this approach, you could instantiate an element which already has some preconditions in causal links

		********Consider above for resolve "uninstantiated step flaw"
"""
