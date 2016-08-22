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
from copy import deepcopy

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

	def convertToDict(self):
		""" Converts Graph into adjacency dictionary"""
		g = collections.defaultdict(set)
		for edge in self.edges:
			g[edge.source.ID].add(edge.sink.ID)
		return g

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
				isomorphisms = self.BreadthFirstIsIsomorphicSubgraphOf(EG, ns, map_= {})

				if len(isomorphisms) > 0:
					return True
			return False
			#return {self.BreadthFirstIsIsomorphicSubgraphOf(EG, ns, openList = {}) for ns in non_sinks}

		if map_ == None:
			return {}

		r_edges = self.getIncidentEdges(r)
		if len(r_edges) == 0:
			return frozenset(map_) #something

		successful_maps = set()
		for r_edge in r_edges:
			cndt_edges = {eg_edge for eg_edge in EG.edges if r_edge.isEquivalent(eg_edge)}
			if r_edge.source in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.source == map_[r_edge.source]}
			if r_edge.sink in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.sink == map_[r_edge.sink]}

			#Fail if there are no cndt edges
			if len(cndt_edges) == 0:
				return set()

			#construct new open list for each cndt
			consistent_maps = set()
			for cndt in cndt_edges:
				Map_ = copy.deepcopy(map_)
				if not cndt.source in map_:
					Map_[cndt.source] = r_edge.source
				if not cndt.sink in map_:
					Map_[cndt.sink] = r_edge.sink
				#OLs.add(OL)
				OLs = self.BreadthFirstIsIsomorphicSubgraphOf(EG, r_edge.sink, map_ = Map_)

				#only add openList if consistent with some successful_ol
				to_add = {ol for ol in OLs for sol in successful_maps if not ol is None and consistent_dicts(ol, sol)}
				consistent_maps.update(to_add)

			#if empty, then no ol collected was consistent with a successful_ol
			if len(consistent_maps) == 0:
				return set()

			successful_maps.update(consistent_maps)
		#gauranteed to have successful_ol for each r_edge if

		return successful_maps

import unittest
import uuid
class TestOrderingGraphMethods(unittest.TestCase):
	def test_isomorphic_subgraph(self):
		"""
				Restriction Graph:
				1 --> 2 --> 3
				1 --> 5 --> 3
				4 --> 5 --> 6
				4 		--> 3
				7       --> 6

				Element Graph:
				[1]  --> [2]  --> [3a]
				[4a] --> [2]  --> [3b]
				[4b] --> [2]  --> [3a]
				[4b] --> [5a] --> [3b]
						 [5a] --> [6a]
				[4b] --> [5b]
				[4a] 		  --> [3a]
				[4b] 		  --> [3b]
				[7]  --> [5a]
				[7]  --> [5b] --> ['n']
				[7]  	      --> [6a]
				[7]           --> [6b]
				[7]  		  --> ['n']


				1 = [1], [4a/4b] = 4, [3a if 4a else 3b if 4b] = 3, [7] = 7, [5b] = 5, [2] = 2, [6a] = 6
			"""
		R_elms = ['buffer']
		R_elms += [Element(ID=uuid.uuid1(i), typ=str(i)) for i in range(1, 8)]
		E_elms = ['buffer']
		E_elms += [Element(ID=uuid.uuid1(91), typ=str(i)) for i in range(1, 8)]
		E_elms += [Element(ID=8, typ='3'),
				   Element(ID=9, typ='4'),
				   Element(ID=10, typ='5'),
				   Element(ID=11, typ='6'),
				   Element(ID=12, typ='n')]
		R_edges = {Edge(R_elms[1], R_elms[2], ' '),
				   Edge(R_elms[1], R_elms[5], ' '),
				   Edge(R_elms[4], R_elms[5], ' '),
				   Edge(R_elms[4], R_elms[3], ' '),
				   Edge(R_elms[7], R_elms[6], ' '),
				   Edge(R_elms[2], R_elms[3], ' '),
				   Edge(R_elms[5], R_elms[3], ' '),
				   Edge(R_elms[5], R_elms[6], ' ')}
		E_edges = {Edge(E_elms[1], E_elms[2], ' '),
				   Edge(E_elms[1], E_elms[5], ' '),
				   Edge(E_elms[4], E_elms[5], ' '),
				   Edge(E_elms[4], E_elms[3], ' '),
				   Edge(E_elms[7], E_elms[6], ' '),
				   Edge(E_elms[2], E_elms[3], ' '),
				   Edge(E_elms[5], E_elms[3], ' '),
				   Edge(E_elms[5], E_elms[6], ' '),
				   Edge(E_elms[2], E_elms[8], ' '),  # 8 = 3b, 9 = 4b, 10 = 5b, 11 = 6b, 12 = 'n'
				   Edge(E_elms[9], E_elms[2], ' '),
				   Edge(E_elms[9], E_elms[5], ' '),
				   Edge(E_elms[5], E_elms[8], ' '),
				   Edge(E_elms[9], E_elms[10], ' '),
				   Edge(E_elms[9], E_elms[8], ' '),
				   Edge(E_elms[7], E_elms[10], ' '),
				   Edge(E_elms[10], E_elms[12], ' '),
				   Edge(E_elms[7], E_elms[11], ' '),
				   Edge(E_elms[7], E_elms[12], ' ')
				   }
		R = Restriction(ID=10, type_graph='R', Elements=set(R_elms), Edges=R_edges)
		E = Graph(ID=11, typ='E', Elements=set(E_elms), Edges=E_edges)

		k = R.BreadthFirstIsIsomorphicSubgraphOf(E)
		assert(k)
		print(R)


if __name__ == '__main__':

	#R.BreadthFirstIsIsomorphicSubgraphOf(E)
	unittest.main()