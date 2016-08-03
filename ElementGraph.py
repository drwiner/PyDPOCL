from Graph import *


class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""

	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None, Constraints=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()

		super(ElementGraph, self).__init__(ID, type_graph, name, Elements, Edges, Constraints)
		self.root = root_element
		self.neqs = set()

	def copyGen(self):
		return copy.deepcopy(self)

	def copyWithNewIDs(self, from_this_num):
		new_self = self.copyGen()
		for element in new_self.elements:
			element.ID = from_this_num
			from_this_num = from_this_num + 1
		return new_self

	@classmethod
	def makeElementGraph(cls, elementGraph, element):
		return cls(element.ID, element.typ, name=None,Elements =elementGraph.rGetDescendants(element),  root_element =element,   Edges =elementGraph.rGetDescendantEdges(element),Constraints=elementGraph.rGetDescendantConstraints(element))

	def getElementGraphFromElement(self, element, Type=None):
		if Type == None:
			Type = element.typ
		if self.root.ID == element.ID:
			return self.copyGen()
		return Type.makeElementGraph(self, element)

	def getElementGraphFromElementID(self, element_ID, Type):
		return self.getElementGraphFromElement(self.getElementById(element_ID), Type)

	def addNonCodesignationConstraints(self, elm1, elm2):
		''' Adds a constraint edge to prevent elm1 from being a legal merge with elm2
			Strategy depends that two preconditions or two effects of the same step could not be non-codesignated
			Also does not take into account future edges which are given the same edge-label
			TODO: more robust anti-merge strategy
		'''
		# could pick more specific edge. some edges could be 'unique' in that no other outgoing/incoming edge label is same
		prnt = next(iter(edge for edge in self.edges if edge.sink.ID == elm1.ID))
		self.constraints.add(Edge(prnt.source, elm2, prnt.label))

	def mergeGraph(self, other, no_add=None):
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
				if no_add is None:
					self.elements.add(element)
					element.replaced_ID = element.ID

		if no_add is None:
			for edge in other.edges:
				source = self.getElementById(edge.source.replaced_ID)
				sink = self.getElementById(edge.sink.replaced_ID)
				existing_edges = {E for E in self.edges if
								  E.source == source and E.sink == sink and E.label == edge.label}
				if len(existing_edges) == 0:
					self.edges.add(Edge(source, sink, edge.label))

		return self

	def getInstantiations(self, other):
		""" self is operator, other is partial step 'Action'
			self is effect, other is precondition of existing step
			Returns all possible ways to unify self and other, 
				may result in changes to self
		"""

		for element in self.elements:
			element.replaced_ID = -1
		for elm in other.elements:
			elm.replaced_ID = -1

		completed = self.absolve(copy.deepcopy(other.edges), self.edges)
		if len(completed) == 0:
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other.ID, self.ID))

		for element_graph in completed:
			# element_graph.updateActionParams() #only will work if this is action
			element_graph.constraints = copy.deepcopy(other.constraints)
		return completed

	def updateArgs(self):
		argTyps = {Argument, Actor}
		self.Args = set()
		for element in self.rGetDescendants(self.root):
			if type(element) in argTyps:
				self.Args.add(element)

	def absolve(self, Remaining=None, Available=None, Collected=None):
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

		if len(Remaining) == 0:
			Collected.add(self)
			return Collected

		other_edge = Remaining.pop()
		num_collected_before = len(Collected)

		for prospect in Available:
			if other_edge.isConsistent(prospect):
				new_self = self.assimilate(prospect, other_edge)
				if new_self.isInternallyConsistent():
					Collected.update(new_self.absolve({copy.deepcopy(rem) for rem in Remaining}, Available, Collected))

		if len(Collected) == 0:
			return set()

		if len(Collected) > num_collected_before:
			return Collected
		else:
			return set()

	def assimilate(self, old_edge, other_edge):
		"""	ProvIDed with old_edge consistent with other_edge
			Merges source and sinks
			Uses = {'new-step', 'effect'}
			"new-step" Self is operator, old_edge is operator edge, other is partial step
			"effect": self is plan-graph, old edge is effect edge, other is eff_abs 
		"""

		new_self = self.copyGen()
		self_source = new_self.getElementById(old_edge.source.ID)  # source from new_self
		self_source.merge(other_edge.source)  # source merge
		self_source.replaced_ID = other_edge.source.ID
		self_sink = new_self.getElementById(old_edge.sink.ID)  # sink from new_self
		self_sink.replaced_ID = other_edge.sink.ID
		self_sink.merge(other_edge.sink)  # sink merge
		return new_self


def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element, set())
	Elements = G.rGetDescendants(element, set())
	Constraints = G.rGetDescendantConstraints(element, set())
	return Type(element.ID, \
				type_graph=element.typ, \
				name=element.name, \
				Elements=Elements, \
				root_element=element, \
				Edges=Edges, \
				Constraints=Constraints \
				)
