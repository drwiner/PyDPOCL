from Graph import *

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	
	def __init__(self,id,type_graph,name=None, Elements = set(), root_element = None, Edges = set(), Constraints = set()):
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
		print('swapping into {}'.format(self.id))
		print('other ought to be the operator: {}'.format(other.id))
		
		for element in other.elements:
			for edge in self.edges:
				if element.replaced_id == edge.sink.id:
					#print('replacing sink {} with {}'.format(edge.sink.id, element.id))
					sink = self.getElementById(edge.sink.id)
					print('Edge ({}--{}-->{}) \treplacing sink {} with {}'.format(edge.source.id, edge.label, edge.sink.id, edge.sink.id, element.id))
					edge.swapSink(element)
					#""" For every sink we replace, make sure we update all of its incident edges"""
					#for other_edges in self.getIncidentEdges(edge.sink):
						#if other_edges.source.id == edge.sink.id:
					#print('replacing sink {} with {}'.format(edge.sink.id, element.id))
					self.elements.add(element)
				
					if sink in self.elements:
						self.elements.remove(sink)
						#print('removing sink {}'.format(edge.sink.id))
						
					#print('\nsink swap')
					#edge.print_edge()
					#edge.sink.print_element()
				if element.replaced_id == edge.source.id:
					#print('replacing source {} with {}'.format(edge.source.id, element.id))
					print('Edge ({}--{}-->{}) \treplacing source {} with {}'.format(edge.source.id, edge.label, edge.sink.id, edge.source.id, element.id))
					source = self.getElementById(edge.source.id)
					edge.swapSource(element)
					
					if source in self.elements:
						#print('removing source {}'.format(edge.source.id))
						self.elements.remove(source)
					#print('\nsource swap')
					self.elements.add(element)
					#edge.print_edge()
					#edge.source.print_element()
					
		for edge in other.edges:
			new_edge = False
			if edge.sink.replaced_id == -1: #-1 means the element is new
				self.elements.add(edge.sink)
				new_edge =True
			if edge.source.replaced_id == -1:
				self.elements.add(edge.source)
				new_edge = True
			if new_edge:
				self.edges.add(edge)
		
		
		return self
		
	def getInstantiations(self, other):
		""" self is operator, other is partial step"""
		print('{}x{}.possible_mergers({}x{})'.format(self.id, self.type, other.id, other.type))
		print('ought to be 200xAction.possible_mergers(111xAction) or 3001xAction.possible_mergers(2111xAction)')
		#operator = self.copyGen()

		for element in self.elements:
			element.replaced_id = -1
					#operator.absolve(partial, partial.edges, operator.available_edges)
		completed = self.absolve(other, other.edges, self.edges, set())
		if len(completed) == 0:
			print('no completed instantiations of {} with operator {}'.format(other.id, self.id))
		return completed	
	
	def possible_mergers(self, other, completed = set()):
		""" self is operator, other is partial step"""
		print('{}x{}.possible_mergers({}x{})'.format(self.id, self.type, other.id, other.type))
		print('ought to be 200xAction.possible_mergers(111xAction) or 3001xAction.possible_mergers(2111xAction)')
		operator = self.copyGen()

		for element in operator.elements:
			element.replaced_id = -1
			
	
		completed = operator.absolve(other, copy.deepcopy(other.edges), operator.edges)
	#	print('completed absolvings: {}'.format(len(completed)))
		if len(completed) == 0:
			print('no completed instantiations of {} with operator {}'.format(other.id, self.id))
		for element_graph in completed:
			element_graph.updateActionParams() #only will work if this is action
			element_graph.constraints = other.constraints
		return completed
	
	def absolve(self, other, Remaining = set(), Available = set(), Collected = set()):
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
		print('remaining ', len(Remaining))
		other_edge = Remaining.pop()
		print('{}.absolve({})... {} --{}--> {} needs replacement'.format(self.id, other.id, other_edge.source.id, other_edge.label, other_edge.sink.id))
		num_collected_before = len(Collected)
		#other_edge.print_edge()
		for prospect in Available:
			if other_edge.isConsistent(prospect):
				print('step {} edge {} --{}--> {} matches {} --{}--> {}'.format(other.id, other_edge.source.id, other_edge.label, other_edge.sink.id, prospect.source.id, prospect.label, prospect.sink.id))
				new_self=  self.assimilate(other, prospect, other_edge)
				#new_self.print_graph()
				#Collected = new_self.absolve(other, Remaining,Available-{prospect},Collected)
				Collected = new_self.absolve(other, Remaining,Available,Collected)
		print('collected ', len(Collected))
		
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
	