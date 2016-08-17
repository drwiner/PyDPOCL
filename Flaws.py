#from pddlToGraphs import *
import collections
import bisect

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

class FlawLib():
	def __init__(self):
		"""TODO: need way to manage multiple sets which have preference ranking and different ordering criterion (
		 LR/MW-first/LIFO)"""
		self.typs = 'statics threats unsafe reusable nonreusable'.split()

		#static = established by init
		self.statics = set()

		#threat = causal link dependency undone
		self.threats = set()

		#unsafe = existing effect would undo
		#		sorted by number of cndts
		self.unsafe = Flawque()

		#reusable = open conditions consistent with at least one existing effect
		#		sorted by number of cndts
		self.reusable = Flawque()

		#nonreusable = open conditions inconsistent with existing effect
		#		sorted by number of cndts
		self.nonreusable = Flawque()

		#cndts is a dictionary mapping open conditions to candidate action effects
		self.cndts = collections.defaultdict(set)

		#risks is a dictionary mapping open conditions to potential undoing (i.e., unsafe)
		# 		Can we use this to limit search for threatened causal link flaws?
		self.risks = collections.defaultdict(set)

	def __len__(self):
		return len(self.threats) + len(self.unsafe) + len(self.statics) + len(self.reusable) + len(self.nonreusable)

	def __contains__(self, flaw):
		return flaw in self.threats or flaw in self.unsafe or flaw in self.nonreusable or flaw in self.reusable or \
			   flaw in self.statics

	def whichList(self, flaw):
		if flaw in self.statics:
			return self.statics
		if flaw in self.threats:
			return self.threats
		if flaw in self.unsafe:
			return self.unsafe
		if flaw in self.reusable:
			return self.reusable
		if flaw in self.nonreusable:
			return self.nonreusable
		return None

	def OCs(self):
		''' Generator for open conditions'''
		g = (flaw for flaw in self.statics)
		yield next(g)
		g = (flaw for flaw in self.unsafe)
		yield next(g)
		g = (flaw for flaw in self.reusable)
		yield next(g)
		g = (flaw for flaw in self.nonreusable)
		yield next(g)

	def next(self):
		''' Returns flaw with highest priority, and removes'''
		if len(self.statics) > 0:
			return self.statics.pop()
		if len(self.threats) > 0:
			return self.threats.pop()
		elif len(self.unsafe) > 0:
			return self.unsafe.pop()
		elif len(self.reusable) > 0:
			return self.reusable.pop()
		elif len(self.nonreusable) > 0:
			return self.nonreusable.pop()
		else:
			return None

	def upgrade(self, flaw, newList):
		which = self.whichList(flaw)
		if not which is None:
			which.remove(flaw)
		newList.add(flaw)

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
				if Effect.canAbsolve(Precondition):
					self.cndts[oc].add(eff)

	def insert(self, graph, flaw):
		''' for each effect of an existing step, check and update mapping to consistent effects'''

		if flaw.name == 'tclf':
			self.threats.add(flaw)
			return

		#Determine existing Cdnts and Risks for this flaw
		s_need, pre = flaw.flaw
		Precondition = graph.subgraph(pre)

		for edge in graph.getEdgesByLabel('effect-of'):

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
			if Effect.canAbsolve(Precondition):
				self.cndts[flaw].add(eff)

		#Bin flaw into right list
		flaw.cndts = len(self.cndts[flaw])
		flaw.risks = len(self.risks[flaw])

		# for any cndt, if establishing step is initial, then flaw is static {t}
		if flaw.cndts > 0:
			for eff in self.cndts[flaw]:
				#elm = graph.getElementById(eff.ID)
				parent = next(iter(graph.getParents(eff)))
				#print(len(parents))
				#parent = parents.pop()
				#parent = next(iter(graph.getParentsByLabel(elm, 'effect-of')))
				if parent.name == 'dummy_init':
					self.statics.add(flaw)
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
		statics = str([flaw for flaw in self.statics])
		threats = str([flaw for flaw in self.threats])
		unsafe = str([flaw for flaw in self.unsafe])
		reusable = str([flaw for flaw in self.reusable])
		nonreusable = str([flaw for flaw in self.nonreusable])
		return '\nFLAW LIBRARY: \nstatics:  \n' + statics + '\nthreats: \n' + threats + '\nunsafe: \n' + unsafe + \
			   '\nreusable: \n' + reusable + '\nnonreusable: \n' + nonreusable + '\n'


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
			if R.canAbsolve(ExistingGraph):
				operation(eff)
		return True
	return False


"""
An open precondition flaw is a tuple <step element, precondition element>
	where precondition element is a literal element,
	there is a precondition edge from the step element to the precondition element,
	and there is no causal link in the graph from another step to the precondition element with label 'effect'
	It's important to consider this last point
		because with this approach, you could instantiate an element which already has some preconditions in causal links

		********Consider above for resolve "uninstantiated step flaw"
"""
