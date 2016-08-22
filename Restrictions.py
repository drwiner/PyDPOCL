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


#class ElmContainer(set):


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

	def rCompare(self, EG, r_elm, eg_elm, mapping = None):
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

		if mapping is None:
			mapping = {}

		eg_elm_edges = EG.getincidentEdges(eg_elm)
		elm_match = {}
		for re in r_elm_edges:
			for eg in eg_elm_edges:
				if re.isEquivalent(eg):
					mapping_copy = copy.deepcopy(mapping)
					mapping_copy[re.sink] = eg.sink
					self.rCompare(EG, re.sink, eg.sink, mapping_copy)


