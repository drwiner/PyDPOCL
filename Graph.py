from Element import *
import copy

class Edge:
	""" Edge labels are assumed to be function-free and ground, and there can be no edge otherwise"""
	__slots__ = 'source', 'sink', 'label'
	def __init__(self, source, sink, label):
		self.source=  source
		self.sink = sink
		self.label = label
		
	def isConsistent(self, other):
		if self.source.isConsistent(other.source) and self.sink.isConsistent(other.sink) and self.label == other.label:
			return True
		return False

	def isEquivalent(self, other):
		if self.source.isEquivalent(other.source) and self.sink.isEquivalent(other.sink) and self.label == other.label:
			return True
		return False
		
	def __eq__(self, other):
		if other is None:
			return False
		if self.source.ID == other.source.ID and self.sink.ID == other.sink.ID and self.label == other.label:
			return True
		return False
		
	def __ne__(self, other):
		return (not self.__eq__(other))
		
	def __hash__(self):
		return hash((self.source.ID, self.sink.ID, self.label))
		
	def merge(self, other):
		"""Merges source and sink"""

		if not self.isConsistent(other):
			return None
			
		self.source.merge(other.source)
		self.sink.merge(other.sink)
		
		return self
	
	def swapSink(self,sink):
		self.sink = sink
		return self
		
	def __repr__(self):
		return 'Edge {} --{}--> {}'.format(self.source, self.label, self.sink)

