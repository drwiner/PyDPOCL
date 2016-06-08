from Graph import *

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	
	def __init__(self,id,type_graph,name=None, Elements = None, root_element = None, Edges = None, Constraints = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()
			
		super(ElementGraph,self).__init__(\
											id,\
											type_graph,\
											name,\
											Elements,\
											Edges,\
											Constraints\
										)
		self.root = root_element		
		
	def copyGen(self):
		return copy.deepcopy(self)

	def copyWithNewIDs(self, from_this_num):
		new_self= self.copyGen()
		for element in new_self.elements:
			element.id = from_this_num 
			from_this_num = from_this_num+1
		return new_self

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
		
	def getElementGraphFromElementId(self, element_id, Type):
		return self.getElementGraphFromElement(self.getElementById(element_id),Type)
		
	def mergeGraph(self, other):		
		for element in other.elements:
			if element.replaced_id != -1:
				existing_element = self.getElementById(element.replaced_id)
				existing_element.merge(element)
			else:
				#############################################################################
				if type(element) is Operator:
					print('element {} is type operator but replaced_id = -1'.format(element.id))
				#############################################################################
				self.elements.add(element)
				element.replaced_id = element.id
		
		for edge in other.edges:
			source = self.getElementById(edge.source.replaced_id)
			sink = self.getElementById(edge.sink.replaced_id)
			existing_edges = {E for E in self.edges if E.source.id == source.id and E.sink.id == sink.id and E.label == edge.label}
			#existing_edges = self.getEdgesByIdsAndLabel(source.id, sink.id, edge.label)
			if len(existing_edges) > 1 :
				print('multipled edges {}--{}--> {}; in plan {} trying to merge {}'.format(edge.source.replaced_id, edge.label, edge.sink.replaced_id, self.id, other.id))
			if len(existing_edges) == 0:
				self.edges.add(Edge(source, sink, edge.label))
				
		return self

		
	def getInstantiations(self, other):
		""" self is operator, other is partial step 'Action'"""
		print('{}x{}.get Instances given partial step ({}x{})'.format(self.id, self.type, other.id, other.type))
		#print('ought to be 200xAction.possible_mergers(111xAction) or 3001xAction.possible_mergers(2111xAction)')
		#operator = self.copyGen()
		
		for element in self.elements:
			element.replaced_id = -1
					#operator.absolve(partial, partial.edges, operator.available_edges)
		completed = self.absolve(other, copy.deepcopy(other.edges), self.edges)
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other.id, self.id))
			
		# for element_graph in completed:
			# element_graph.updateActionParams() #only will work if this is action
			# element_graph.constraints = other.constraints
		return completed	

	
	def absolve(self, other, Remaining = None, Available = None, Collected = None):
		if Remaining == None:
			Remaining = set()
		if Available == None:
			Available = set()
		if Collected == None:
			Collected = set()
		""" Every edge from other must be consistent with some edge in self.
			An edge from self cannot account for more than one edge from other? 
				
				Remaining: edges left to account for in other
				Available: edges in 'first' self, which cannot account for more than one edge
				
				USAGE: Excavate_Graph.absolves(partial_step, partial_step.edges, self.edges, Collected)
				
				Returns: Set of copies of Operator which absolve the step (i.e. merge)
		"""
		if len(Remaining)  == 0:
			Collected.add(self)
			return Collected
			

		other_edge = Remaining.pop()
		#print('{}.absolve({})... {} --{}--> {} needs replacement \n'.format(self.id, other.id, other_edge.source.id, other_edge.label, other_edge.sink.id))
		num_collected_before = len(Collected)
		
		for prospect in Available:
			if other_edge.isConsistent(prospect):
			#	print('\nstep {} edge {} --{}--> {} matches {} --{}--> {}\n'.format(other.id, other_edge.source.id, other_edge.label, other_edge.sink.id, prospect.source.id, prospect.label, prospect.sink.id))
				new_self=  self.assimilate(other, prospect, other_edge)
				Collected.update(new_self.absolve(other, {copy.deepcopy(rem) for rem in Remaining}, Available, Collected))					
		
		if len(Collected) == 0:
			return set()
			
		if len(Collected) > num_collected_before:
			return Collected
		else:
			return set()
		
	
	def assimilate(self, other, old_edge, other_edge):
		"""	Provided with old_edge consistent with other_edge
			Merges source and sinks
			Self is usually operator, other is partial step
		"""

		new_self = self.copyGen()
		self_source = new_self.getElementById(old_edge.source.id)			#source from new_self
		self_source.merge(other_edge.source)								#source merge
		self_source.replaced_id = other_edge.source.id
		self_sink = new_self.getElementById(old_edge.sink.id)				#sink from new_self
		self_sink.replaced_id = other_edge.sink.id
		self_sink.merge(other_edge.sink)									#sink merge
		return new_self
		

def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element, set())
	Elements = G.rGetDescendants(element, set())
	Constraints = G.rGetDescendantConstraints(element, set())
	return Type(	element.id,\
					type_graph = element.type, \
					name=element.name, \
					Elements = Elements, \
					root_element = element,\
					Edges = Edges, \
					Constraints = Constraints\
				)
	