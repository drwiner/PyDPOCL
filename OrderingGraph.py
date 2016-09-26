from collections import defaultdict

from ElementGraph import *


class OrderingGraph(Graph):
	
	def __init__(self, ID, typ = None, name = None, Elements = None, Edges = None):
		if typ == None:
			typ = 'ordering graph'
		super(OrderingGraph,self).__init__(ID,typ,name,Elements,Edges,Restrictions=None)
		
	def isInternallyConsistent(self):
		if self.detectCycle():
			return False
		return True
			
	def addOrdering(self, source, sink):
		self.elements.add(source)
		self.elements.add(sink)
		self.edges.add(Edge(source, sink, '<'))
		
	def addEdge(self, source, sink):
		self.addOrdering(source, sink)

	def detectCycle(self,):
		''' Returns True if cycle, False otherwise
			Strategy: for each element, find descendent elements. If a is descendant of b and b is descendant of a,
			then there is a cycle'''

		for element in self.elements:
			visited = self.rDetectCycle(element) - {element}
			predecessors = self.getParents(element)
			for elm in visited:
				if elm in predecessors:
					return True
		return False

			
	######       rDetect       ####################
	def rDetectCycle(self, element, visited = None):
		if visited == None:
			visited = set()
			
		#Base Case 1
		if element in visited:
			return visited
			
		visited.add(element)
		
		#Base Case 2
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			return visited
			
		#Induction
		for edge in incidentEdges:
			#Descendants.add(edge.sink)
			visited = self.rDetectCycle(edge.sink, visited = visited)
		return visited
		
	def foundPath(self,start, finish):
		""" Returns if there is path start to finish (1) finish to start (2) or none at all (0)"""
		visited = self.rDetectCycle(start)
		if visited:
			if finish in visited:
				return 1
		visited2 = self.rDetectCycle(finish)
		if visited2:
			if start in visited2:
				return 2
		return 0
		
	def isPath(self, start, finish):
		"""Returns True if path from start to Finish, False otherwise"""
		visited = self.rDetectCycle(start) 
		if visited:
			if finish in visited:
				return True
		return False
		
	def __repr__(self):
		return str(['{}-{} < {}-{}'.format(edge.source.name, edge.source.arg_name, edge.sink.name, edge.sink.arg_name) for edge in self.edges])
		
		
class CausalLinkGraph(OrderingGraph):
	def __init__(self, ID, typ = None, name = None, Elements = None , Edges = None):
		if typ == None:
			typ = 'causal link graph'
		super(CausalLinkGraph,self).__init__(ID,typ,name,Elements,Edges)
		self.nonThreats = defaultdict(set)
	
	def addEdge(self, source, sink, condition):
		self.elements.add(source)
		self.elements.add(sink)
		self.edges.add(Edge(source, sink, condition))
		
	def __repr__(self):
		return str(['{}-{} --{}-{}-{}--> {}-{}'.format(edge.source.name, edge.source.arg_name, edge.label.truth,
													   edge.label.replaced_ID, edge.label.name, edge.sink.name,
					edge.sink.arg_name)	for edge in self.edges])

import unittest
class TestOrderingGraphMethods(unittest.TestCase):


	def test_detect_cycle(self):
		Elms = [Element(ID=0, name = '0'), Element(ID=1, name='1'), Element(ID=2, name='2'), Element(ID=3, name='3')]
		edges = {Edge(Elms[0], Elms[1], '<'), Edge(Elms[0], Elms[2], '<'), Edge(Elms[0], Elms[3], '<'),
				 Edge(Elms[2], Elms[1], '<'), Edge(Elms[3], Elms[1], '<')}
		G = Graph(ID=10, typ='test', Elements=set(Elms), Edges=edges)
		OG = OrderingGraph(ID = 5, Elements = G.elements, Edges = G.edges)
		assert(not OG.detectCycle())
		OG.edges.add(Edge(Elms[1], Elms[0], '<'))
		assert (OG.detectCycle())
		#Graph.get
		#OG.isPath()

if __name__ ==  '__main__':

	unittest.main()