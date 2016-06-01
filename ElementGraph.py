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
	
	
	def possible_mergers(self, other):
		
		completed = self.absolve(other, other.edges, self.edges)
		for element_graph in completed:
			element_graph.constraints = other.constraints
		return completed
	
	def absolve(self, other, Remaining = set(), Available = set(), Collected = set()):
		""" Every edge from other must be consistent with some edge in self.
			An edge from self cannot account for more than one edge from other
			
				Remaining: edges left to account for in other
				Available: edges in 'first' self, which cannot account for more than one edge
				
				USAGE: Excavate_Graph.absolves(other, other.edges, self.edges, Collected)
		"""
		if len(Remaining)  == 0:
			Collected.add(self)
			return Collected
			
		other_edge = Remaining.pop()
		print('remaining ', len(Remaining))

		for prospect in Available:
			if other_edge.isConsistent(prospect):
				new_self=  self.assimilate(other,prospect, other_edge)
				Collected = new_self.absolve(other, Remaining,Available-{prospect},Collected)

		print('collected ', len(Collected))
		return Collected
		
	
	def assimilate(self, other, old_edge, other_edge):
		"""	Provided with old_edge consistent with other_edge
			Merges source and sinks
		"""
		new_self = self.copyGen()
		self_source = new_self.getElementById(old_edge.source.id)			#source from new_self
		self_source.merge(other_edge.source)								#source merge
		self_sink = new_self.getElementById(old_edge.sink.id)				#sink from new_self
		self_sink.merge(other_edge.sink)									#sink merge
		return new_self
		

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
	