from Restrictions import *
import uuid

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	arglabels = ['first-arg', 'sec-arg', 'third-arg', 'fourth-arg', 'fifth-arg']

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

	def mergeUnifiedEffect(self, effabs):
		for element in effabs.elements:
			if element.replaced_ID != -1:
				existing_element = self.getElementById(element.replaced_ID)
				existing_element.merge(element)
			else:
				element.replaced_ID = element.ID
		return self

	#This method has been replaced by the method above
	# def mergeGraph(self, effabs, no_add=None):
	# 	"""
	# 		@param effabs -  an effect of a step unified with precondition of existing step
	# 		@param no_add - if step whose effects include effabs is new, then toggle no_add to add new elms from effabs
	# 		@return self with effabs replacing its former precondition literal
	# 	"""
	# 	for element in effabs.elements:
	#
	# 		#if effabs element replaced a precondition during unification
	# 		# (NOTE: replaced_IDs switched to -1 before unify)
	# 		if element.replaced_ID != -1:
	# 			existing_element = self.getElementById(element.replaced_ID)
	# 			existing_element.merge(element)
	# 			#existing_element.replaced_ID = element.ID #CHECK: is this needed?
	# 		else:
	# 			element.replaced_ID = element.ID
	# 			#if no_add is None:
	# 				#self.elements.add(element)
	#
	# 	# if no_add is None:
	# 	# 	#Create edges for each edge in effabs where the elms
	# 	# 	for edge in effabs.edges:
	# 	# 		source = self.getElementById(edge.source.replaced_ID)
	# 	# 		sink = self.getElementById(edge.sink.replaced_ID)
	# 	# 		existing_edges = {E for E in self.edges if
	# 	# 						  E.source == source and E.sink == sink and E.label == edge.label}
	# 	# 		if len(existing_edges) == 0:
	# 	# 			self.edges.add(Edge(source, sink, edge.label))
	# 	# 			print('a;sldkfjal;sdkfja\nsl;dkfjas\n;ldkfjas;ldf\njkas;ldfkj;asldk\nfja;sldfjkas;ldfkjas;\nldfkjas'
	# 	# 				  ';dlfkjasdl;fkj')
	#
	# 	return self

	def UnifyWith(self, other):
		""" self is operator, other is partial step 'Action'
			self is effect, other is precondition of existing step
			Returns all possible ways to unify self and other, 
				may result in changes to self
		"""

		for element in self.elements:
			element.replaced_ID = -1
		for elm in other.elements:
			elm.replaced_ID = -1

		completed = UnifyLiterals(self, other)
		#completed = self.absolve(copy.deepcopy(other.edges), self.edges)
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other, self))

		return completed

	def getSingleArgByLabel(self, label):
		for edge in self.edges:
			if edge.source == self.root:
				if edge.label == label:
					return edge.sink
		return None

	def updateArgs(self):
		#arglabels = ['first-arg', 'sec-arg', 'third-arg', 'fourth-arg', 'fifth-arg']
		#argTyps = {Argument, Actor}
		self.Args = []
		for label in self.arglabels:
			arg = self.getSingleArgByLabel(label)
			if arg is None:
				break
			else:
				self.Args.append(arg)
		#for element in self.rGetDescendants(self.root):
			#if type(element) in argTyps:
			#	self.Args.add(element)

	def getArgLabel(self, arg):
		incoming = {edge for edge in self.edges if edge.source == self.root and edge.sink == arg}
		for edge in incoming:
			if edge.label in self.arglabels:
				return self.arglabels.index(edge.label)

	def getArgLabels(self, arg_tuple):
		return tuple(self.getArgLabel(arg) for arg in arg_tuple)

	def replaceArg(self, original, replacer):

		self.elements.add(replacer)
		incoming = {edge for edge in self.edges if edge.sink == original}
		for edge in incoming:
			edge.sink = replacer
		#print('Ok')
		#removable = self.getElementById(original.ID)
		#self.elements.remove(removable)

	def replaceArgs(self, arg_tuple):
		"""
		A method to replace all args, as ordered by their args in self.Args, by the args in tuple
		@param arg_tuple: a tuple of args ordered by their replacement of args in self
		@return: none
		"""
		if not len(arg_tuple) == len(self.Args):
			raise ValueError('cannot replace Args, arg_tuple too long/short for %s' % self.name)

		for i, arg in enumerate(arg_tuple):
			original = self.getSingleArgByLabel(self.arglabels[i])
			self.replaceArg(original, arg)
		self.updateArgs()

	def replaceArgsFromLabels(self, arg_list, label_tuple):
		self.updateArgs()
		if not len(self.Args) >= label_tuple[-1]:
			raise ValueError('cannot replace Args, label_tuple references nonexistent arg in %s' % self.name)

		for i,index in enumerate(label_tuple):
			label = self.arglabels[index]
			original = self.getSingleArgByLabel(label)
			self.replaceArg(original, arg_list[i])
		self.updateArgs()

	def swap(self, internal_old, internal_new):
		for edge in (e for e in self.edges if e.sink == internal_old):
			edge.sink = internal_new
		for edge in (e for e in self.edges if e.source == internal_old):
			edge.source = internal_new

	def replaceStepArgsInGraph(self, old_args, new_args):
		pass


