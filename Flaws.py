#from pddlToGraphs import *
import collections
import copy
""" 
	Flaws for element graphs
"""

class Flaw:
	def __init__(self, tuple, name):
		self.name = name
		self.flaw = tuple
		self.h = 1000
		self.effort = 0
		
	def __hash__(self):
		return hash((self.name, self.flaw))
		
	def __eq__(self, other):
		return hash(self) == hash(other)
		
	def __repr__(self):
		return '{}, {}'.format(self.name, self.flaw)


class FlawLib():
	def __init__(self):
		"""TODO: need way to manage multiple sets which have preference ranking and different ordering criterion (
		 LR/MW-first/LIFO)"""

		#static = established by init
		self.statics = set()

		#threat = causal link dependency undone
		self.threats = set()

		#unsafe = existing effect would undo
		self.unsafe = collections.deque

		#reusable = open conditions consistent with at least one existing effect
		self.reusable = set()

		#nonreusable = open conditions inconsistent with existing effect
		self.nonreusable = set()

		#cndts is a dictionary mapping open conditions to candidate action effects
		self.cndts = collections.defaultdict(set)

		#risks is a dictionary mapping open conditions to potential undoing (i.e., unsafe)
		# 	Can we use this to limit search for threatened causal link flaws?
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
			return self.stats.pop()
		if len(self.threats) > 0:
			return self.threats.pop()
		elif len(self.unsafe) > 0:
			return self.unsafe.pop()
		elif len(self.simple) > 0:
			return self.simple.pop()
		elif len(self.local) > 0:
			return self.local.pop()
		else:
			return None

	def upgrade(self, flaw, newList):
		which = self.whichList(flaw)
		if not which is None:
			which.remove(flaw)
		newList.add(flaw)

	def insert(self, flaw, status):
		''' determine which list to put flaw in '''
		if status == 'static':
			self.statics.add(flaw)
		if status == 'threat':
			self.threats.add(flaw)
		if status == 'unsafe':
			self.unsafe.append(flaw)
		if status == 'reusable':
			self.reusable.add(flaw)
		else:
			self.nonreusable.add(flaw)

	def evalCndts(self, graph, action):
		""" For each effect of Action, add to open-condition mapping if consistent"""
		for eff in graph.getNeighborsByLabel(action, 'effect-of'):
			Effect = graph.getElementGraphFromElementID(eff.ID)
			for oc in self.OCs():
				s_need, pre = oc.flaw
				if graph.OrderingGraph.isPath(action, s_need):
					continue
				if not pre.isConsistent(eff):
					#check if "unsafe"
					if pre.name == eff.name:
						Precondition = graph.getElementGraphFromElementID(pre.ID)
						Precondition.root.truth = not pre.truth
						if Effect.canAbsolve(Precondition):
							self.risks[oc].add(eff)
							continue
					else:
						#effect is not a risk nor a candidate
						continue
				Precondition = graph.getElementGraphFromElementID(pre.ID)
				if Effect.canAbsolve(Precondition):
					self.cndts[oc].add(eff)


	def evalFlaw(self, graph, flaw):
		''' for each effect of an existing step, check and update mapping to consistent effects'''
		if flaw.name == 'tclf':
			self.threats.add(flaw)
			return

		operateIfConsistent(graph, flaw, self.cndts[flaw].add)

		if len(self.cdnts[flaw]) > 0:
			static = False
			for eff in self.cndts[flaw]:
				#check if static
				parent = graph.getParentsByLabel(eff, 'effect-of')
				if parent.name == 'initial_dummy_step':
					self.statics.add(flaw)
					static = True
					break

			if not static:
				self.reusable.add(flaw)
		else:
			self.nonreusable.add(flaw)

def operateIfConsistent(graph, flaw, operation):
	s_need, pre = flaw.flaw
	Precondition = graph.getElementGraphFromElementID(pre.ID)
	for edge in graph.edges:
		if edge.label != 'effect-of':
			continue
		eff = edge.sink
		if graph.OrderingGraph.isPath(edge.source, s_need):
			continue
		if not eff.isConsistent(pre):
			continue
		Effect = graph.getElementGraphFromElementID(eff.ID)
		if Effect.canAbsolve(Precondition):
			operation(eff)

#
# class Flaw(collections.deque):
# 	def __init__(self):
# 		self._flaws = []
#
# 	def __getitem__(self, position):
# 		return self._flaws[position]
#
# 	def __len__(self):
# 		return len(self._flaws)
#
# 	def __setitem__(self, flaw, position):
# 		self._flaws[position] = flaw

# def openConditionHeuristic(graph, flaw):
# 	''' q is open condition '''
# 	s_need, q = flaw
# 	init_state = {eff for eff in graph.getNeighborsByLabel(graph.initial_dummy_step, 'effect-of')}
# 	Q = graph.getElementGraphFromElementID(q.ID, Condition)
# 	#if q is false, then we fail if consistent with some Q
# 	if not q.truth:
# 		Q.root.truth = True
# 		cndts = {state for state in init_state if state.isConsistent(Q.root)}
# 		for cndt in cndts:
# 			State = graph.getElementGraphFromElementID(cndt.ID, Condition)
# 			if State.canAbsolve(Q):
#
# 	for state in init_state:
# 		if state.isConsistent(Q.root):
# 			State = graph.getElementGraphFromElementID(state.ID, Condition)
# 		else:
# 			continue
# 		if State.canAbsolve(Q):
# 			flaw.h = 0
# 			flaw.effort = 1
# 			return
# 	if not q.truth:
#
#
# 	#first, check existing actions
# 	for step in graph.Steps:
# 		for eff in graph.getNeighborsByLabel(step, 'effect-of'):
# 			if eff.isConsistent(q):
# 				Eff = graph.getElementGraphFromElementID(eff.ID, Condition)
# 			else:
# 				continue
# 		if Eff.canAbsolve(Q):
# 			flaw.h +=



"""
An open precondition flaw is a tuple <step element, precondition element>
	where precondition element is a literal element,
	there is a precondition edge from the step element to the precondition element,
	and there is no causal link in the graph from another step to the precondition element with label 'effect'
	It's important to consider this last point
		because with this approach, you could instantiate an element which already has some preconditions in causal links

		********Consider above for resolve "uninstantiated step flaw"
"""
