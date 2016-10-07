from Element import *
import copy
from clockdeco import clock
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
		return hash(self.source.ID) ^ hash(self.sink.ID) ^ hash(self.label)

	def assign(self, endpoint, new_val):
		new_val.ID = self.endpoint.ID
		self.endpoint = new_val
		
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
		self.subgraphs = Restrictions

	def __len__(self):
		return len(self.elements)

	def __iter__(self):
		elms = iter(self.elements)
		yield next(elms)
	
	def getElementById(self, ID):
		for element in self.elements:
			if element.ID == ID:
				return element
		return None
	
	def getElmByRID(self, ID):
		for element in self.elements:
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
		for r in self.subgraphs:
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

	def assign(self, old_elm_in_edge, new_elm, remove_old=True):
		if new_elm not in self.elements:
			self.elements.add(new_elm)
		if remove_old:
			self.elements.remove(old_elm_in_edge)
		edges = iter(self.edges)
		for edge in edges:
			if edge.source == old_elm_in_edge:
				self.edges.add(Edge(new_elm, edge.sink, edge.label))
				self.edges.remove(edge)
			if edge.sink == old_elm_in_edge:
				self.edges.add(Edge(edge.source, new_elm, edge.label))
				self.edges.remove(edge)
		for r in self.subgraphs:
			if r.name == 'Restriction':
				r.assign(old_elm_in_edge, new_elm)


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
	def getIncomingEdgesByTypeAndLabel(self, element, typ, label):
		return {edge for edge in self.edges if edge.sink == element and edge.source.typ == typ and edge.label == label}
		
	######       rGet       ####################
	def rGetDescendants(self, element, Descendants=None):
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

	def rGetDescendantEdges(self, element, Descendant_Edges=None):
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

	def isConsistentSubgraph(self, cndt_subgraph, return_map=False):
		"""
		@param other: a graph which may be a consistent subgraph of self
		@param return_map
		@return: if for each other.edge, there is a consistent self.edge, following the shared-endpoints rule of edge sets
		"""
		possible_map = isConsistentEdgeSet(Rem=copy.deepcopy(cndt_subgraph.edges), Avail=copy.deepcopy(self.edges),
										   return_map=return_map)
		if not possible_map is False:
			#returns True when return_map  is False
			#return_map = possible_map
			return possible_map
		return False

	def findConsistentSubgraph(self, cndt_subgraph):
		return findConsistentEdgeMap(Rem = copy.deepcopy(cndt_subgraph.edges), Avail = copy.deepcopy(self.edges))
		
	def isInternallyConsistent(self):
		return not self.equivalentWithRestrictions()

	def equivalentWithRestrictions(self):
		if not hasattr(self, 'subplans') or len(self.subplans) == 0:
			return False

		for restriction in self.subgraphs:
			if restriction.type_graph != 'Restriction':
				continue
			if restriction.isIsomorphicSubgraphOf(self):
				return True
		return False

	def __repr__(self):
		edges = str([edge for edge in self.edges])
		elms = str([elm for elm in self.elements])
		return '\n' + edges + '\n\n_____\n\n ' + elms + '\n'


################################################################
# consistent edge sets following shared endpoints clause    ####
################################################################

def isConsistentEdgeSet(Rem, Avail, map_=None, return_map=False):
	if map_ == None:
		map_ = {}

	#Base Case - all Remaining edges
	if len(Rem) == 0:
		if return_map:
			return map_
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
		_Map = isConsistentEdgeSet(copy.deepcopy(Rem), Avail-{cndt}, Map_, return_map)
		if not _Map is False:
			if return_map:
				return _Map
		#if isConsistentEdgeSet(copy.deepcopy(Rem), Avail-{cndt}, Map_):
		#	if return_map:
		#		return Map_
		#	return True
	return False



def findConsistentEdgeMap(Rem, Avail, map_ = None, Super_Maps = None):
	if map_ is None:
		map_ = {}
	if Super_Maps is None:
		Super_Maps = []

	#Base Case - all Remaining edges
	if len(Rem) == 0:
		Super_Maps.append(map_)
		return Super_Maps

	edge_match = Rem.pop()

	cndt_edges = {edge for edge in Avail if edge.isConsistent(edge_match)}

	if edge_match.source in map_:
		cndt_edges -= {edge for edge in cndt_edges if not edge.source == map_[edge_match.source]}
	if edge_match.sink in map_:
		cndt_edges -= {edge for edge in cndt_edges if not edge.sink == map_[edge_match.sink]}

	if len(cndt_edges) == 0:
		return Super_Maps

	for cndt in cndt_edges:
		Map_ = copy.deepcopy(map_)
		if not cndt.source in map_:
			Map_[edge_match.source] = cndt.source
		if not cndt.sink in map_:
			Map_[edge_match.sink] = cndt.sink
		findConsistentEdgeMap(copy.deepcopy(Rem), Avail, Map_, Super_Maps)

	return Super_Maps

