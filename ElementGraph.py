from Graph import *

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	
	def __init__(self,ID,type_graph,name=None, Elements = None, root_element = None, Edges = None, Constraints = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()
			
		super(ElementGraph,self).__init__(\
											ID,\
											type_graph,\
											name,\
											Elements,\
											Edges,\
											Constraints\
										)
		self.root = root_element		
		self.neqs = set()
		
	def copyGen(self):
		return copy.deepcopy(self)

	def copyWithNewIDs(self, from_this_num):
		new_self= self.copyGen()
		for element in new_self.elements:
			element.ID = from_this_num 
			from_this_num = from_this_num+1
		return new_self

	@classmethod
	def makeElementGraph(cls, elementGraph, element):
		return cls(				element.ID, \
								element.typ, \
								name=None,\
								Elements = elementGraph.rGetDescendants(element),\
								root_element = element,\
								Edges = elementGraph.rGetDescendantEdges(element),\
								Constraints = elementGraph.rGetDescendantConstraints(element))
					
		
	def getElementGraphFromElement(self, element, Type):
		if self.root.ID == element.ID:
			return self.copyGen()
		return Type.makeElementGraph(self,element)
		
	def getElementGraphFromElementID(self, element_ID, Type):
		return self.getElementGraphFromElement(self.getElementById(element_ID),Type)
		
	def mergeGraph(self, other):
		"""
			For each element in other to include in self, if its a replacer, merge it into self
					A relacer element 'replacer' is one such that replacer.replaced_ID == some element ID in self
			Otherwise, add that element to self
			For each edge in other to include in self, if its in self do nothing, otherwise add it
		
			Plan.mergeGraph(instance), where instance is "other". 
					Other is a graph where some elements in the graph are "replacing" elements in self
					
			Precondition.mergeGraph(Effect) where the Effect is a Condition which has instantiated a precondition of S_{need}
					Effect has some elements (arguments) which replaced elements in the operator clone
					This method will merge the originals in the operator giving them the extra properties in the replacees of Effect
					
			Graph.mergeGraph(new_operator) where new_operator has replaced some elements in graph.
					Then, if its a new element, add it. If its a replacer, merge it. 
					For each edge in new_operator, if 
					
		"""
		for element in other.elements:
			if not hasattr(element, 'replaced_ID'):
				element.replaced_ID = -1
				
			if element.replaced_ID != -1:
					existing_element = self.getElementById(element.replaced_ID)
					existing_element.merge(element)
					existing_element.replaced_ID = element.ID
			else:
				self.elements.add(element)
				element.replaced_ID = element.ID
		
		for edge in other.edges:
			source = self.getElementById(edge.source.replaced_ID)
			sink = self.getElementById(edge.sink.replaced_ID)
			existing_edges = {E for E in self.edges if E.source.ID == source.ID and E.sink.ID == sink.ID and E.label == edge.label}
			#existing_edges = self.getEdgesByIDsAndLabel(source.ID, sink.ID, edge.label)
			if len(existing_edges) > 1 :
				print('multiple edges {}--{}--> {}; in plan {} trying to merge {}'.format(edge.source.replaced_ID, edge.label, edge.sink.replaced_ID, self.ID, other.ID))
			if len(existing_edges) == 0:
				self.edges.add(Edge(source, sink, edge.label))
				
		return self

		
	def getInstantiations(self, other):
		""" self is operator, other is partial step 'Action'
			self is effect, other is precondition of existing step
			Returns all possible ways to unify self and other, 
				may result in changes to self
		"""
		print('{}x{}.get Instances given partial element graph ({}x{})'.format(self.ID, self.typ, other.ID, other.typ))
		#print('ought to be 200xAction.possible_mergers(111xAction) or 3001xAction.possible_mergers(2111xAction)')
		#operator = self.copyGen()
		
		for element in self.elements:
			element.replaced_ID = -1
					#operator.absolve(partial, partial.edges, operator.available_edges)
		completed = self.absolve(copy.deepcopy(other.edges), self.edges)
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other.ID, self.ID))
			
		for element_graph in completed:
			# element_graph.updateActionParams() #only will work if this is action
			element_graph.constraints = copy.deepcopy(other.constraints)
		return completed	

	
	def absolve(self, Remaining = None, Available = None, Collected = None):
		""" Every edge from other must be consistent with some edge in self.
			An edge from self cannot account for more than one edge from other? 
				
				Remaining: edges left to account for in other
				Available: edges in 'first' self, which cannot account for more than one edge
				
				USAGE: Excavate_Graph.absolves(partial_step, partial_step.edges, self.edges, Collected)
				
				Returns: Set of copies of Operator which absolve the step (i.e. merge)
		"""
		
		if Remaining == None:
			Remaining = set()
		if Available == None:
			Available = set()
		if Collected == None:
			Collected = set()
		
		if len(Remaining)  == 0:
			Collected.add(self)
			return Collected
			

		other_edge = Remaining.pop()
		#print('{}.absolve({})... {} --{}--> {} needs replacement \n'.format(self.ID, other.ID, other_edge.source.ID, other_edge.label, other_edge.sink.ID))
		num_collected_before = len(Collected)
		
		for prospect in Available:
			if other_edge.isConsistent(prospect):
				#check if constraints violated?
			#	print('\nstep {} edge {} --{}--> {} matches {} --{}--> {}\n'.format(other.ID, other_edge.source.ID, other_edge.label, other_edge.sink.ID, prospect.source.ID, prospect.label, prospect.sink.ID))
				new_self=  self.assimilate(prospect, other_edge)
				if new_self.isInternallyConsistent():
					Collected.update(new_self.absolve({copy.deepcopy(rem) for rem in Remaining}, Available, Collected))					
		
		if len(Collected) == 0:
			return set()
			
		if len(Collected) > num_collected_before:
			return Collected
		else:
			return set()
			

			
	def legalMerge(self, element, other):
		'''element in self, is other on neq list?'''
		if not element.isConsistent(other):
			return False
		if other.ID in self.neqs[element.ID]:
			return False
		return True
		
	
	def assimilate(self, old_edge, other_edge):
		"""	ProvIDed with old_edge consistent with other_edge
			Merges source and sinks
			Self is usually operator, other is partial step
		"""

		new_self = self.copyGen()
		self_source = new_self.getElementById(old_edge.source.ID)			#source from new_self
		self_source.merge(other_edge.source)								#source merge
		self_source.replaced_ID = other_edge.source.ID
		self_sink = new_self.getElementById(old_edge.sink.ID)				#sink from new_self
		self_sink.replaced_ID = other_edge.sink.ID
		self_sink.merge(other_edge.sink)									#sink merge
		return new_self
		

def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element, set())
	Elements = G.rGetDescendants(element, set())
	Constraints = G.rGetDescendantConstraints(element, set())
	return Type(	element.ID,\
					type_graph = element.typ, \
					name=element.name, \
					Elements = Elements, \
					root_element = element,\
					Edges = Edges, \
					Constraints = Constraints\
				)
	