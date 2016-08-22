"""
Restrictions.py

Restrictions are patterns of edges. If detected in a graph, then the graph is considered invalid
Restrictions subclass the Graph class.

If 'p' is an endpoint of an edge in a restriction 'R' of a PlanElmementGraph 'E', then 'p' is an element in 'R' just
when 'p' is an element in 'E'. (In other words, Elements of a restriction must be real elements (must be 'identical'
ID-wise to element in 'E') whereas if 'p' is not an element in 'R', then 'p' must only be 'isEquivalent' to some
element in 'E'.

"""

from Graph import *
import collections

#class ElmContainer(set):
def realHeadEdgeCompare(restriction_edge, existing_edge):
	if restriction_edge.source.ID == existing_edge.source.ID:
		if restriction_edge.sink.isEquivalent(existing_edge.sink):
			return True
	return False
def realTailEdgeCompare(restriction_edge, existing_edge):
	if restriction_edge.sink.ID == existing_edge.sink.ID:
		if restriction_edge.source.isEquivalent(existing_edge.source):
			return True
	return False
def realEdgeCompare(restriction_edge, existing_edge):
	if restriction_edge.source.ID == existing_edge.source.ID:
		if restriction_edge.sink.ID == existing_edge.sink.ID:
			return True
	return False

def consistent_dicts(dict1, dict2):
	common_keys = set(dict1.keys()) & set(dict2.keys())
	for ck in common_keys:
		if not dict1[ck] == dict2[ck]:
			return False

	return True


