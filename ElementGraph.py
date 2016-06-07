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

	def swap(self, source, other):
		""" source is root of partial step in self, other is other which absolved source.Action
		
				purpose: 	for each element in other, 
							if element.replaced_id is sink in an edge in self.edges
							replace sink of edge with element
							
							Note: 	its already the case that all edges in self where edge.source in self.edges
									is an element in other has been replaced, or else the getElementGraphFromElement
									made an error
							
							For each new element and edge in other, need to add those to self as well
							
		"""
		#print('swapping into {}'.format(self.id))
		#print('other ought to be the operator: {}'.format(other.id))
		""" For all edges that go into old self, replace those with edges that go into new self
			For all edges that start from old self, replace those with edges that originate from new self
		"""
		for element in other.elements:
			for edge in self.edges:
				
				#edge.print_edge()
				#if not edge.sink is None:
				#	print('{} swap in {} at source {}; element.replaced_id {} == edge.sink.id {}'.format(self.id, other.id, source.id, element.replaced_id, edge.sink.id))
				if element.replaced_id == edge.sink.id:
					print('Edge ({}--{}-->{}) \treplacing sink {} with {}'.format(edge.source.id, edge.label, edge.sink.id, edge.sink.id, element.id))

					sink = self.getElementById(edge.sink.id)
					element.merge(edge.sink)
					edge.swapSink(element)
					self.elements.add(element)
				
					if sink in self.elements:
						self.elements.remove(sink)

				if element.replaced_id == edge.source.id:
					print('Edge ({}--{}-->{}) \treplacing source {} with {}'.format(edge.source.id, edge.label, edge.sink.id, edge.source.id, element.id))
					
					source = self.getElementById(edge.source.id)
					element.merge(edge.source)
					edge.swapSource(element)
					
					self.elements.add(element)
					
					if source in self.elements:
						self.elements.remove(source)
					

		""" For all new elements in new self, add those to old self. Add all brand new edges as well"""
		for edge in other.edges:
			
			new_edge = False
			
			if edge.sink.replaced_id == -1: #-1 means the element is new and was not replaced
				self.elements.add(edge.sink)
				#print('new element {}'.format(edge.sink.id))
				new_edge =True
					
			if edge.source.replaced_id == -1:
				self.elements.add(edge.source)
				#print('new element {}'.format(edge.source.id))
				new_edge = True
				
			if new_edge:
				#print('New Edge ', end= " ")
				#edge.print_edge()
				self.edges.add(edge)
		
		
		return self
		
	def getInstantiations(self, other):
		""" self is operator, other is partial step"""
		print('{}x{}.get Instances given partial step ({}x{})'.format(self.id, self.type, other.id, other.type))
		#print('ought to be 200xAction.possible_mergers(111xAction) or 3001xAction.possible_mergers(2111xAction)')
		#operator = self.copyGen()
		
		for element in self.elements:
			element.replaced_id = -1
					#operator.absolve(partial, partial.edges, operator.available_edges)
		completed = self.absolve(other, copy.deepcopy(other.edges), self.edges, set())
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other.id, self.id))
		return completed	
	
	def possible_mergers(self, other, completed = set()):
		""" self is operator, other is partial step"""
		print('\n{}x{}.possible_mergers({}x{})'.format(self.id, self.type, other.id, other.type))
		operator = self.copyGen()
		other = other.copyGen()
		for element in operator.elements:
			element.replaced_id = -1
			
	
		completed = operator.absolve(other, other.edges, operator.edges, set())
	#	print('completed absolvings: {}'.format(len(completed)))
		if len(completed) == 0:
			print('no completed instantiations of {} with operator {}'.format(other.id, self.id))
		for element_graph in completed:
			element_graph.updateActionParams() #only will work if this is action
			element_graph.constraints = other.constraints
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
			
		#print('PRE collected ', len(Collected))
	#	print('\n ABSOLVE remaining ', len(Remaining))
		other_edge = Remaining.pop()
	#	print('{}.absolve({})... {} --{}--> {} needs replacement \n'.format(self.id, other.id, other_edge.source.id, other_edge.label, other_edge.sink.id))
		num_collected_before = len(Collected)
		#other_edge.print_edge()
		
		for prospect in Available:
			if other_edge.isConsistent(prospect):
	#			print('\nstep {} edge {} --{}--> {} matches {} --{}--> {}\n'.format(other.id, other_edge.source.id, other_edge.label, other_edge.sink.id, prospect.source.id, prospect.label, prospect.sink.id))
				new_self=  self.assimilate(other, prospect, other_edge)
				#new_self.print_graph()
				#Collected = new_self.absolve(other, Remaining,Available-{prospect},Collected)
				potential = new_self.absolve(other.copyGen(), copy.deepcopy(Remaining), copy.deepcopy(Available), copy.deepcopy(Collected))
				Collected.update(potential)					

	#	print('collected {}'.format(len(Collected)))
		
		if len(Collected) == 0:
			return set()
			
		if len(Collected) > num_collected_before:
			return Collected
		else:
	#		print('\nbackup bitch\n')
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
	