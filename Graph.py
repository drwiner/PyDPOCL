from Element import *
import copy

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

	def isEquivalent(self, other):
		if self.source.isEquivalent(other.source) and self.sink.isEquivalent(other.sink) and self.label == other.label:
			return True
		return False
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		"""Merges source and sink"""

		#Assume edges are consistent
		if not self.isConsistent(other):
			return None
			
		self.source.merge(other.source)
		self.sink.merge(other.sink)
		
		return self
	
	def swapSource(self,source):
		self.source= source
		return self
	
	def swapSink(self,sink):
		self.sink = sink
		return self
		
	#def print_edge(self):
		#self.source.print_element()
		#print(self.label)
		#self.sink.print_element()
		
	def print_edge(self):
		print('Edge {} --{}--> {}'.format(self.source.id, self.label, self.sink.id))

class Graph(Element):
	"""A graph is an element with elements, edges, and constraints"""
	def __init__(self, id, type, name = None, \
		Elements = None, Edges = None, Constraints = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()
		
		super(Graph,self).__init__(id,type,name)
		self.elements = Elements
		self.edges = Edges;
		self.constraints = Constraints
		
	def print_graph(self):
		print('ElementGraph {}:'.format(self.id))
		for edge in self.edges:
			print('Edge {} --{}--> {}'.format(edge.source.id, edge.label, edge.sink.id))
			#edge.source.print_element()
			#edge.sink.print_element()
		for element in self.elements:
			if type(element) is Literal:
				print('Element {id} = {truth}{name},\ttype = {type}'.format(id=element.id, truth='not ' if not element.truth else '', name=element.name, type=element.type))
			elif type(element) is Operator:
				print('Element {id} = {truth}{name},\ttype = {type}'.format(id=element.id, truth='not ' if element.executed==False else '', name=element.name, type=element.type))
			else:
				print('Element {} = {},\ttype = {}'.format(element.id, element.name, element.type))
	
	def print_graph_names(self):
		print('ElementGraph {}:'.format(self.name))
		for edge in self.edges:
			if type(edge.sink) is Literal:
				print('Edge {} --{}--> {}-{}'.format(edge.source.name, edge.label, edge.sink.truth, edge.sink.name))
			if type(edge.source) is Literal:
				print('Edge {}-{} --{}--> {}'.format(edge.source.truth, edge.source.name, edge.label,edge.sink.name))
			else:
				print('Edge {} --{}--> {}'.format(edge.source.name, edge.label,edge.sink.name))
			#edge.source.print_element()
			#edge.sink.print_element()
		for element in self.elements:
			if type(element) is Literal:
				print('Element {truth}{name},\ttype = {type}'.format(truth='not ' if not element.truth else '', name=element.name, type=element.type))
			elif type(element) is Operator:
				print('Element {truth}{name},\ttype = {type}'.format(truth='not ' if element.executed==False else '', name=element.name, type=element.type))
			else:
				print('Element {} ,\ttype = {}'.format(element.name, element.type))
	
	def hasEdgeIdentity(self, edge):
		""" Returns set of edges s.t. (source.id, label, sink.id) in self.edges"""
		return self.getEdgesByIdsAndLabel(edge.source.id, edge.sink.id, edge.label)
		
	def hasConstraintIdentity(self, edge):
		return self.getConstraintsByIdsAndLabel(edge.source.id, edge.sink.id, edge.label)
	
	def addEdgeByIdentity(self, edge):
		""" Assumes edge not in Graph
			Finds elements with edge.source.id and edge.sink.id
			Adds edge between them with edge.label
		"""
		source = self.getElementById(edge.source.id)
		sink = self.getElementById(edge.sink.id)
		label = edge.label
		self.edges.add(Edge(source, sink, label))
		
	def addConstraintByIdentity(self, edge):
		source = self.getElementById(edge.source.id)
		sink = self.getElementById(edge.sink.id)
		label = edge.label
		self.constraints.add(Edge(source, sink, label))
	
	def getElementById(self, id):
		for element in self.elements:
			if element.id == id:
				return element
		return None
		
	def addConstraint(self, edge):
		if edge not in self.constraints:
			self.constraints.add(edge)
			
	def replaceWith(self, element, other):
		if self.getElementById(other.id) is None:
			self.elements.add(other)
		self.elements.remove(element)
		for outgoing in self.getIncidentEdges(element):
			outgoing.source = other
		for incoming in  {edge for edge in self.edges if edge.sink.id == element.id}
			incoming.sink = other
		return self
			
	def getEdgesByIdsAndLabel(self, source_id, sink_id, label):
		return {edge for edge in self.edges if edge.source.id == source_id and edge.sink.id == sink_id and edge.label == label}
		
	def getConstraintsByIdsAndLabel(self, source_id, sink_id, label):
		return {edge for edge in self.constraints if edge.source.id == source_id and edge.sink.id == sink_id and edge.label == label}
			
	def getIncidentEdges(self, element):
		return {edge for edge in self.edges if edge.source.id == element.id}
	def getNeighbors(self, element):
		return {edge.sink for edge in self.edges if edge.source.id == element.id}
	def getParents(self, element):
		return set(edge.source for edge in self.edges if edge.sink is element)
	def getNeighborsByLabel(self, element, label):
		return {edge.sink for edge in self.edges if edge.source.id == element.id and edge.label == label}
	def getIncidentEdgesByLabel(self, element, label):
		return {edge for edge in self.edges if edge.source.id == element.id and edge.label == label}
	def getParentsByLabel(self, element, label):
		return set(edge.source for edge in self.edges if edge.sink is element and edge.label is label)
	def getConstraints(self, element):
		return {edge for edge in self.constraints if edge.source.id == element.id}
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
		
	def rGetDescendantsGenerator(self, element, Descendants = None):
		if Descendants == None:
			Descendants = set()
		""" TODO: test this generator"""
		#Base Case
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			yield element
			
		#Induction
		for edge in incidentEdges:
			yield element
			return self.rGetDescendants(edge.sink, Descendants)
	
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
		
	def rGetDescendantConstraints(self, constraint_source, Descendant_Constraints = None):
		if Descendant_Constraints == None:
			Descendant_Constraints = set()
		#Base Case
		incident_constraints = self.getConstraints(constraint_source)
		if len(incident_constraints) == 0:
			return Descendant_Constraints
		
		#Induction
		Descendant_Constraints=Descendant_Constraints.union(incident_constraints)
		for c in incident_constraints:
			Descendant_Constraints = self.rGetDescendantConstraints(c.sink, \
																	Descendant_Constraints\
																	)
			
		return Descendant_Constraints
	
	
	################  Consistency ###############################
	def canAbsolve(self, other):
		""" A graph absolves another iff for each other.edge, there is a consistent self.edge
		"""
		if rDetectConsistentEdgeGraph(Remaining = copy.deepcopy(other.edges), Available = copy.deepcopy(self.edges)):
			print('consistent without constraints')
			if not self.equivalentWithConstraints(other):
				print('consistent with constraints')
				return True
		return False
		
	def isInternallyConsistent(self):
		constraint_sources = self.getConstraintSources()
		for cs in constraint_sources:
			suspects = {edge.source for edge in self.edges if edge.source.id == cs.id}
			if len(suspects) == 0:
				print('no suspects for constraint source {}'.format(cs.id))
				continue
			cg = self.rGetDescendantConstraints(cs)
			for sp in suspects:
				sg = self.rGetDescendantEdges(sp)
				if rDetectEquivalentEdgeGraph(copy.deepcopy(cg),copy.deepcopy(sg)):
					print('suspect {} not consistent with constraints from source {}'.format(sp.id,cs.id))
					return False

		return True
		
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
		
	def elementsAreEquivalent(self, other, self_element, other_element):
		""" Elements in different graphs (self vs other) are equivalent 
		if edge path from self_element has superset of edge path from other_element"""
		if not self_element.isEquivalent(other_element):
			return False
		
		descendant_edges = self.rGetDescendantEdges(self_element)
		other_descendant_edges = other.rGetDescendantEdges(other_element)
		return rDetectEquivalentEdgeGraph(other_descendant_edges, descendant_edges)

	def getConstraintSources(self):
		"""Constraints sources are constraint elements which are not sinks
		"""
		sinks = {constraint.sink for constraint in self.constraints}
		return {constraint.source for constraint in self.constraints if constraint.source not in sinks}

			
		
	######       Constraints       ####################
	def equivalentWithConstraints(self, other):
		"""
			1) For each constraint source (propogate to source)
			2) Find equivalent suspect (if none, move on)
			3) Make constraint graph
			4) Make operator subgraph from suspect
			5) Determine if constraint equivalency via rDetectEquivalentEdges
		"""
		constraint_sources = other.getConstraintSources()
		for cs in constraint_sources:
			suspects = {edge.source for edge in self.edges if edge.source.isEquivalent(cs)}
			if len(suspects) == 0:
				print('no suspects for constraint source {}'.format(cs.id))
				continue
			cg = other.rGetDescendantConstraints(cs)
			for sp in suspects:
				sg = self.rGetDescendantEdges(sp)
				if rDetectEquivalentEdgeGraph(copy.deepcopy(cg),copy.deepcopy(sg)):
					print('suspect {} not consistent with constraints from source {}'.format(sp.id,cs.id))
					return True

		return False
		
	# def old_equivalent_with_constraints(self, other):
			
		# for c in other.constraints:
			# #First, narrow down edges to just those which are equivalent with constraint source
			# suspects = {edge.source \
							# for edge in self.edges \
							# if edge.source.isEquivalent(c.source)\
						# }
			# for suspect in suspects:
				# print('suspect: (', suspect.id, 'has ', c.label, '-', c.sink.type, ')')
				# if self.constraintEquivalentWithElement(other, \
														# suspect, \
														# c.source\
														# ):
					# return True
		# return False	
		
	# def constraintEquivalentWithElement(self, other, self_element, constraint_element):
		# """ Returns True if element and constraint have equivalent descendant edge graphs"""
		# #Assumes self_element is equivalent with constraint_element, but just in case
		# if not self_element.isEquivalent(constraint_element):
			# return False
		# print('equiv')
		# descendant_edges = self.rGetDescendantEdges(self_element)
		# constraints = other.rGetDescendantConstraints(constraint_element)
		# for c in constraints:
			# c.print_edge()
		# #Equivalent if we can find an equivalent edge graph
		# return rDetectEquivalentEdgeGraph(copy.deepcopy(constraints), copy.deepcopy(descendant_edges))
		
def rDetectConsistentEdgeGraph(Remaining = None, Available = None):
	if Remaining == None:
		Remaining = set()
	if Available == None:
		Available = set()
		
	""" Returns True if all remaining edges can be assigned a consistent non-used edge in self """
	if len(Remaining)  == 0:
		return True
		
	# #No solution if there are more edges remaining then there are available edges
	# if len(Remaining) > len(Available):
		# return False

	other_edge = Remaining.pop()
	print('remaining ', len(Remaining))
	#print('available ', len(Available))
	for prospect in Available:
		#print('prospect ,', prospect.source.id, ' ', 	prospect.label, ' ', 	prospect.sink.id)
		#print('other_edge ,', other_edge.source.id, ' ', other_edge.label, ' ', 	other_edge.sink.id)
		if prospect.isConsistent(other_edge):
			if rDetectConsistentEdgeGraph(	Remaining, \
											{item \
												for item in Available - {prospect}\
											}):
				return True
	return False
	
def rDetectEquivalentEdgeGraph(Remaining = None, Available = None):
	if Remaining == None:
		Remaining = set()
	if Available == None:
		Available = set()
	""" Returns True if all remaining edges can be assigned an equivalent non-used edge in self 
	"""
	if len(Remaining)  == 0:
		return True
		
	#No solution if there are more edges remaining then there are available edges
	if len(Remaining) > len(Available):
		return False

	other_edge = Remaining.pop()
	print('constraints remaining ', len(Remaining))
	other_edge.print_edge()
	for prospect in Available:
		if prospect.isEquivalent(other_edge):
			#print('\nequivalence detected: constraint (above) and operator edge:')
			#prospect.print_edge()
			#print('\n')
			if rDetectEquivalentEdgeGraph(	Remaining, \
											{item \
												for item in Available \
													if not item is prospect\
											}):
				return True

	return False
	
