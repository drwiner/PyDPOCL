from Element import *

class Edge:
	def __init__(self, source, sink, label):
		self.source=  source
		self.sink = sink
		self.label = label
		
	def isProperty(self,other,property):
		return self.property(other)
		
	def isConsistent(self, other):
		if self.source.isConsistent(other.source) and self.sink.isConsistent(other.sink) and self.label == other.label:
			return True
		return False
		
	def isCoConsistent(self,other):
		if self.isCoConsistent(other) and other.isCoConsistent(self):
			return True
			
		return False

	def isEquivalent(self, other):
		if self.source.isEquivalent(other.source) and self.sink.isEquivalent(other.sink) and self.label == other.label:
			return True
		return False
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		"""Returns merge other.sink into self.sink"""
		#Assume source is already equal and edge label is already equal
		if not self.source.isEqual(other.source):
			return False
		#Assume edges are co-consistent
		if not self.isCoConsistent(other):
			return False
		
		return self.sink.merge(other.sink)

class Graph(Element):
	"""A graph is an element with elements, edges, and constraints"""
	def __init__(self, id, type, name = None, Elements = set(), Edges = set(), Constraints = set()):
		super(Graph,self).__init__(id,type,name)
		self.elements = Elements
		self.edges = Edges;
		self.constraints = Constraints
		
	def addEdge(self, edge):
		if edge not in self.edges:
			self.edges.add(edge)
		
	def addConstraint(self, edge):
		if edge not in self.constraints:
			self.constraints.add(edge)
			
	def getIncidentEdges(self, element):
		return {edge for edge in self.edges if edge.source is element}
	def getNeighbors(self, element):
		return set(edge.sink for edge in self.edges if edge.source is element)
	def getParents(self, element):
		return set(edge.source for edge in self.edges if edge.sink is element)
	def getNeighborsByLabel(self, element, label):
		return set(edge.sink for edge in self.edges if edge.source is element and edge.label is label)
	def getIncidentEdgesByLabel(self, element, label):
		return {edge for edge in self.edges if edge.source is element and edge.label is label}
	def getParentsByLabel(self, element, label):
		return set(edge.source for edge in self.edges if edge.sink is element and edge.label is label)
	def getConstraints(self, element):
		return {edge for edge in self.constraints if edge.source is element}
	def getConstraintsByLabel(self, element, label):
		return set(edge for edge in self.constraints if edge.source is element and edge.label is label)
	def getConstraintsByParent(self, element):
		return {edge.source for edge in self.constraints if edge.sink is element}
		
	def findConsistentElement(self, element):
		return set(member for member in self.elements if member.isConsistent(element))
		
	#Given edge, find all other edges with same source
	def findCoIncidentEdges(self, lonely_edge):
		return set(edge for edge in self.edges if edge.source is lonely_edge.source and edge is not lonely_edge)
		
	def findConsistentEdge(self, edge):
		return set(member for member in self.edges if member.isConsistent(edge))
		
	def findConsistentEdgeWithIgnoreList(self, edge, Ignore_List):
		return set(member for member in self.edges if member not in Ignore_List and member.isConsistent(edge))
		
	def rGetDescendants(self, element, Descendants = set()):
	
		#Base Case
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			return element
			
		#Induction
		for edge in incidentEdges:
			Descendants.add(element)
			Descendants = self.rGetDescendants(edge.sink, Descendants)
		return Descendants
	
	def rGetDescendantEdges(self, element, Descendant_Edges = set()):
		#Base Case
		incident_Edges = self.getIncidentEdges(element)
		if len(incident_Edges) == 0:
			return Descendant_Edges
		
		#Induction
		Descendant_Edges=Descendant_Edges.union(incident_Edges)
		for edge in incident_Edges:
			Descendant_Edges = self.rGetDescendantEdges(edge.sink, Descendant_Edges)
			
		return Descendant_Edges	
		
	def equivalentWithConstraints(self, other):
		for c in other.constraints:
			#First, narrow down edges to just those which are equivalent with constraint source
			suspects = {edge.source for edge in self.edges if edge.source.isEquivalent(c.source)}
			for suspect in suspects:
				print('suspect id: ', suspect.id)
				if self.constraintEquivalentWithElement(other, suspect, c.source):
					return True
		return False	
		
	def constraintEquivalentWithElement(self, other, self_element, constraint_element):
		""" Returns True if element and constraint have equivalent descendant edge graphs"""
		#Assumes self_element is equivalent with constraint_element, but just in case
		if not self_element.isEquivalent(constraint_element):
			return False
		
		descendant_edges = self.rGetDescendantEdges(self_element)
		constraints = other.rGetDescendantConstraints(constraint_element)
		return rDetectEquivalentEdgeGraph(constraints, descendant_edges)
		
	def rGetDescendantConstraints(self, constraint_source, Descendant_Constraints = set()):
		#Base Case
		incident_constraints = self.getConstraints(constraint_source)
		if len(incident_constraints) == 0:
			return Descendant_Constraints
		
		#Induction
		Descendant_Constraints=Descendant_Constraints.union(incident_constraints)
		for c in incident_constraints:
			Descendant_Constraints = self.rGetDescendantConstraints(c.sink, Descendant_Constraints)
			
		return Descendant_Constraints
	
	###############################################################
	def isConsistent(self, other):
		""" Returns True if for every edge in other_graph, there is some consistent edge in self"""
		if rDetectConsistentEdgeGraph(Remaining = other.edges, Available = self.edges):
			print('consistent without constraints')
			if not self.equivalentWithConstraints(other):
				print('consistent with constraints')
				return True
		return False
		
	def isCoConsistent(self,other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
	###############################################################
		
	def elementsAreConsistent(self, other, self_element, other_element):
		if not self_element.isConsistent(other_element):
			return False
			
		descendant_edges = self.rGetDescendantEdges(self_element)
		other_descendant_edges = other.rGetDescendantEdges(other_element)
		if rDetectConsistentEdgeGraph(other_descendant_edges,descendant_edges):
			return True
			
		return False
		
	def elementsAreEquivalent(self, other, self_element, other_element):
		""" Elements in different graphs (self vs other) are equivalent 
		if edge path from self_element has superset of edge path from other_element"""
		if not self_element.isEquivalent(other_element):
			return False
		
		descendant_edges = self.rGetDescendantEdges(self_element)
		other_descendant_edges = other.rGetDescendantEdges(other_element)
		return rDetectEquivalentEdgeGraph(other_descendant_edges, descendant_edges)
		
def rDetectConsistentEdgeGraph(Remaining = set(), Available = set()):
	""" Returns True if all remaining edges can be assigned a consistent non-used edge in self """
	if len(Remaining)  == 0:
		return True
		
	#No solution if there are more edges remaining then there are available edges
	if len(Remaining) > len(Available):
		return False

	other_edge = Remaining.pop()
	print('remaining ', len(Remaining))
	for prospect in Available:
		if prospect.isConsistent(other_edge):
			A = {item for item in Available if not (item is prospect)}
			if (rDetectConsistentEdgeGraph(Remaining, A)):
				return True
	return False
	
def rDetectEquivalentEdgeGraph(Remaining = set(), Available = set()):
	""" Returns True if all remaining edges can be assigned an equivalent non-used edge in self """
	if len(Remaining)  == 0:
		return True
		
	#No solution if there are more edges remaining then there are available edges
	if len(Remaining) > len(Available):
		return False

	other_edge = Remaining.pop()
	print('constraints remaining ', len(Remaining))
	for prospect in Available:
		if prospect.isEquivalent(other_edge):
			A = {item for item in Available if not (item is prospect)}
			if (rDetectEquivalentEdgeGraph(Remaining, A)):
				return True
	return False
	