def assimilate(EG, ee, pe):
	"""	ProvIDed with old_edge consistent with other_edge
		Merges source and sinks
		Uses = {'new-step', 'effect'}
		"new-step" Self is operator, old_edge is operator edge, other is partial step
		"effect": self is plan-graph, old edge is effect edge, other is eff_abs
	"""

	new_self = EG.copyGen()
	self_source = new_self.getElementById(ee.source.ID)  # source from new_self
	self_source.merge(pe.source)  # source merge
	self_source.replaced_ID = pe.source.ID
	self_sink = new_self.getElementById(ee.sink.ID)  # sink from new_self
	self_sink.replaced_ID = pe.sink.ID
	self_sink.merge(pe.sink)  # sink merge
	return new_self


def UnifyLiterals(effect, prec, C = None):
	"""
		@param effect is an element graph, root element is literal
		@param prec is an element graph, root element is literal consistent with effect.root
		@param C is collected unifications in set
		@return set of literals corresponding to potential effect-prec unifications

		Unifying literals, unlike other elements, can be done just by finding consistent edges, since it is assumed
		that each edge label is unique per literal.

		It is assumed that prec is a subgraph of effect, except with argument bindings.
	"""

	# collected unifications
	if C == None:
		C = set()

	#BASE CASE:
	if len(prec.edges) == 0:
		C.add(effect)
		return C

	P = copy.deepcopy(prec)

	#until we can account for all precondition edges
	pe = P.edges.pop()
	b4 = len(C)
	for ee in effect.edges:
		if pe.isConsistent(ee):
			merged_graph = assimilate(effect, ee, pe)
			C.update(UnifyLiterals(merged_graph, P, C))
	if len(C) > b4 and len(C) > 0:
		return C
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

	New Strategy as of 5 seconds ago:
		If G is self and G' is another graph,
			1) For each root r' in G', create an r'-induced subgraph R' from G'. {R'1, ..., R'n)
			2) For each R', find r consistent with r' and make r-induced subgraph R from G
				If R is "consistent" with R' -- but, what if R and R' share nothing but r==r'?
					RULE: you cannot merge requirement graphs with partial steps because it's not clear who
					has what. If we took all possible ways to aggregate two partial steps with nothing in
					common, then we would have explosion of possible steps. Any partial step which is part of a
					frame must first become instantiated by an operator before it can be used to satisfy a requirement-step.

					But, what about frames? A frame is consistent with another frame - requires a definition such that
						F1 is consistent with F2 just when for each special labeled edge in F1, if F2 has that
						label, then that edge must be consistent. For each pair of steps which must be
						consistent, if those steps are both partial steps, then this is fine since if they have
						goal literals or consenting agents, these would need to be consistent already.
	"""
	pass

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

		""" Instead of "create possible worlds method, instead we just need to select some consistent mapping. But,
		we don't need to do this for operator effects to absolve preconditions because roots are always lits and args
		are always temporal and therefore uniquely labeled."""

if __name__ ==  '__main__':
	unittest.main()