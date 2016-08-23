from Element import *
import copy

class Edge:
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
		return hash((self.source.ID, self.sink.ID, self.label))
		
	def merge(self, other):
		"""Merges source and sink"""

		if not self.isConsistent(other):
			return None
			
		self.source.merge(other.source)
		self.sink.merge(other.sink)
		
		return self
	
	def swapSink(self,sink):
		self.sink = sink
		return self
		
	def __repr__(self):
		return 'Edge {} --{}--> {}'.format(self.source, self.label, self.sink)

class Graph(Element):
	"""A graph is an element with elements, edges, and restrictions"""
	def __init__(self, ID, typ, name = None, Elements = None, Edges = None, Restrictions = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()
		
		super(Graph,self).__init__(ID,typ,name)
		self.elements = Elements
		self.edges = Edges
		self.restrictions = Restrictions
	
	def getElementById(self, ID):
		for element in self.elements:
			if element.ID == ID:
				return element
		return None
	
	def getElementByReplacedId(self, ID):
		for element in self.elements:
			if hasattr(element, 'replaced_ID'):
				if element.replaced_ID == ID:
					return element
		return None

			
	def replaceWith(self, oldsnk, newsnk):
		''' removes oldsnk from self.elements, replaces all edges with snk = oldsnk with newsnk'''
		if oldsnk == newsnk:
			return
		if self.getElementById(newsnk.ID) is None:
			raise NameError('newsnk replacer is not found in self')
		if oldsnk in self.elements:
			self.elements.remove(oldsnk)
		for incoming in (edge for edge in self.edges if edge.sink == oldsnk):
			incoming.sink = newsnk
		#update constraint edges which might reference specific elements being replaced
		for edge in self.constraints:
			if edge.source == oldsnk:
				edge.source = newsnk
			if edge.sink == oldsnk:
				edge.sink = newsnk
		return self

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
		
	######       rGet       ####################
	def rGetDescendants(self, element, Descendants = None):
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

	def rGetDescendantEdges(self, element, Descendant_Edges = None):
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
	
	################  Consistency ###############################
	def canAbsolve(self, other):
		""" A graph absolves another iff for each other.edge, there is a consistent self.edge
		"""
		if rDetectConsistentEdgeGraph(Remaining = copy.deepcopy(other.edges), Available = copy.deepcopy(self.edges)):
			if not self.equivalentWithRestrictions():
				return True
		return False
		
	def isInternallyConsistent(self):
		return self.equivalentWithRestrictions()
		
	def coAbsolvant(self, other):
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
		

	def equivalentWithRestrictions(self):
		for restriction in self.restrictions:
			if restriction.isIsomorphicSubgraphOf(self):
				return True
		return False

	def __repr__(self):
		edges = str([edge for edge in self.edges])
		elms = str([elm for elm in self.elements])
		return '\n' + edges + '\n\n_____\n\n ' + elms + '\n'
		
def rDetectConsistentEdgeGraph(Remaining = None, Available = None):
	""" Returns True if all remaining edges can be assigned a consistent non-used edge in self
		TODO: investigate if possible problem: two edges p1-->p2-->p3 are consistent with edges q1-->q2 q2'-->q3 just when q2 == q2'
				this method will succeed, incorrectly, when q2 neq q2'
			  -- This hasn't been a problem, because most edge labels have unique labels in a graph
			  -- should create test conditions - in ElementGraph -- to test if "canAbsolve" always means that we will return something with "getInstantiations"
	"""
	if Remaining == None:
		Remaining = set()
	if Available == None:
		Available = set()
		

	if len(Remaining)  == 0:
		return True

	other_edge = Remaining.pop()

	for prospect in Available:
		if prospect.isConsistent(other_edge):
			if rDetectConsistentEdgeGraph(	Remaining, {item for item in Available - {prospect}}):
				return True
	return False
	
