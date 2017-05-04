"""
Restrictions.py

Restrictions are patterns of edges. If detected in a graph, then the graph is considered invalid
Restrictions subclass the Graph class.

If 'p' is an endpoint of an edge in a restriction 'R' of a PlanElmementGraph 'E', then 'p' is an element in 'R' just
when 'p' is an element in 'E'. (In other words, Elements of a restriction must be real elements (must be 'identical'
ID-wise to element in 'E') whereas if 'p' is not an element in 'R', then 'p' must only be 'isEquivalent' to some
element in 'E'.

"""

from Ground_Compiler_Library.Graph import *
#graph has import copy
import collections

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
def consistentMaps(prior_maps, cndt_maps, Mbins = None):
	if Mbins == None:
		Mbins = []
	if len(prior_maps) == 0:
		Mbins.extend(cndt_maps)
	else:
		# for each dictionary 'm' in the list 'Maps_'
		for m in cndt_maps:
			if len(m) == 0:
				continue
			# for each dictionary 'sm' in the set 'successful_maps'
			for pm in prior_maps:
				if consistent_dicts(m, pm):
					Mbins.append(m)
					# this 'm' has been satisfied
					break
	return Mbins

class Restriction(Graph):
	def __init__(self, ID = None, name = None, type_graph = None, Elements = None, Edges = None):
		if type_graph == None:
			type_graph = 'Restriction'
		if ID == None:
			ID = uuid.uuid1(101)

		super(Restriction, self).__init__(ID = ID, name = name, typ = type_graph, Elements= Elements, Edges = Edges)

	def firstIsIsomorphicSubgraphOf(self, EG, identities = None, consistency = None):
		if consistency == None:
			consistency = False
		if consistency == True and identities == None:
			identities = {elm: EG.getElementById(elm.ID) for elm in self.elements
							  if not EG.getElementById(elm.ID) == None}
		if identities == None:
			identities = {elm:EG.getElementById(elm.ID) for elm in self.elements}

		#identify graph sources for graph traversals
		sinks = {edge.sink for edge in self.edges}
		non_sinks = {edge.source for edge in self.edges if edge.source not in sinks}

		#isomorphisms which are consistent across graph traversals
		isos = []
		for ns in non_sinks:
			# ns has incident edges, so base case cannot be first return
			cndt_isomorphisms = self.isIsomorphicSubgraphOf(EG, ns, map_=identities, consistency=consistency)
			if len(cndt_isomorphisms) == 0:
				return False
			new_isos = consistentIsos(isos, cndt_isomorphisms)
			if len(new_isos) == 0:
				return False
			isos.extend(new_isos)
		return True

	def isIsomorphicSubgraphOf(self, EG, r = None, map_ = None, consistency = None):
		""" Graph traversals to determine if self is a subgraph of EG, with special identity requirements
				r is root
				"map_" is of the form self.r_elm : EG.elm
		"""
		if consistency == None:
			consistency= False
		if r == None:
			return self.firstIsIsomorphicSubgraphOf(EG, map_, consistency=consistency)

		if map_ == None:
			return []

		r_edges = self.getIncidentEdges(r)
		if len(r_edges) == 0:
			return [map_] #something

		successful_maps = []
		for r_edge in r_edges:
			if not consistency:
				cndt_edges = {eg_edge for eg_edge in EG.edges if r_edge.isEquivalent(eg_edge)}
			else:
				cndt_edges = {eg_edge for eg_edge in EG.edges if r_edge.isConsistent(eg_edge)}
			if r_edge.source in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.source == map_[r_edge.source]}
			if r_edge.sink in map_:
				cndt_edges -= {edge for edge in cndt_edges if not edge.sink == map_[r_edge.sink]}

			#Fail if there are no cndt edges
			if len(cndt_edges) == 0:
				return []

			#construct new open list for each cndt
			consistent_maps = []
			for cndt in cndt_edges:
				Map_ = copy.deepcopy(map_)
				if not cndt.source in map_:
					Map_[r_edge.source] = cndt.source
				if not cndt.sink in map_:
					Map_[r_edge.sink] = cndt.sink

				Maps_ = self.isIsomorphicSubgraphOf(EG, r_edge.sink, map_ = Map_, consistency=consistency)

				consistent_maps = consistentIsos(successful_maps, Maps_, consistent_maps)

			#if empty, then no ol collected was consistent with a successful_ol
			if len(consistent_maps) == 0:
				return []

			successful_maps.extend(consistent_maps)
		#gauranteed to have successful_map for each r_edge if

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
				[1]  --> [5a]
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

		E_elms = ['buffer']
		E_elms += [Element(ID=uuid.uuid1(91), typ=str(i)) for i in range(1, 8)]

		R_elms = copy.deepcopy(E_elms)

		E_elms += [Element(ID=8, typ='3'),
				   Element(ID=9, typ='4'),
				   Element(ID=10, typ='5'),
				   Element(ID=11, typ='6'),
				   Element(ID=12, typ='n')]


		#R_elms += [Element(ID=uuid.uuid1(i), typ=str(i)) for i in range(1, 8)]

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

		R = Restriction(ID=10, type_graph='R',Elements = set(), Edges=R_edges)
		E = Graph(ID=11, typ='E', Elements=set(E_elms[1:]), Edges=E_edges)

		k = R.isIsomorphicSubgraphOf(E)
		assert k is True

		R_prime = Restriction(ID=10, type_graph='R', Elements=set(R_elms[1:]), Edges=R_edges)
		k = R_prime.isIsomorphicSubgraphOf(E)
		assert k is True


		R_elms = ['buffer']
		R_elms += [Element(ID=uuid.uuid1(i), typ=str(i)) for i in range(1, 8)]
		R_edges = {Edge(R_elms[1], R_elms[2], ' '),
				   Edge(R_elms[1], R_elms[5], ' '),
				   Edge(R_elms[4], R_elms[5], ' '),
				   Edge(R_elms[4], R_elms[3], ' '),
				   Edge(R_elms[7], R_elms[6], ' '),
				   Edge(R_elms[2], R_elms[3], ' '),
				   Edge(R_elms[5], R_elms[3], ' '),
				   Edge(R_elms[5], R_elms[6], ' ')}
		R_new_IDS = Restriction(ID=10, type_graph='R', Elements=set(R_elms[1:]), Edges=R_edges)
		k = R_new_IDS.isIsomorphicSubgraphOf(E)
		assert k is False

		R_edges.add(Edge(R_elms[7], R_elms[2], ' '))
		R_prime_prime_prime = Restriction(ID=10, type_graph='R', Elements=set(R_elms[1:2:1]), Edges=R_edges)
		k = R_prime_prime_prime.isIsomorphicSubgraphOf(E)
		assert k is False

	def test_consistent_Graph(self):
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

		Req = Restriction(ID=10, type_graph='R', Elements = set(O), Edges = Rem)
		Plan = Graph(ID=11, typ='E', Elements=set(G[1:]), Edges = Avail)

		isit = Req.isIsomorphicSubgraphOf(Plan, consistency=True)
		assert isit is True

if __name__ == '__main__':
	unittest.main()