class Restriction(Graph):
	def __init__(self, ID, name = None, type_graph = None, Elements = None, Edges = None):
		if type_graph == None:
			type_graph = 'Restriction'

		super(Restriction, self).__init__(ID = ID, name = name, typ = type_graph, Elements= Elements, Edges = Edges)

	def exists(self, elm):
		return elm in self.edges

	@property
	def realStats(self):
		realheads = set()
		realtails = set()
		reals_ = set()
		unreals = set()
		for edge in self.edges:
			if self.exists(edge.source):
				if self.exists(edge.sink):
					reals_.add(edge)
				else:
					realheads.add(edge)
			elif self.exists(edge.sink):
				realtails.add(edge)
			else:
				unreals.add(edge)
		return (realheads, realtails, reals_, unreals)

	def detectIn(self, EG):
		#EG - elementGraph
		#Find a subset of edges in EG such that for each edge in self, there is some equivalent edge in EG and if
		#For each edge, if edge.source in self.elements,
		realheads, realtails, reals_, unreals  = self.realStats
		#for unreal in unreals:

	def convertToDict(self):
		""" Converts Graph into adjacency dictionary"""
		g = collections.defaultdict(set)
		for edge in self.edges:
			g[edge.source.ID].add(edge.sink.ID)
		return g



	def isIsomorphicSubgraph(self, EG_edges, consistent_graphs = None):
		if consistent_graphs == None:
			consistent_graphs = set()

		if len(EG_edges) == 0:
			return consistent_graphs

		g = collections.defaultdict(set)
		for edge in self.edges:
			for other_edge in EG_edges:
				if edge.isEquivalent(other_edge):
					g_prime = copy.deepcopy(g)
					g_prime[edge.source] = edge.sink
					g_prime.add(self.isIsomorphicSubgraph(EG_edges - {other_edge}, consistent_graphs))

	def rCompare(self, EG, r_elm, eg_elm):
		''' Assuming r_elm and eg_elm are equivalent/identical:
			Base case - no incident edges in r_elm.
			1) get all incident edges of r_elm, and of eg_elm
			2) find equivalent/identical matching edges for each r_elm_edges in eg_elm_edges (record them in dictionary)
			3) If successful, then for each r_elm_edge_sink - eg_elm_edge.sink pair, rCompare
		'''
		#base case:
		r_elm_edges = self.getIncidentEdges(r_elm)
		if len(r_elm_edges) == 0:
			return True

		eg_elm_edges = EG.getincidentEdges(eg_elm)
		potential_matches = {}

		#graph container
		new_graph = collections.defaultdict(set)
		for re in r_elm_edges:
			potential_matches = {new_graph}
			for eg in eg_elm_edges:
				if re.isEquivalent(eg):
					if self.rCompare(EG, re.sink, eg.sink):

						potential_matches.add(eg.sink)
			#if len(potential_matches) == 0:
			#THIS STRATEGY DOESN'T WORK BECAUSE: consider edges in self a --> b --> c, and a --> d --> c and edges a' --> b' --> r' and a'-->d' --> t' in EG where r' /= t'.
			#instead, need to construct new graphs, where the graphs are valid just when they are isomorphic in edge
					# relationships to R/self.
	def rCompare(self, EG, r_elm, eg_elm, mapping = None):
		"""GOAL: find all mappings of edges in self to edges in EG with as few as possible terminating branches
				Strategy 1: top-down
				Strategy 2: pick any edge and find consistent/equivalent other-edge
		"""

		#initially, mapping_dict[r_elm] : eg_elm

		if mapping is None:
			mapping = collections.defaultdict(int)

		r_elm_edges = self.getIncidentEdges(r_elm)
		if len(r_elm_edges) == 0:
			return True

		eg_elm_edges = EG.getincidentEdges(eg_elm)

		#realheads, realtails, reals_, unreals = self.realStats
		edge_mapping = collections.defaultdict(int)
		edge_mappings
		for re in r_elm_edges:
			#limit search to just those
			if not mapping[re.sink] == 0:
				for eg in eg_elm_edges:
					if re.isEquivalent(eg):
						#mapping_copy = copy.deepcopy(mapping)
						mapping[re.sink] = eg.sink
			else:
				cndts = {eg_edge for eg_edge in eg_elm_edges if eg_edge.sink == mapping[re.sink]}
				for cndt in cndts:
					if re.isEquivalent(cndt):
						edge_mapping[re] = cndt

			for eg in eg_elm_edges:
			#	if re in unreals:
					if re.isEquivalent(eg):
						mapping_copy = copy.deepcopy(mapping)
						mapping_copy[re.sink] = eg.sink
						mappings.add(self.rCompare(EG, re.sink, eg.sink))

		#then, for each potential edge
		pass

	def compare(self, EG, mapping_dicts = None):
		if mapping_dicts == None:
			mapping_dicts = set()

		realheads, realtails, reals_, unreals = self.realStats

		#Surface level copy is fine, just don't want to modify 'the set' EG.edges
		Available = copy(EG.edges)
		mapping_dict = {}
		mapping_dicts.add(mapping_dict)
		for edge in unreals:
			for edge in Available:
				if edge

		def mapEdges(self, es1, es2):
			mapping = {}
			for edge in es1:
				if self.exists(es1.source):
					if self.exists(es1)
		#initially, mapping_dict[r_elm] : eg_elm


	def equivEdgesSameSink(self, EG, r_sink):
		'''
				r_edges = {edge for edge in self.edges if edge.sink == r_sink}
				if len(r_edges) == 0:
					return
		'''

		r_edges = self.getIncidentEdges(r_sink)

		#Base Case 1: No outgoing edges, then find equivalent sink and return
		if len(r_edges) == 0:
			return {elm for elm in EG if elm.isEquivalent(r_sink)}
			#return {(r_sink, cndt) for cndt in (elm for elm in EG if elm.isEquivalent(r_sink))}

		for r_edge in r_edges:

			#get all edges in EG which have sink compatible with r_sink
			cndts = self.equivEdgesSameSink(EG, r_edge.source)
			cndt_edges = {edge for edge in EG.edges if edge.sink in cndts}

			#for each r_edge, match to an equivalent cndt EG edge

			for cndt_edge in cndt_edges:
				if r_edge.isEquivalent(cndt_edge):
					self.equivEdgesSameSink(EG, r_edge.source)



	def BreadthFirstIsIsomorphicSubgraphOf(self, EG, r = None, map_ = None):
		""" Breadth-first search to determine if self is a subgraph of EG, with special identity requirements

				Requirements: self must have at least one outgoing edge from 'r'
		"""

		# if r == none, then find all elms which are souces but not sinks
		if r == None:
			sinks = {edge.sink for edge in self.edges}
			non_sinks = {edge.source for edge in self.edges if edge.source not in sinks}
			for ns in non_sinks:
				#ns has incident edges, so base case cannot be first return
				if not self.BreadthFirstIsIsomorphicSubgraphOf(EG, ns, map_= {}) is None:
					return True
			return False
			#return {self.BreadthFirstIsIsomorphicSubgraphOf(EG, ns, openList = {}) for ns in non_sinks}

		r_edges = self.getIncidentEdges(r)
		if len(r_edges) == 0:
			return {map_} #something

		successful_maps = set()
		for r_edge in r_edges:
			cndt_edges = {eg_edge for eg_edge in EG.edges if r_edge.isEquivalent(eg_edge)}
			if r_edge.source in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.source == map_[r_edge.source]}
			if r_edge.sink in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.sink == map_[r_edge.sink]}

			#Fail if there are no cndt edges
			if len(cndt_edges) == 0:
				return None

			#construct new open list for each cndt
			consistent_maps = set()
			for cndt in cndt_edges:
				Map_ = copy(map_)
				if not cndt.source in map_:
					Map_[cndt.source] = r_edge.source
				if not cndt.sink in map_:
					Map_[cndt.sink] = r_edge.sink
				#OLs.add(OL)
				OLs = self.BreadthFirstIsIsomorphicSubgraphOf(EG, r_edge.sink, Map_)

				#only add openList if consistent with some successful_ol
				consistent_maps.update({ol for ol in OLs for sol in successful_maps if not ol is None and consistent_dicts(ol,sol)})

			#if empty, then no ol collected was consistent with a successful_ol
			if len(consistent_maps) == 0:
				return None

			successful_maps.update(consistent_maps)
		#gauranteed to have successful_ol for each r_edge if

		return successful_maps
