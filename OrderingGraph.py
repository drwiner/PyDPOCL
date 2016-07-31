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
		self.edges.add(Edge(source, sink, '<'))
		
	def addEdge(self, source, sink):
		self.addOrdering(source, sink)
		
	def detectCycle(self, V = None):
		if V == None:
			V = set()	
			
		for element in self.elements:
			if element in V:
				continue
				
			visited = self.rDetectCycle(original_element=element)
			
			if visited == True:
				return True
			else:
				V.update(visited)
				
		return False

			
	######       rDetect       ####################
	def rDetectCycle(self, original_element, element = None, visited = None):
		""" Returns true if cycle detected. otherwise, returns visited elements

		"""
		if visited == None:
			visited = set()
			
		#Base Case 1
		if not element is None:
			if element is original_element:
				return True
			
		#Runs on first time
		if element is None:
			element = original_element
			
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
		output = '{'
		for edge in self.edges:
			output.append('{}-{} --{}--> {}-{}'.format(edge.source.name, edge.source.typ, edge.label, edge.sink.name, edge.sink.typ))
		output.append(['}'])
		return '\n'.join(output)
		
		
class CausalLinkGraph(OrderingGraph):
	def __init__(self, ID, typ = None, name = None, Elements = None , Edges = None, Constraints = None):
		if typ == None:
			typ = 'causal link graph'
		super(CausalLinkGraph,self).__init__(ID,typ,name,Elements,Edges,Constraints)
	
	def addEdge(self, source, sink, condition_id):
		self.edges.add(Edge(source, sink, condition_id))