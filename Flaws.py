#from pddlToGraphs import *
import collections
import bisect
from uuid import uuid1, uuid4
from Graph import isConsistentEdgeSet

import itertools
from clockdeco import clock
#from PlanElementGraph import Condition
#import PlanElementGraph
"""
	Flaws for plan element graphs
"""

class Flaw:
	def __init__(self, f, name):
		self.name = name
		self.flaw = f
		self.cndts = 0
		self.risks = 0
		self.criteria = self.cndts
		self.heuristic = float('inf')
		if name == 'opf':
			self.tiebreaker = hash(f[1].replaced_ID)

	def __hash__(self):
		return hash(self.flaw)
		
	def __eq__(self, other):
		return hash(self) == hash(other)

	#For comparison via bisect
	def __lt__(self, other):
		if self.criteria != other.criteria:
			return self.criteria < other.criteria
		else:
			return self.tiebreaker < other.tiebreaker


	def setCriteria(self, flaw_type):
		if self.name == 'tclf':
			self.criteria = self.flaw[0].stepnumber
			self.tiebreaker = hash(self.flaw[1].label.replaced_ID) + self.flaw[1].sink.stepnumber
		elif flaw_type == 'unsafe':
			self.criteria = self.risks
		elif flaw_type in {'inits', 'statics', 'nonreusable'}:
			self.criteria = self.heuristic

	def __repr__(self):
		return 'Flaw({}, h={}, criteria={}, tb={})'.format(self.flaw, self.heuristic, self.criteria, self.tiebreaker)

class TCLF(Flaw):
	def __init__(self, f, name):
		super(TCLF, self).__init__(f, name)
		self.threat = self.flaw[0]
		self.link = self.flaw[1]
		self.criteria = self.threat.stepnumber
		self.tiebreaker = hash(self.link.label.replaced_ID) + self.link.sink.stepnumber

	def __hash__(self):
	 	return self.threat.stepnumber*1000 + self.link.source.stepnumber + self.link.sink.stepnumber + hash(
			self.link.label.replaced_ID)

class DCF(Flaw):
	def __init__(self, f, name):
		super(DCF, self).__init__(f, name)
		self.criteria = len(f.Steps)
		self.tiebreaker = f.root.stepnumber
	def __repr__(self):
		steps = [''.join(str(step) + ', ' for step in self.flaw.Step_Graphs)]
		return 'DCF(' + ''.join(['{}'.format(step) for step in steps]) + 'criteria ={}, tb={})'.format(
			self.criteria, self.tiebreaker)

class Flawque:
	""" A deque which pretends to be a set, and keeps everything sorted, highest-value first"""

	def __init__(self, name=None):
		self._flaws = collections.deque()
		self.name = name

	def add(self, flaw):
		flaw.setCriteria(self.name)
		self.insert(flaw)
		#self._flaws.append(item)

	def update(self, iter):
		for flaw in iter:
			self.add(flaw)

	def __contains__(self, item):
		return item in self._flaws

	def __len__(self):
		return len(self._flaws)

	def removeDuplicates(self):
		self._flaws = collections.deque(set(self._flaws))

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
		#self.name = name
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
		self.statics = Flawque('statics')

		#init = established by initial state
		self.inits = Flawque('inits')

		#decomps - decompositional ground subplans to add
		self.decomps = Flawque('decomps')

		#threat = causal link dependency undone
		self.threats = Flawque('threats')

		#unsafe = existing effect would undo sorted by number of cndts
		self.unsafe = Flawque('unsafe')

		#reusable = open conditions consistent with at least one existing effect sorted by number of cndts
		self.reusable = Flawque('reusable')

		#nonreusable = open conditions inconsistent with existing effect sorted by number of cndts
		self.nonreusable = Flawque('nonreusable')

		self.typs = [self.statics, self.inits, self.threats, self.decomps, self.unsafe, self.reusable, self.nonreusable]
		self.restricted_names = ['threats', 'decomps']

	# @property
	# def heuristic(self):
	# 	value = 0
	# 	for i, flawques in enumerate(self.typs):
	# 		if flawques.name in self.restricted_names:
	# 			continue
	# 		value += i*len(flawques)
	# 	return value

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
		return [flaw for i, flaw_set in enumerate(self.typs) for flaw in flaw_set if flaw_set.name not in
				self.restricted_names]

	def OCs(self):
		''' Generator for open conditions'''
		for i, flaw_set in enumerate(self.typs):
			if len(flaw_set) == 0:
				continue
			if flaw_set.name in self.restricted_names:
				continue
			g = (flaw for flaw in flaw_set)
			yield(next(g))

	def next(self):
		''' Returns flaw with highest priority, and removes'''
		for flaw_set in self.typs:
			if len(flaw_set) > 0:
				return flaw_set.pop()
		return None

	#@clock
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

	#@clock
	def insert(self, GL, plan, flaw):
		''' for each effect of an existing step, check and update mapping to consistent effects'''

		if flaw.name == 'tclf':
			#if flaw not in self.threats:
			self.threats.add(flaw)
			return

		if flaw.name == 'dcf':
			self.decomps.add(flaw)
			return

		#unpack flaw
		s_need, pre = flaw.flaw

		#if pre.predicate is static
		if (pre.name, pre.truth) not in FlawLib.non_static_preds:
			self.statics.add(flaw)
			return

		#Eval number of existing candidates
		ante_nums = GL.id_dict[pre.replaced_ID]
		risk_nums = GL.threat_dict[s_need.stepnumber]

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
			if step.stepnumber in risk_nums:
				flaw.risks += 1

		if flaw in self.inits:
			return

		if flaw.risks > 0:
			self.unsafe.add(flaw)
			return

		#if not static but has cndts, then reusable
		if flaw.cndts > 0:
			self.reusable.add(flaw)
			return

		#last, must be nonreusable
		self.nonreusable.add(flaw)

	def __repr__(self):
		#flaw_str_list = [str([flaw for flaw in flaw_set]) for flaw_set in self.typs]
		F = [('|' + ''.join([str(flaw) + '\n|' for flaw in T]) , T.name) for T in self.typs if len(T) > 0]
		#flaw_lib_string = str(['\n {}: \n {} '.format(flaws, name) + '\n' for flaws, name in F])
		return '______________________\n|FLAWLIBRARY: \n|' + ''.join(['\n|{}: \n{}'.format(name, flaws) for
																		  flaws, name in F]) + '______________________'

import unittest
class TestOrderingGraphMethods(unittest.TestCase):

	def test_flaw_counter(self):
		assert True


if __name__ ==  '__main__':
	unittest.main()