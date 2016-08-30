from Restrictions import *
import uuid

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""

	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None, Restrictions=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()

		super(ElementGraph, self).__init__(ID, type_graph, name, Elements, Edges, Restrictions)
		self.root = root_element

	def copyGen(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid1(21)
		return new_self

	def copyWithNewIDs(self, from_this_num):
		new_self = self.copyGen()
		for element in new_self.elements:
			element.ID = from_this_num
			from_this_num = from_this_num + 1
		return new_self

	@classmethod
	def makeElementGraph(cls, elementGraph, element):
		edges = copy.deepcopy(elementGraph.rGetDescendantEdges(element))
		elms = {edge.source for edge in edges}|{edge.sink for edge in edges}
		element_copy = next(iter(elm for elm in elms if elm.ID == element.ID))
		return cls(element.ID, element.typ, name=None, root_element=element_copy,Elements= elms, Edges = edges,
				   Restrictions=elementGraph.restrictions)

	def getElementGraphFromElement(self, element, Type=None):
		if Type == None:
			Type = eval(element.typ)
		if self.root == element:
			return self.copyGen()
		return Type.makeElementGraph(self, element)

	def getElementGraphFromElementID(self, element_ID, Type = None):
		return self.getElementGraphFromElement(self.getElementById(element_ID), Type)

	def preventThreatWithRestriction(self, threat, condition):
		"""
		"""
		R = Restriction()
		edge_pairs = {(e1, e2) for e1 in self.getIncidentEdges(threat) for e2 in self.getIncidentEdges(condition)
						if e1.label == e2.label and e1.sink != e2.sink}
		if len(edge_pairs) == 0:
			return False

		t_edge, c_edge = next(iter(edge_pairs))
		R.elements.add(c_edge.source)
		R.elements.add(t_edge.sink)
		R.edges.add(Edge(c_edge.source, t_edge.sink, t_edge.label))
		self.restrictions.add(R)
		return True
		# for ce in condition_edges:
		# 	for te in threat_edges:
		# 		if ce.label != te.label and ce.sink != te.sink:
		# 			R.elements.add(threat)
		# 			R.elements.add(ce.sink)
		# 			R.edges.add(Edge(te.source, ce.sink, ce.label))
		# 			return

		# R.elements.add(threat)
		# for threat_edge in self.getIncidentEdges(threat):
		# 	if threat_edge.sink.name is None:
		# 		R.edges.add(Edge(condition, threat_edge.sink, threat_edge.label))
		# 		R.elements.add(threat_edge.sink)
		# if len(R.edges) == 0:
		# 	R.elements.add(condition)
		# 	for condition_edge in self.getIncidentEdges(condition):
		# 		if condition_edge.sink.name is None:
		# 			R.edges.add(Edge(threat, condition_edge.sink, condition_edge.label))
		# 			R.elements.add(condition_edge.sink)
		# if len(R.edges) == 0:
		# 	return None


	# def addNonCodesignationConstraints(self, elm1, elm2):
	# 	''' Adds a constraint edge to prevent elm1 from being a legal merge with elm2
	# 		Strategy depends that two preconditions or two effects of the same step could not be non-codesignated
	# 		Also does not take into account future edges which are given the same edge-label
	# 		TODO: more robust anti-merge strategy
	# 	'''
	# 	# could pick more specific edge. some edges could be 'unique' in that no other outgoing/incoming edge label is same
	#
	# 	#Revisited :
	# 	cndts1 = {edge.sink for edge in self.getNeighbors(elm1) if edge.sink.name is None}
	# 	cndts2 = {edge.sink for edge in self.getNeighbors(elm2) if edge.sink.name is None}
	# 	if len(cndts1) + len(cndts2) == 0:
	# 		return None
	#
	# 	elm2_edges = self.getIncidentEdges(elm2)
	#
	# 	#If any edge
	# 	# for edge in self.getIncidentEdges(elm1):
	# 	# 	if not edge.sink in self.getNeighborsByLabel(elm2, edge.label):
	#
	#
	#
	# 	prnt = next(iter(edge for edge in self.edges if edge.sink.ID == elm1.ID))
	# 	self.restrictions.add(Restriction(Elements = {prnt.source, prnt.label, elm2}, Edges = {Edge(prnt.source, elm2,
	# 																					prnt.label)}))

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
				element.replaced_ID = element.ID
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
			print('\n\nno completed instantiations of {} with operator {}\n\n'.format(other, self))

		for element_graph in completed:
			# element_graph.updateActionParams() #only will work if this is action
			element_graph.restrictions = copy.deepcopy(other.restrictions)
		return completed

	def updateArgs(self):
		argTyps = {Argument, Actor}
		self.Args = set()
		for element in self.rGetDescendants(self.root):
			if type(element) in argTyps:
				self.Args.add(element)

	def absolve(self, Remaining=None, Available=None, Collected=None):
		""" Every edge from other must be consistent with some edge in self.
			An edge from self cannot account for more than one edge from other.
				
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