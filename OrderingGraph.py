from ElementGraph import *

class OrderingGraph(Graph):
	
	def __init__(self, ID, typ = None, name = None, Elements = None, Edges = None, Constraints= None):
		if typ == None:
			typ = 'ordering graph'
		super(OrderingGraph,self).__init__(ID,typ,name,Elements,Edges,Constraints)
		
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
		
	def detectCycle(self, V = None):
		if V == None:
			V = set()	
			
		for element in self.elements:
			if element in V:
				continue
				
			visited = self.rDetectCycle(element)
			
			if visited == True:
				return True
			else:
				V.update(visited)
				
		return False

			
	######       rDetect       ####################
	def rDetectCycle(self, element, visited = None):
		""" Returns true if cycle detected. otherwise, returns visited elements

		"""
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
	def __init__(self, ID, typ = None, name = None, Elements = None , Edges = None, Constraints = None):
		if typ == None:
			typ = 'causal link graph'
		super(CausalLinkGraph,self).__init__(ID,typ,name,Elements,Edges,Constraints)
		self.safeSteps = set()
		self.safeConditions = set()
	
	def addEdge(self, source, sink, condition):
		self.elements.add(source)
		self.elements.add(sink)
		self.edges.add(Edge(source, sink, condition))
		
	def __repr__(self):
		return str(['{}-{} --{}-{}--> {}-{}'.format(edge.source.name, edge.source.arg_name, edge.label.truth, edge.label.name, edge.sink.name, edge.sink.arg_name) for edge in self.edges])

import unittest
class TestOrderingGraphMethods(unittest.TestCase):


	def test_detect_cycle(self):
		Elms = [Element(id=0), Element(id=1), Element(id=2), Element(id=3)]
		edges = {Edge(Elms[0], Elms[1], '<'), Edge(Elms[0], Elms[2], '<'), Edge(Elms[0], Elms[3], '<'),
				 Edge(Elms[2], Elms[1], '<'), Edge(Elms[3], Elms[1], '<')}
		G = Graph(id=10, typ='test', Elements=set(Elms), Edges=edges)
		OG = OrderingGraph(G)
		#Graph.get
		#OG.isPath()

if __name__ ==  '__main__':

	unittest.main()