#A method - unify - which given two graphs, will merge. currently performed by mergeGraph
# def UnifyActions(_Map = None, R = None, A = None):
# 	"""
#
# 	@param _Map: dictonary
# 	@param R: edges to account for
# 	@param A: edges which account as
# 	@return: dictionary _Map
# 	"""
#
# 	if _Map ==None:
# 		_Map = {} 	;#_Map is a 1:1 mapping (r : a) for r in "R" for a in "A" s.t. every edge in "R" has one partner in "A"
# 					#Mapping is a dictionary.
# 	if R == None:
# 		R = []		;#"R" is the set of edges all of whose edges must be accounted for
# 	if A == None:
# 		A = []		;#"A" is the set of edges which account for edges in "R".
#
# 	if len(R) == 0:
# 		return _Map
#
# 	rem = R.pop()
# 	cndts = {edge for edge in A if edge.isConsistent(rem)}
#
# 	if rem.source in _Map:
# 		cndts -= {edge for edge in cndts if not edge.source == _Map[rem.source]}
# 	if rem.sink in _Map:
# 		cndts -= {edge for edge in cndts if not edge.sink == _Map[rem.sink]}
#
# 	if len(cndts) == 0:
# 		return []
#
# 	Mbins = []
# 	for cndt in cndts:
# 		Map_ = copy.deepcopy(_Map)
# 		if not cndt.source in _Map:
# 			Map_[rem.source] = cndt.source
# 		if not cndt.sink in _Map:
# 			Map_[rem.sink] = cndt.sink
#
# 		#if this 'cndt' was to account for 'rem', recursively solve for rest of R and append all possible worlds in []
# 		M_ = isConsistentEdgeSet(Map_ = _Map, R = copy.deepcopy(R), A = A-{cndt})
# 		Mbins = consistentMaps(prior_maps=Map_,cndt_maps = M_, Mbins = Mbins)
#
# 	if len(Mbins) == 0:
# 		return []
#
# 	return _Map.extend(Mbins)


import unittest

class TestGraph(unittest.TestCase):
	pass
	# def test_consistent_edge_set(self):
	# 	"""
	# 			Full Graph
	# 			1 --> 2 --> 3 --> 5
	# 				  2 --> 4 --> 5
	#
	# 			Requirements
	# 			[2]  --> [3]
	# 			[2]  --> [4]
	#
	#
	# 		"""
	# 	G = 	  ['buffer',
	# 			   Element(ID=1,name=1, typ='1'),
	# 			   Element(ID=2,name=2, typ='2'),
	# 			   Element(ID=3,name=3, typ='3'),
	# 			   Element(ID=4,name=4, typ='4'),
	# 			   Element(ID=5,name=5, typ='5')]
	# 	O =		  [Element(ID=20, typ='2'),
	# 			   Element(ID=30, typ='3'),
	# 			   Element(ID=40, typ='4')]
	#
	# 	Avail = {Edge(G[1],G[2],'a'),
	# 		   Edge(G[2],G[3], 'b'),
	# 		   Edge(G[2],G[4], 'c'),
	# 		   Edge(G[3],G[5], 'd'),
	# 		   Edge(G[4],G[5], 'e')}
	# 	Rem = {
	# 			Edge(O[0],O[1], 'b'),
	# 			Edge(O[0],O[2], 'c')}
	#
	#
	# 	isit = isConsistentEdgeSet(Rem, Avail)
	# 	assert(isit)
	# 	assert(not isConsistentEdgeSet(Avail, Rem))
	# 	print(isit)
	#
	# 	#With LARGER example to look through
	# 	G = ['buffer']
	# 	G+= [Element(ID=i, name=i, typ=str(i)) for i in range(1,900)]
	# 	Avail = {Edge(G[i],G[i+1],'m') for i in range(1,700)}
	# 	Avail.update({Edge(G[1],G[2],'a'),
	# 		   Edge(G[2],G[3], 'b'),
	# 		   Edge(G[2],G[4], 'c'),
	# 		   Edge(G[3],G[5], 'd'),
	# 		   Edge(G[4],G[5], 'e')})
	#
	# 	isit = isConsistentEdgeSet(Rem, Avail)
	# 	assert (isit)
	# 	print(isit)

if __name__ ==  '__main__':
	pass
	#unittest.main()