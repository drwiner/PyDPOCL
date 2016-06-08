from PlanElementGraph import *

class OrderingGraph(Graph):
	
	def __init__(self, id, type = None, name = None, Elements = None, Edges = None, Constraints= None):
		if type == None:
			type = 'ordering graph'
		super(OrderingGraph,self).__init__(id,type,name,Elements,Edges,Constraints)
		
		
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
		""" Returns true if cycle detected. otherwise, returns visited elements"""
		if visited == None:
			visited = set()
			
		#Base Case 1
		if element in visited:
			return True
			
		visited.add(element)
		
		#Base Case 2
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			return visited
			
		#Induction
		for edge in incidentEdges:
			#Descendants.add(edge.sink)
			visited = self.rDetectCycle(edge.sink, visited)
		return visited