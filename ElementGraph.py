from Graph import *
import copy

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
		self.root = root
		
	def copyGen(self):
		yield copy.deepcopy(self)
		
	def getElementGraphFromElement(self, element, Type):
		if self.root is element:
			return self
		
		return Type(element.id, \
					type='element %s' %subgraph, \
					name=self.name,\
					Elements = self.rGetDescendants(element),\
					root_element = element,\
					Edges = self.rGetDescendantEdges(element),\
					Constraints = self.rGetDescendantConstraints(element)\
					)
			
	def mergeEdgesFromSource(self, other, edge_source, mergeable_edges = set()):
		""" Treats all edges as unique, does not merge the edges, merges source"""
		if edge_source.merge(other.root) is None:
			return None
			
		new_incident_edges = {Edge(\
									edge_source, \
									edge.sink, \
									edge.label\
									) \
									for edge in mergeable_edges\
							}
		self.edges.union_update(new_incident_edges)
		for new_edge in new_incident_edges:
			self.elements.add(new_edge.sink)
			self.elements.union_update(other.rGetDescendants(new_edge.sink)) #Try using Generator
			
			self.edges.union_update(other.rGetDescendantEdges(new_edge.sink))
			self.constraints.union_update(other.rGetDescendantConstraints(new_edge.sink))
	
		return self	
			
	def mergeAt(self, other, edge_source):		
		return self.mergeFromEdges(	other, \
									edge_source, \
									other.getIncidentEdges(other.root)\
								)
		
	def getConsistentEdgePairs(self, incidentEdges, otherEdges):
		return {(edge,other_edge) \
									for edge in incidentEdges \
									for other_edge in otherEdges \
												if edge.isCoConsistent(other)\
				}
				
	def getInconsistentEdges(self, other_edges, consistent_edge_pairs):
		"""Returns set, because parameter mergeable edges in mergeEdgesFromSource takes set"""
		return {other_edge \
					for other_edge in otherEdges \
						if other_edge not in \
							(oe for (e,oe) in consistent_edge_pairs\
						)\
				}
			
	def rMerge(self, other, self_element, consistent_merges = set()):
		""" Returns set of consistent merges, which are Edge Graphs of the form self.merge(other)""" 
		#self_element.merge(other_element)
		
		#Get next edges
		otherEdges = other.getIncidentEdges(other.root)
		
		#BASE CASE
		if len(otherEdges) == 0:
			return consistent_merges.add(self)
			
		
		consistent_edge_pairs = self.getConsistentEdgePairs(self.getIncidentEdges(self_element), \
															otherEdges\
															)
															

		#If they're all inconsistent, then let's just get to den, aye?
		if len(consistent_edge_pairs) == 0:
			if self.mergeAt(self_element,other) is None:
				return consistent_merges
			return consistent_merges.add(self)
			
		#INDUCTION	
		
		#First, merge inconsistent other edges, do this on every path
		self.mergeEdgesFromSource(	other, \									#other 
									self.element, \								#self_element
									getInconsistentEdges(\						#mergeable_edges
														otherEdges,\			
														consistent_edge_pairs\
														)\
									) 
		
		#Assimilation Merge: see if we can merge the sinks.
		consistent_merges.union_update({\
										self.copyGen().rMerge(\
																other.getElementGraphFromElement(o.sink,o.sink.type), \ 	#other
																e.sink, \ 													#self_element
																consistent_merges\											#consistent_merges
															) \
															for (e,o) in consistent_edge_pairs \
										})
										
		#For each pair of consistent edges, create a copy of self and see what happens if we merge sinks and rMerge onward
		#For each consistent_edge, try assimilating, and try accomodating. For each one that works,
		for e,oe in consistent_edge_pairs:
			new_self = self.copyGen()
			new_self.root.merge(other.root)
			self.getElementGraphFromElement(e.sink, e.sink.type)
			new_other  = other.getElementGraphFromElement(oe.sink,oe.sink.type)
			consistent_merges.union_update(new_self.rMerge(new_other,e.sink,consistent_merges))

		#Accomodation Merge: see if we can add the sink's element graph
		#Don't check if type is literal, because if edges are consistent, \
			#then they share label, and literals have unique labels
		if not type(self_element) == Literal:
			for (e,o) in consistent_edge_pairs:
				take_other = self.copyGen().mergeEdgesFromSource(other, \			#other
																self_element, \		#edge_source
																{o}\				#mergeable_edges
																)
				consistent_merges = take_other.rMerge(\
														other.getElementGraphFromElement(o.sink,o.sink.type), \	#other
														e.sink, \												#self_element 
														consistent_merges\										#consistent_merges
													)
	
		return consistent_merges
		

def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element)
	Elements = G.rGetDescendants(element)
	Constraints = G.rGetDescendantConstraints(element)
	return Type(element.id,\
				type = element.type, \
				name=element.name, \
				Elements = Elements, \
				root_element = element,\
				Edges = Edges, \
				Constraints = Constraints\
				)
	