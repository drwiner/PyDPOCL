from Element import Element, Argument, Literal
#from PlanElementGraph import Condition
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
		
	def merge(self, other):
		"""Merges source and sink"""

		if not self.isConsistent(other):
			return None
			
		self.source.merge(other.source)
		self.sink.merge(other.sink)
		
		return self
		
	def __repr__(self):
		return 'Edge {} --{}--> {}'.format(self.source, self.label, self.sink)

class Graph(Element):
	"""A graph is an element with elements, edges, and restrictions"""
	def __init__(self, ID, typ, name=None, Elements=None, Edges=None, Restrictions=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()
		
		super(Graph, self).__init__(ID, typ, name)
		self.elements = Elements
		self.edges = Edges
		self.subgraphs = Restrictions

	def __len__(self):
		return len(self.elements)

	def __iter__(self):
		elms = iter(self.elements)
		yield next(elms)

	def get_by_id(self, _id):
		for element in self.elements:
			if element.ID == _id:
				return element
		return None
	
	def getElmByRID(self, ID):
		for element in self.elements:
			if element.replaced_ID == ID:
				return element
		for edge in self.edges:
			if edge.source.replaced_ID == ID:
				return edge.source
			if edge.sink.replaced_ID == ID:
				return edge.sink
		return None

	def replaceWith(self, oldsnk, newsnk):
		''' removes oldsnk from self.elements, replaces all edges with snk = oldsnk with newsnk'''

		if oldsnk == newsnk:
			return

		self.assign(oldsnk, newsnk)

		if self.get_by_id(newsnk.ID) is None:
			raise NameError('newsnk replacer is not found in self')

		# update constraint edges which might reference specific elements being replaced
		for r in self.subgraphs:
			r.assign(oldsnk, newsnk)

		if hasattr(self, 'ground_subplan'):
			self.ground_subplan.assign(oldsnk, newsnk)

		return self

	def assign(self, old_elm_in_edge, new_elm, remove_old=True):
		if old_elm_in_edge.ID == new_elm.ID:
			return
		new_elements = list(self.elements)
		new_edges = list(self.edges)
		if remove_old:
			# if old_elm_in_edge in self.elements:
			new_elements.remove(old_elm_in_edge)
		if new_elm not in self.elements:
			new_elements.append(new_elm)
		for edge in list(self.edges):
			if edge.source == old_elm_in_edge:
				# if edge in self.edges:
				new_edges.remove(edge)
				new_edges.append(Edge(new_elm, edge.sink, edge.label))
			if edge.sink == old_elm_in_edge:
				new_edges.remove(edge)
				new_edges.append(Edge(edge.source, new_elm, edge.label))
		self.elements = set(new_elements)
		self.edges = set(new_edges)
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
		return findConsistentEdgeMap(Rem=copy.deepcopy(cndt_subgraph.edges), Avail=copy.deepcopy(self.edges))
		
	def isInternallyConsistent(self):
		return not self.equivalentWithRestrictions()

	def equivalentWithRestrictions(self):
		if not hasattr(self, 'subgraphs') or len(self.subgraphs) == 0:
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

def isIdenticalElmsInArgs(C1, C2):
	arg_map = zip(C1, C2)
	for u, v in arg_map:
		if isinstance(u, Argument):
			if u.ID != v.ID:
				return False
			continue
		for elm in u.elements:
			try:
				v.get_by_id(elm.ID)
			except:
				if isinstance(elm, Literal):
					for v_elm in v.elements:
						if v_elm.name == elm.name and v_elm.truth == elm.truth:
							continue
				return False
			# if elm.ID != v.getElmByRID(elm.replaced_ID).ID:
			#	return False
	return True

def retargetElmsInArgs(GSP, C1, C2):
	# C2 is removable, in GSP, while C1 is replacer not in GSP
	arg_map = dict(zip(C1, C2))
	#For all args in C1/C2 which are element graphs, create a map by finding equivalent pieces via replaced_IDs. which are assumed to be the same for both. This makes sense since they are "literally" the same ground elements, but with different IDs
	bigger_map = {}
	for u, v in arg_map.items():
		if isinstance(u, Argument):
			bigger_map[u] = v
			continue
		for elm in u.elements:
			bigger_map[elm] = v.getElmByRID(elm.replaced_ID)
			#if bigger_map[elm] is None and isinstance(elm, Literal):
			#	for v_elm in v.elements:
			#		if v_elm.name == elm.name and v_elm.truth == elm.truth:
			#			bigger_map[elm] = v_elm
			#			break
	#for each elm in GSP, or story, replace
	retarget(GSP, bigger_map)

	#Links
	links = list(GSP.CausalLinkGraph.edges)
	for link in list(GSP.CausalLinkGraph.edges):
		if link.source in bigger_map and link.sink in bigger_map:
			links.remove(link)
			links.append(
				Edge(bigger_map[link.source], bigger_map[link.sink], bigger_map[link.label]))
		elif link.source in bigger_map:
			links.remove(link)
			links.append(
				Edge(bigger_map[link.source], link.sink, bigger_map[link.label]))
		elif link.sink in bigger_map:
			links.remove(link)
			links.append(
				Edge(link.source, bigger_map[link.sink], bigger_map[link.label]))
	GSP.CausalLinkGraph.edges = set(links)

	#Orderings
	orderings = list(GSP.OrderingGraph.edges)
	for o in list(GSP.OrderingGraph.edges):
		if o.source in bigger_map and o.sink in bigger_map:
			orderings.remove(o)
			orderings.append(Edge(bigger_map[o.source], bigger_map[o.sink], '<'))
		elif o.source in bigger_map:
			orderings.remove(o)
			orderings.append(Edge(bigger_map[o.source], o.sink, '<'))
		elif o.sink in bigger_map:
			orderings.remove(o)
			orderings.append(Edge(o.source, bigger_map[o.sink], '<'))
	GSP.OrderingGraph.edges = set(orderings)

	return C2

def retargetArgs(G, C1, C2):
	#G contains C1 and means to replace it with C2
	retarget(G, dict(zip(C1,C2)))
	return C2

def retarget(G, _map):
	for elm in list(G.elements):
		if elm in _map:
			if elm.ID != _map[elm].ID:
				G.assign(elm, _map[elm])


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
	return False

def findConsistentEdgeMap(Rem, Avail, map_=None, Super_Maps=None):
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
		findConsistentEdgeMap(Rem, Avail, Map_, Super_Maps)

	return Super_Maps

import unittest

class TestGraph(unittest.TestCase):
	pass

if __name__ ==  '__main__':
	pass
	#unittest.main()