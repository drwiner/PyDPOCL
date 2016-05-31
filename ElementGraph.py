from Graph import *

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	
	def __init__(self,id,type,name=None, Elements = set(), root_element = None, Edges = set(), Constraints = set()):
		super(ElementGraph,self).__init__(\
											id,\
											type,\
											name,\
											Elements,\
											Edges,\
											Constraints\
										)
		self.root = root_element		
		
	def copyGen(self):
		return copy.deepcopy(self)
		
	@classmethod
	def from_scratch(cls, id, type, name, elements, root, edges, constraints):
		return cls(		root.id,\
						root.type,\
						name,\
						elements,\
						root,\
						edges,\
						constraints)
	
	@classmethod
	def makeElementGraph(cls, elementGraph, element):
		return cls(				element.id, \
								element.type, \
								name=None,\
								Elements = elementGraph.rGetDescendants(element),\
								root_element = element,\
								Edges = elementGraph.rGetDescendantEdges(element),\
								Constraints = elementGraph.rGetDescendantConstraints(element))
					
		
	def getElementGraphFromElement(self, element, Type):
		if self.root.id == element.id:
			return self.copyGen()
			
		return Type.makeElementGraph(self,element)
								
		# return ElementGraph	(id=element.id, \
								# type= element.type, \
								# name=None,\
								# Elements = self.rGetDescendants(element),\
								# root_element = element,\
								# Edges = self.rGetDescendantEdges(element),\
								# Constraints = self.rGetDescendantConstraints(element)\
								# )
					
	def swap(self, source, other):
		"""	SWAP: 	
					For every descendant d of source, find d' which has same ID
						If it doesn't exist, add d' to self
						otherwise, d.merge(d')
					For every descendant edge d' --> y'
						If there is no edge d --> y in self.edges, add d --> y
						otherwise, do nothing
						
			Purpose:
					Other is consistent subgraph with root equivalent to source
					Merging other with self at source is a consistent_merge
			Check:	
					If elementGraph is an operator, make sure to mergeArgs
		"""
		#descendants = self.rGetDescendants(source)
		self_ids = {descendant.id for descendant in self.elements}
		other_ids = {element.id for element in other.elements}
		#New ids are other_ids which are not in self_ids
		new_ids = other_ids - self_ids.intersection(other_ids)
		
		print("\nNEW IDs")
		for id in new_ids:
			print(id)
		print("\n")
		#If d'.id == d.id, then merge
		merged_elements = {d.merge(d_prime) for d in self.elements for d_prime in other.elements if d_prime.id == d.id}
		#If there is no d' s.t. d'.id == d.id then add d'
		new_elements = {d_prime for d_prime in other.elements if d_prime.id in new_ids}
		#descendants.update(new_elements)
		self.elements.update(new_elements)
		
		#Add Missing Edges
		descendantEdges = self.rGetDescendantEdges(source)
		{self.addEdgeByIdentity(edge) for edge in other.edges if not self.hasEdgeIdentity(edge)}
		
		#Add Missing Constraints (problem: all constraint elements must be in self.elements)
		descendantConstraints = self.rGetDescendantConstraints(source)
		{self.addConstraintByIdentity(edge) for edge in other.constraints if not self.hasConstraintIdentity(edge)}
		return self
		
	def rAddNewDescendants(self, other, other_source):
		""" for each new descendant sink with an unencountered id
			add that element and the edge that took us there
			recursively 
		"""
		element_ids = {element.id for element in self.elements}
		new_edges = {edge \
							for edge in other.edges \
								if other_source.id == edge.source.id \
								and edge.sink.id not in element_ids}
									
		#BASE CASE:
		if len(new_edges) == 0:
			return self
			
		#INDUCTION
		self.edges.update(new_edges)
		{self.elements.add(new_edge.sink) for new_edge in new_edges}
		{self.rAddNewDescendants(other,new_edge.sink) for new_edge in new_edges}
		
		return self
			
	def mergeEdgesFromSource(self, other, edge_source, mergeable_edges = set()):
		""" Accommodates, does not merge the edges, merges source
			If mergeable_edge.sink is not in self.elements,
				then recursively get its edges via sinks not in self.elements
			mergeEdgesFromSource: 	
					First things first, merge the roots
					For every edge of mergeable_edges,
						
						if we can't find the sink
							add the sink to the elements
						else
							self_sink.merge(other_sink)
							
						add edge
						
			Purpose:
					Merge inconsistent other edges from edge_source
					Then, 

		"""
		if edge_source.merge(other.root) is None:
			return None
			
		if len(mergeable_edges) == 0:
			return None
			
		new_incident_edges = {edge.swapSource(edge_source) for edge in mergeable_edges}
		
		self.edges.update(new_incident_edges)
	
		for new_edge in new_incident_edges:
			self.elements.add(new_edge.sink)
			self.elements.update(other.rGetDescendants(new_edge.sink)) #Try using Generator
			
			self.edges.update(other.rGetDescendantEdges(new_edge.sink))
			self.constraints.update(other.rGetDescendantConstraints(new_edge.sink))
	
		return self		
			
	def mergeAt(self, other, edge_source):
		""" Steals all edges from other, adds edges to edges_source
		 All edges are 'Accomodated' 
		 """
		return self.mergeEdgesFromSource(	other, \
											edge_source, \
											other.getIncidentEdges(other.root)\
										)
		
	def getConsistentEdgePairs(self, incidentEdges, otherEdges):
		return {(edge,other_edge) \
					for edge in incidentEdges \
							for other_edge in otherEdges \
									if edge.isConsistent(other)\
				}
				
	def getInconsistentEdges(self, otherEdges, consistent_edge_pairs):
		"""	Returns an edge from otherEdges if its not in consistent_edge_pairs
		"""
		return {other_edge \
					for other_edge in otherEdges \
						if other_edge not in \
							(oe for (e,oe) in consistent_edge_pairs\
						)\
				}
	
	def assimilate(self, other, old_self_sink, other_sink, consistent_merges = set()):
		new_self = self.copyGen()
		self_sink = new_self.getElementById(old_self_sink.id)
		self_sink.merge(other_sink)
		return new_self.rMerge(other, self_sink, other_sink, consistent_merges)
		
	#### This would entail, do this for each consistent sink
	def assimilateNewEdge(self, other, self_source, consistent_sink, other_edge, consistent_merges = set()):
		new_self = self.copyGen()
		self_sink = new_self.getElementById(consistent_sink.id)
		self_sink.merge(other_edge.sink)
		new_self.edges.add(Edge(self_source, self_sink, other_edge.label))
		return new_self.rMerge(other, self_sink, other_edge.sink, consistent_merges)
	
	def accommodate(self, other, other_edge, consistent_merges = set()):
		new_self = self.copyGen()
		self_sink = copy.deepcopy(other_edge.sink)
		self.elements.add(self_sink)
		return new_self.rMerge(other, self_sink, other_edge.sink, consistent_merges)
		
	def accomodateNewEdge(self, other, self_source, other_edge, consistent_merges = set()):
		new_self = self.copyGen()
		self_sink = copy.deepcopy(other_edge.sink)
		self.elements.add(self_sink)
		new_self.edges.add(Edge(self_source, self_sink, other_edge.label))
		return new_self.rMerge(other, self_sink, other_edge.sink, consistent_merges)
	
	def Merge(self, other):
		return self.rMerge(other, self.root)
	
	
	def rMerge(self, other, self_element, other_element, consistent_merges = set()):
		""" Returns set of consistent merges, which are Edge Graphs of the form self.merge(other)
					
					Base case: 	other has no incident edges, 
								and therefore, we can merge this with self_element and return
								Reaching base case means the assimilation/accomodation strategy was successful
					
					Induction: 
							Case 1 incident edge is consistent with some other edge
							Case 2 incident edge sink is consistent with some self.element (but no consistent edge)
							Case 3 incident edge is inconsistent with any edge (i.e. no consistent sink)
							
							Methods:
								A)	self_sink.merge(other_sink)
								B)	create element (and add to elements)
								C)	add edge to self_sink
								
							
							Case 1:
								1) A 				- Assimilate
								2) B then C			- Accomodate
							Case 2:
								1) A then C			- Assimilate
								2) B then C			- Accomodate
							Case 3:
								1) B then C			- Accomodate
								

		""" 
		#self_element.merge(other_element)
		
		#Get next edges
		otherEdges = other.getIncidentEdges(other.root)
		print('how many incident edges: ', len(otherEdges))
		
		#BASE CASE
		if len(otherEdges) == 0:
			return {self}
			
		#INDUCTION
		
		consistent_edge_pairs	= 	self.getConsistentEdgePairs(self.getIncidentEdges(self_element),otherEdges)
		inconsistent_edges		= 	self.getInconsistentEdges(otherEdges,consistent_edge_pairs)
		
		#new_merges are merges that were recursively successful at commitment to assimilate vs accomodate
		#But, says nothing about 
		new_merges	=set()				
		
		#Case 1
		for e, oe in consistent_edge_pairs:
			#Assimilate
				""" A """ 
				new_merges.update(self.assimilate(other, e.sink, oe.sink, consistent_merges))
			#Accomodate
				""" B then C"""
				new_merges.update(self.accomodateNewEdge(other, e.sink, oe, consistent_merges))
				
		#Cases 2-3
		for ie in inconsistent_edges:
			#Assimilate Case 2
				""" A then C""" 
				prospects = {consistent_element for consistent_element in self.elements if consistent_element.isConsistent(ie.sink)}
				new_merges.update({self.accomodateNewEdge(other, self_element, prospect, ie, consistent_merges) for prospect in prospects})
			#Accomodate Case 2
			
			
															
		#If they're all inconsistent, then let's just get to den, aye?
		if len(consistent_edge_pairs) == 0:
			if self.mergeAt(other, self_element) is None:
				return None
			return {self}
			
		#INDUCTION	
		
		#First, merge inconsistent other edges, do this on every path
		self.mergeEdgesFromSource(	other, \
									self.element, \
									self.getInconsistentEdges(\
															otherEdges,\
															consistent_edge_pairs\
															)\
									) 
										
		#For each pair of consistent edges, create a copy of self and see what happens if we merge sinks and rMerge onward
		#For each consistent_edge, try assimilating, and try accomodating. For each one that works,
		edge_mapper = {}
		for e,oe in consistent_edge_pairs:
			accomodate_self = self.getElementGraphFromElement(e.sink, e.sink.type)
			assimilate_self = self.getElementGraphFromElement(e.sink, e.sink.type)
			to_merge 		= other.getElementGraphFromElement(oe.sink, oe.sink.type)
	
			#Can we rMerge from the sinks? (Let this be the same edge)
			assimilate_merges = assimilate_self.rMerge(to_merge)
			
			#Can we accomodate this new edge (let this be a new edge)
			
			if not type(e.sink) == Literal\
				and not accomodate_self.mergeEdgesFromSource(	other, \
																e.sink, \
																{o}\
															) 	is None:
				accomodate_merges = accomodate_self.rMerge(to_merge)
			else:
				accomodate_merges = set()
				
			if len(assimilate_merges) ==0 and len(accomodate_merges) == 0:
				"""e.sink has no consistent merge with other.sink"""
				print('e.sink has no consistent merge with other.sink')
				return None
			
			edge_mapper[e.sink].update(assimilate_merges)
			edge_mapper[e.sink].update(accomodate_merges)
		
		#Then, for each entry edge, pick a merge and move on. If we get through the whole thing, then we've found a consistent_merge
		
		return self.rCreateConsistentMerges(	set(edge_mapper.keys()),\
												edge_mapper,\
												consistent_merges\
											)
											
		#return consistent_merges
	
	def rCreateConsistentMerges(self, 	sinks_remaining = set(), \
										edge_mapper = {}, \
										complete_merges = set()):
		""" Given a set of sinks and a set of strategies per sink, 
			Find a strategy per sink, swap in strategy in self.copy
		"""
		#Base Case				
		if len(sinks_remaining) == 0:
			return self

		sink = sinks_remaining.pop()
		# complete_merges.update	({\
				# self.copyGen().swap(sink,strategy).\
					# rCreateConsistentMerges	(\
											# sinks_remaining,\
											# edge_mapper,\
											# complete_merges\
											# )\
									 # for strategy in edge_mapper[sink]\
									# })
								
		strategies = edge_mapper[sink]
		for strategy in edge_mapper[sink]:
			self_copy = self.copyGen()
			#Swap: given strategy/graph, pin the root onto sink element
			self_copy.swap(sink, strategy)
			complete_merges.update(self_copy.rCreateConsistentMerges(	sinks_remaining,\
																		edge_mapper,\
																		complete_merges))
			
		return complete_merges


def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element)
	Elements = G.rGetDescendants(element)
	Constraints = G.rGetDescendantConstraints(element)
	return Type(	element.id,\
					type = element.type, \
					name=element.name, \
					Elements = Elements, \
					root_element = element,\
					Edges = Edges, \
					Constraints = Constraints\
				)
	