class Graph(Element):
	"""A graph is an element with elements, edges, and restrictions"""
	def __init__(self, ID, typ, name = None, Elements = None, Edges = None, Restrictions = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()
		
		super(Graph,self).__init__(ID,typ,name)
		self.elements = Elements
		self.edges = Edges
		self.restrictions = Restrictions
	
	def getElementById(self, ID):
		for element in self.elements:
			if element.ID == ID:
				return element
		return None
	
	def getElementByReplacedId(self, ID):
		for element in self.elements:
			if hasattr(element, 'replaced_ID'):
				if element.replaced_ID == ID:
					return element
		return None

			
	def replaceWith(self, oldsnk, newsnk):
		''' removes oldsnk from self.elements, replaces all edges with snk = oldsnk with newsnk'''


		if oldsnk == newsnk:
			return
		if self.getElementById(newsnk.ID) is None:
			raise NameError('newsnk replacer is not found in self')
		if oldsnk in self.elements:
			self.elements.remove(oldsnk)
		for incoming in (edge for edge in self.edges if edge.sink == oldsnk):
			incoming.sink = newsnk
		#update constraint edges which might reference specific elements being replaced
		for r in self.restrictions:
			for r_edge in r.edges:
				if r_edge.source == oldsnk:
					if r_edge.source in r.elements:
						r.elements.add(newsnk)
					r.replaceWith(r_edge.source, newsnk)
				if r_edge.sink == oldsnk:
					if r_edge.sink in r.elements:
						r.elements.add(newsnk)
					r.replaceWith(r_edge.sink, newsnk)
		return self

	def getEdgesByLabel(self, label):
		return {edge for edge in self.edges if edge.label == label}
			
	def getEdgesByIdsAndLabel(self, source_id, sink_id, label):
		return {edge for edge in self.edges if edge.source.ID == source_id and edge.sink.ID == sink_id and edge.label == label}


	def getIncidentEdges(self, element):
		return {edge for edge in self.edges if edge.source == element}
	def getNeighbors(self, element):
		return {edge.sink for edge in self.edges if edge.source.ID == element.ID}
	def getEstablishingParent(self, element):
		return next(iter(edge.source for edge in self.edges if edge.sink == element and edge.label == 'effect-of'))
	def getParents(self, element):
		return set(edge.source for edge in self.edges if edge.sink == element)
	def getNeighborsByLabel(self, element, label):
		return {edge.sink for edge in self.edges if edge.source.ID == element.ID and edge.label == label}
	def getIncidentEdgesByLabel(self, element, label):
		return {edge for edge in self.edges if edge.source.ID == element.ID and edge.label == label}
	def getParentsByLabel(self, element, label):
		return set(edge.source for edge in self.edges if edge.sink is element and edge.label is label)
	def getIncomingEdges(self, element):
		return {edge for edge in self.edges if edge.sink == element}
	def getIncomingEdgesByType(self, element, typ):
		return {edge for edge in self.edges if edge.sink  == element and edge.source.typ == typ}
		
	######       rGet       ####################
	def rGetDescendants(self, element, Descendants = None):
		if Descendants == None:
			Descendants = set()
			
		Descendants.add(element)
		
		#Base Case
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			return Descendants
			
		#Induction
		for edge in incidentEdges:
			#Descendants.add(edge.sink)
			Descendants = self.rGetDescendants(edge.sink, Descendants)
		return Descendants

	def rGetDescendantEdges(self, element, Descendant_Edges = None):
		if Descendant_Edges == None:
			Descendant_Edges = set()
		#Base Case
		incident_Edges = self.getIncidentEdges(element)
		if len(incident_Edges) == 0:
			return Descendant_Edges
		
		#Induction
		Descendant_Edges= Descendant_Edges.union(incident_Edges)
		for edge in incident_Edges:
			Descendant_Edges = self.rGetDescendantEdges(edge.sink, Descendant_Edges)
			
		return Descendant_Edges
	
	################  Consistency ###############################
	def canAbsolve(self, other):
		""" A graph absolves another iff for each other.edge, there is a consistent self.edge
		"""
		if rDetectConsistentEdgeGraph(Remaining = copy.deepcopy(other.edges), Available = copy.deepcopy(self.edges)):
			if not self.equivalentWithRestrictions():
				return True
		return False
		
	def isInternallyConsistent(self):
		return not self.equivalentWithRestrictions()
		
	def coAbsolvant(self, other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
		
	###############################################################
		
	def elementsAreConsistent(self, other, self_element, other_element):
		if not self_element.isConsistent(other_element):
			return False
			
		descendant_edges = self.rGetDescendantEdges(self_element)
		other_descendant_edges = other.rGetDescendantEdges(other_element)
		if rDetectConsistentEdgeGraph(other_descendant_edges,descendant_edges):
			return True
			
		return False
		

	def equivalentWithRestrictions(self):
		if len(self.restrictions) == 0:
			return False

		for restriction in self.restrictions:
			if restriction.isIsomorphicSubgraphOf(self):
				return True
		return False

	def __repr__(self):
		edges = str([edge for edge in self.edges])
		elms = str([elm for elm in self.elements])
		return '\n' + edges + '\n\n_____\n\n ' + elms + '\n'
		
def rDetectConsistentEdgeGraph(Remaining = None, Available = None):
	""" Returns True if all remaining edges can be assigned a consistent non-used edge in self
		TODO: investigate if possible problem: two edges p1-->p2-->p3 are consistent with edges q1-->q2 q2'-->q3 just when q2 == q2'
				this method will succeed, incorrectly, when q2 neq q2'
			  -- This hasn't been a problem, because most edge labels have unique labels in a graph
			  -- should create test conditions - in ElementGraph -- to test if "canAbsolve" always means that we will return something with "getInstantiations"
	"""
	if Remaining == None:
		Remaining = set()
	if Available == None:
		Available = set()
		

	if len(Remaining)  == 0:
		return True

	other_edge = Remaining.pop()

	for prospect in Available:
		if prospect.isConsistent(other_edge):
			if rDetectConsistentEdgeGraph(	Remaining, {item for item in Available - {prospect}}):
				return True
	return False


def consistent_dicts(dict1, dict2):
	common_keys = set(dict1.keys()) & set(dict2.keys())
	for ck in common_keys:
		if not dict1[ck] == dict2[ck]:
			return False

	return True


def consistentIsos(prior_isos, cndt_isos, new_isos = None):
	if new_isos == None:
		new_isos = []
	if len(prior_isos) == 0:
		new_isos.extend(cndt_isos)
	else:
		# for each dictionary 'm' in the list 'Maps_'
		for m in cndt_isos:
			if len(m) == 0:
				continue
			# for each dictionary 'sm' in the set 'successful_maps'
			for sm in prior_isos:
				if consistent_dicts(m, sm):
					new_isos.append(m)
					# this 'm' has been satisfied
					break
	return new_isos

def isConsistentEdgeSet(Rem = None, Avail = None, map_ = None):
	if Rem == None:
		Rem = set()
	if Avail == None:
		Avail = set()
	if map_ == None:
		map_ = {}

	#Base Case - all Remaining edges
	if len(Rem) == 0:
		return True

	edge_match = Rem.pop()

	cndt_edges = {edge for edge in Avail if edge.isConsistent(edge_match)}

	if edge_match.source in map_:
		cndt_edges -= {edge for edge in cndt_edges if not edge.source == map_[edge_match.source]}
	if edge_match.sink in map_:
		cndt_edges -= {edge for edge in cndt_edges if not edge.sink == map_[edge_match.sink]}

	if len(cndt_edges) == 0:
		return False

	for cndt in cndt_edges:
		Map_ = copy.deepcopy(map_)
		if not cndt.source in map_:
			Map_[edge_match.source] = cndt.source
		if not cndt.sink in map_:
			Map_[edge_match.sink] = cndt.sink
		if isConsistentEdgeSet(copy.deepcopy(Rem), Avail-{cndt}, Map_):
			return True
	return False

def Unify(_Map = None, R = None, A = None):
	if _Map ==None:
		_Map = {} 	;#_Map is a 1:1 mapping (r : a) for r in "R" for a in "A" s.t. every edge in "R" has one partner in "A"
	if R == None:
		R = []		;#"R" is the set of edges all of whose edges must be accounted for
	if A == None:
		A = []		;#"A" is the set of edges which account for edges in "R".

					#@param _Map is a mapping (r : a) for r in R for a in A
					#@param R is the



import unittest

class TestGraph(unittest.TestCase):
	def test_consistent_edge_set(self):
		"""
				Full Graph
				1 --> 2 --> 3 --> 5
					  2 --> 4 --> 5

				Requirements
				[2]  --> [3]
				[2]  --> [4]


			"""
		G = 	  ['buffer',
				   Element(ID=1,name=1, typ='1'),
				   Element(ID=2,name=2, typ='2'),
				   Element(ID=3,name=3, typ='3'),
				   Element(ID=4,name=4, typ='4'),
				   Element(ID=5,name=5, typ='5')]
		O =		  [Element(ID=20, typ='2'),
				   Element(ID=30, typ='3'),
				   Element(ID=40, typ='4')]

		Avail = {Edge(G[1],G[2],'a'),
			   Edge(G[2],G[3], 'b'),
			   Edge(G[2],G[4], 'c'),
			   Edge(G[3],G[5], 'd'),
			   Edge(G[4],G[5], 'e')}
		Rem = {
				Edge(O[0],O[1], 'b'),
				Edge(O[0],O[2], 'c')}


		isit = isConsistentEdgeSet(Rem, Avail)
		assert(isit)
		assert(not isConsistentEdgeSet(Avail, Rem))
		print(isit)

		#With LARGER example to look through
		G = ['buffer']
		G+= [Element(ID=i, name=i, typ=str(i)) for i in range(1,900)]
		Avail = {Edge(G[i],G[i+1],'m') for i in range(1,700)}
		Avail.update({Edge(G[1],G[2],'a'),
			   Edge(G[2],G[3], 'b'),
			   Edge(G[2],G[4], 'c'),
			   Edge(G[3],G[5], 'd'),
			   Edge(G[4],G[5], 'e')})

		isit = isConsistentEdgeSet(Rem, Avail)
		assert (isit)
		print(isit)

if __name__ ==  '__main__':
	unittest.main()