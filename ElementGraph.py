from Restrictions import *
import uuid

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""

	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None, Restrictions=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()

		super(ElementGraph, self).__init__(ID, type_graph, name, Elements, Edges, Restrictions)
		self.root = root_element

	def copyGen(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid1(21)
		return new_self

	def copyWithNewIDs(self, from_this_num):
		new_self = self.copyGen()
		for element in new_self.elements:
			element.ID = from_this_num
			from_this_num = from_this_num + 1
		return new_self

	@classmethod
	def makeElementGraph(cls, elementGraph, element):
		edges = copy.deepcopy(elementGraph.rGetDescendantEdges(element))
		elms = {edge.source for edge in edges}|{edge.sink for edge in edges}
		element_copy = next(iter(elm for elm in elms if elm.ID == element.ID))
		return cls(element.ID, element.typ, name=None, root_element=element_copy,Elements= elms, Edges = edges,
				   Restrictions=elementGraph.restrictions)

	def getElementGraphFromElement(self, element, Type=None):
		if Type == None:
			Type = eval(element.typ)
		if self.root == element:
			return self.copyGen()
		return Type.makeElementGraph(self, element)

	def getElementGraphFromElementID(self, element_ID, Type = None):
		return self.getElementGraphFromElement(self.getElementById(element_ID), Type)

	def addRealRestriction(self, source, sink, label):
		""" It's 'real' because the source and sink must be ID-identical in a graph for the Restriction to be
		considered an isomorphic subgraph"""
		R = Restriction()
		R.elements.add(source)
		R.elements.add(sink)
		R.edges.add(Edge(source,sink, label))
		self.restrictions.add(R)

	def addNonEqualityRestrictions(self, iter):
		""" @param iter : set of False-Equals Lits"""
		for nonequal in iter:
			IE = self.getIncidentEdges(nonequal)
			arg1, arg2 = (edge.sink for edge in IE)
			self.edges -= IE
			self.elements -= {nonequal}
			if not self.preventEqualityWithRestriction(arg1, arg2):
				return False
		return True

	def preventEqualityWithRestriction(self, arg1, arg2):
		#Just need one parent of type Condition

		arg_1_edge = next(iter(self.getIncomingEdgesByType(arg1, 'Condition')))
		if arg_1_edge is None:
			arg_2_edge = next(iter(self.getIncomingEdgesByType(arg2, 'Condition')))
			if arg_2_edge is None:
				#TODO: consider cases when argument passed to this method would be orphans without Condition parents
				return False
			self.addRealRestriction(arg_2_edge.source, arg1, arg_2_edge.label)
			return True

		self.addRealRestriction(arg_1_edge.source, arg2, arg_1_edge.label)
		return True



	def preventThreatWithRestriction(self, threat, condition):
		"""
		"""
		R = Restriction()
		T = self.getIncidentEdges(threat)
		C = self.getIncidentEdges(condition)
		edge_pairs = {(e1, e2) for e1 in T for e2 in C
						if e1.label == e2.label and e1.sink != e2.sink}
		if len(edge_pairs) == 0:
			if len(T) == 0 and len(C) == 0:
				#TODO: consider cases when a Condition wouldn't have children even if hollow containers with no minds
				#  of their own
				return False
			return False

		t_edge, c_edge = next(iter(edge_pairs))
		R.elements.add(c_edge.source)
		R.elements.add(t_edge.sink)
		R.edges.add(Edge(c_edge.source, t_edge.sink, t_edge.label))
		self.restrictions.add(R)
		return True

	def mergeGraph(self, other, no_add=None):
		"""
			For each element in other to include in self, if its a replacer, merge it into self
					A relacer element 'replacer' is one such that replacer.replaced_ID == some element ID in self
			Otherwise, add that element to self
			For each edge in other to include in self, if its in self do nothing, otherwise add it
		
			Plan.mergeGraph(instance), where instance is "other". 
					Other is a graph where some elements in the graph are "replacing" elements in self
					
			Precondition.mergeGraph(Effect) where the Effect is a Condition which has instantiated a precondition of S_{need}
					Effect has some elements (arguments) which replaced elements in the operator clone
					This method will merge the originals in the operator giving them the extra properties in the replacees of Effect
					
			Graph.mergeGraph(new_operator) where new_operator has replaced some elements in graph.
					Then, if its a new element, add it. If its a replacer, merge it. 
					For each edge in new_operator, if 
					
		"""
		for element in other.elements:
			if not hasattr(element, 'replaced_ID'):
				element.replaced_ID = -1

			if element.replaced_ID != -1:
				existing_element = self.getElementById(element.replaced_ID)
				existing_element.merge(element)
				existing_element.replaced_ID = element.ID
			else:
				element.replaced_ID = element.ID
				if no_add is None:
					self.elements.add(element)
					element.replaced_ID = element.ID

		if no_add is None:
			for edge in other.edges:
				source = self.getElementById(edge.source.replaced_ID)
				sink = self.getElementById(edge.sink.replaced_ID)
				existing_edges = {E for E in self.edges if
								  E.source == source and E.sink == sink and E.label == edge.label}
				if len(existing_edges) == 0:
					self.edges.add(Edge(source, sink, edge.label))

		return self

	def getInstantiations(self, other):
		""" self is operator, other is partial step 'Action'
			self is effect, other is precondition of existing step
			Returns all possible ways to unify self and other, 
				may result in changes to self
		"""

		for element in self.elements:
			element.replaced_ID = -1
		for elm in other.elements:
			elm.replaced_ID = -1

		completed = self.absolve(copy.deepcopy(other.edges), self.edges)
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other, self))

		return completed

	def updateArgs(self):
		arglabels = ['first-arg', 'sec-arg', 'third-arg', 'fourth-arg', 'fifth-arg']
		#argTyps = {Argument, Actor}
		self.Args = []
		for label in arglabels:
			try:
				self.Args.append(next(iter(self.getNeighborsByLabel(self.root, label))))
			except:
				return
		#for element in self.rGetDescendants(self.root):
			#if type(element) in argTyps:
			#	self.Args.add(element)

	def absolve(self, Remaining=None, Available=None, Collected=None):
		""" Every edge from other must be consistent with some edge in self.
			An edge from self cannot account for more than one edge from other.
				
				Remaining: edges left to account for in other
				Available: edges in 'first' self, which cannot account for more than one edge
				
				USAGE: Excavate_Graph.absolves(partial_step, partial_step.edges, self.edges, Collected)
				
				Returns: Set of copies of Operator which absolve the step (i.e. merge)
		"""

		if Remaining == None:
			Remaining = set()
		if Available == None:
			Available = set()
		if Collected == None:
			Collected = set()

		if len(Remaining) == 0:
			Collected.add(self)
			return Collected

		other_edge = Remaining.pop()
		num_collected_before = len(Collected)

		for prospect in Available:
			if other_edge.isConsistent(prospect):
				new_self = self.assimilate(prospect, other_edge)
				#if new_self.isInternallyConsistent():
				Collected.update(new_self.absolve({copy.deepcopy(rem) for rem in Remaining}, Available, Collected))

		if len(Collected) > num_collected_before and len(Collected) > 0:
			return Collected

		return set()

	def createPossibleWorlds(self, Remaining=None, Available=None, Collected=None):
		""" Every edge from other must be consistent with some edge in self.
			"Shared-endpoint clause"
				AND, for any two edges (e1, e2) sharing an endpoint p, if (d1, d2) are two edges consistent with (e1,
				e2), then (d1,d2) share an endpoint p' consistent with p.
			"Possible-exclusion clause"
				AND, for each edge of the form p1 --k--> p2, if there is a consistent edge in self pi --k-->pj,
				then there are (at least) 2 possible worlds: 1 where (pi,pj) merges with (p1,p2), and another world
				where (pi,pj) are distinct from (p1,p2).
			"Potential-adjacencies clause"
				AND, for each edge of the form p1 --k--> p2, if there is a consistent edge in self pi --k-->pj,
				then there are 3 additional possible worlds, 1 where pi==p1 (s.t. all edges of the form (p0,
				p1) are now (p0,p1==pi), another where pj == p2, BUT THERE IS NO THIRD WORLD where pi==p1 and pj==p2
				because then it would be the same edge with label k. Labels are always function-free and grounded.

			In total, for every edge (p1,p2) consistent with edge in self (pi,pj), there are 4 possible worlds
				1) (p1==pi,p2==pj)			   "regular merge"
				2) (p1,p2), (pi,pj)			   "possibel exclusion"
				3) (p1==pi, p2), (p1==pi, pj)  "potential adjacencies"
				4) (p1, p2==pj), (pi, p2==pj)  "potential adjacencies"
		"""

		if Remaining == None:
			Remaining = set()
		if Available == None:
			Available = set()
		if Collected == None:
			Collected = set()

		if len(Remaining) == 0:
			Collected.add(self)
			return Collected

		other_edge = Remaining.pop()
		num_collected_before = len(Collected)

		for prospect in Available:
			if other_edge.isConsistent(prospect):
				new_self = self.assimilate(prospect, other_edge)
				# if new_self.isInternallyConsistent():
				Collected.update(new_self.absolve({copy.deepcopy(rem) for rem in Remaining}, Available, Collected))

		if len(Collected) > num_collected_before and len(Collected) > 0:
			return Collected

		return set()

	def assimilate(self, old_edge, other_edge):
		"""	ProvIDed with old_edge consistent with other_edge
			Merges source and sinks
			Uses = {'new-step', 'effect'}
			"new-step" Self is operator, old_edge is operator edge, other is partial step
			"effect": self is plan-graph, old edge is effect edge, other is eff_abs 
		"""

		new_self = self.copyGen()
		self_source = new_self.getElementById(old_edge.source.ID)  # source from new_self
		self_source.merge(other_edge.source)  # source merge
		self_source.replaced_ID = other_edge.source.ID
		self_sink = new_self.getElementById(old_edge.sink.ID)  # sink from new_self
		self_sink.replaced_ID = other_edge.sink.ID
		self_sink.merge(other_edge.sink)  # sink merge
		return new_self


import unittest
class TestInstantiations(unittest.TestCase):
	def test_method(self):
		""" Test Idea:
				Create three conditions between pairs of two graphs
				1) G1 is a subset of G2
				2) G1 has a subset which equals a subset of G2, but G1 is not a subset of G2
				3) G1 has

		"""
		Elms = [Element(ID=0, name='0'), Element(ID=1, name='1'), Element(ID=2, name='2'), Element(ID=3, name='3')]
		edges = {Edge(Elms[0], Elms[1], 'k1'), Edge(Elms[0], Elms[2], 'k2'), Edge(Elms[0], Elms[3], 'k3'),
				 Edge(Elms[2], Elms[1], 'j'), Edge(Elms[3], Elms[1], 'j')}
		G = Graph(ID=10, typ='test', Elements=set(Elms), Edges=edges)


if __name__ ==  '__main__':
	unittest.main()