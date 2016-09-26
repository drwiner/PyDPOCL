#from pddlToGraphs import *
import collections
import bisect
from Graph import isConsistentEdgeSet

import itertools
from clockdeco import clock
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
		self.heuristic = 0

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
		return 'Flaw({}, h={}'.format(self.flaw, self.heuristic)


class Flawque:
	""" A deque which pretends to be a set, and keeps everything sorted"""

	def __init__(self):
		self._flaws = collections.deque()
	#	self._name = name

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
	#def __init__(self, name):
		#super(simpleQueueWrapper, self).__init__()
		#self._name = name
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

		#static = unchangeable (should do oldest first.)
		self.statics = simpleQueueWrapper()

		#init = established by initial state
		self.inits = simpleQueueWrapper()

		#threat = causal link dependency undone
		self.threats = simpleQueueWrapper()

		#unsafe = existing effect would undo sorted by number of cndts
		self.unsafe = Flawque()

		#reusable = open conditions consistent with at least one existing effect sorted by number of cndts
		self.reusable = Flawque()

		#nonreusable = open conditions inconsistent with existing effect sorted by number of cndts
		self.nonreusable = Flawque()

		self.typs = [self.statics, self.inits, self.threats, self.unsafe, self.reusable, self.nonreusable]

	@property
	def heuristic(self):
		value = 0
		for i,flaw_set in enumerate(self.typs):
			if i == 2:
				continue
			value+=i*len(flaw_set)
		return value

	def __len__(self):
		return sum(len(flaw_set) for flaw_set in self.typs)
	#	return len(self.threats) + len(self.unsafe) + len(self.statics) + len(self.reusable) + len(self.nonreusable)

	def __contains__(self, flaw):
		for flaw_set in self.typs:
			if flaw in flaw_set:
				return True
		return False

	@property
	def flaws(self):
		return [flaw  for i, flaw_set in enumerate(self.typs) for flaw in flaw_set if i != 2]


	def OCs(self):
		''' Generator for open conditions'''
		for i, flaw_set in enumerate(self.typs):
			if len(flaw_set) == 0:
				continue
			if i == 2:
				continue
			g = (flaw for flaw in flaw_set)
			yield(next(g))

	def next(self):
		''' Returns flaw with highest priority, and removes'''
		for flaw_set in self.typs:
			if len(flaw_set) > 0:
				return flaw_set.pop()
		return None

	def addCndtsAndRisks(self, GL, action):
		""" For each effect of Action, add to open-condition mapping if consistent"""

		for oc in self.OCs():
			s_need, pre = oc.flaw

			# step numbers of antecdent types
			if action.stepnumber in GL.id_dict[pre.replaced_ID]:
				oc.cndts += 1

			# step numbers of threatening steps
			elif action.stepnumber in GL.threat_dict[s_need.stepnumber]:
				oc.risks += 1


	def insert(self, GL, plan, flaw):
		''' for each effect of an existing step, check and update mapping to consistent effects'''

		if flaw.name == 'tclf':
			self.threats.add(flaw)
			return

		#unpack flaw
		s_need, pre = flaw.flaw

		#if pre.predicate is static
		if not pre.name in FlawLib.non_static_preds:
			self.statics.add(flaw)
			return

		#Eval number of existing candidates
		ante_nums = GL.id_dict[pre.replaced_ID]
		risk_nums = GL.threat_dict[s_need.replaced_ID]

		for step in plan.Steps:
			#defense
			if step == s_need:
				continue
			if plan.OrderingGraph.isPath(s_need, step):
				continue
			if step.stepnumber in ante_nums:
				flaw.cndts += 1
				if step.name == 'dummy_init':
					self.inits.add(flaw)
			if step.replaced_ID in risk_nums:
				flaw.risks += 1

		if flaw in self.inits:
			return

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
