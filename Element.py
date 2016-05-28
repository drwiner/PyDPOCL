
		
class Element:
	def __init__(self, id, type = None, name = None):
		self.id = id
		self.type = type
		self.name = name
		
	def isConsistent(self, other):
		#""" Returns True if self and other have same name or unassigned"""
		if not other.type is None:
			if self.type != other.type:
				return False
		return True
		
	def isIdentical(self, other):
		if self.id == other.id:
			if self.isEquivalent(other):
				return True
		return False
		
	def isEquivalent(self, other):
		if self.type == other.type:
			return True
		return False
	
	def isProperty(self, other, property):
		return self.property(other)
		
			
		
class InternalElement(Element):
	def __init__(self, id, type, name = None, num_args = 0):
		super(InternalElement,self).__init__(id,type,name)
		self.num_args = num_args
		
	# def isEquivalent(self, other):
		# if self.type == other.type and self.name == other.name and self.num_args == other.num_args:
			# return True
		# return False
	
	def isEquivalent(self, other):
		# for each incident edge of other, there is a unique equivalent edge of self
		# and for each constraint of other, there is no uniqe equivalent edge of self
		if not (super(InternalElement,self).isEquivalent(other) \
			and self.name == other.name \
			and self.num_args == other.num_args):
			return False
			
		#out_incident_edges = {edge for edge in }
	
	def isConsistent(self, other):
	
		#If other has a type, then return False if they are not the same
		if not super(InternalElement,self).isConsistent(other):
			return False
				
		#If other has an argument number, then return False if they are not the same
		if other.num_args > 0:
			if self.num_args != other.num_args:
				return False
	
		#If other has a predicate name, then return False if they are not the same
		if not other.name is None:
			if self.name != other.name:
				return False
				
		return True
		
				
		
class Operator(InternalElement):
	def __init__(self, id, type, name = None, num_args = 0, executed = None):
		super(Operator,self).__init__(id,type,name, num_args)
		self.executed = executed
		
		
class Literal(InternalElement):
	def __init__(self, id, type, name = None, num_args = 0, truth = None):
		super(Literal,self).__init__(id,type,name, num_args)
		self.truth = truth

	def isConsistent(self, other):
		if not super(Literal,self).isConsistent(other):
			return False
				
		if not other.truth is None:
			if self.truth != other.truth:
				return False
				
		return True

	def isCoConsistent(self, other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
		
	def isEquivalent(self,other):
		if self.name == other.name and self.type == other.type:
			return True
		return False
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False

		
class Argument(Element):
	def __init__(self, id, type, name= None, arg_pos_dict = {}):
		super(Argument,self).__init__(id,type,name)
		self.arg_pos_dict = arg_pos_dict
		self.position = position
		
	def isConsistent(self, other):
		if not super(Argument,self).isConsistent(other):
			return False
		if other.id in other.arg_pos_dict:
			if other.arg_pos_dict[other.id] != self.arg_pos_dict[self.id]:
				return False
		return True
	
	def isEquivalent(self, other):
		if super(Argument,self).isEquivalent(other) and self.position == other.position:
			return True
		return False
		

class Graph(Element):
	def __init__(self, id, type, name = None, Elements = set(), Edges = set(), Constraints = set()):
		super(Graph,self).__init__(id,type,name)
		self.elements = Elements
		self.edges = Edges;
		self.constraints = Constraints
		
	def addEdge(self, edge):
		if edge not in self.edges:
			self.edges.add(edge)
		
	def addConstraint(self, edge):
		if edge not in self.constraints:
			self.constraints.add(edge)
			
	def merge(self, other):
		#Danger of a union is that we'll represent consistent elements twice.
		#check if two steps with nonempty intersection can be merged
		#For just literals first:
		if 
			
	def getIncidentEdges(self, element):
		return {edge for edge in self.edges if edge.source is element}
	def getNeighbors(self, element):
		return set(edge.sink for edge in self.edges if edge.source is element)
	def getParents(self, element):
		return set(edge.source for edge in self.edges if edge.sink is element)
	def getNeighborsByLabel(self, element, label):
		return set(edge.sink for edge in self.edges if edge.source is element and edge.label is label)
	def getIncidentEdgesByLabel(self, element, label):
		return set(edge for edge in self.edges if edge.source is element and edge.label is label)
	def getParentsByLabel(self, element, label):
		return set(edge.source for edge in self.edges if edge.sink is element and edge.label is label)
	def getConstraints(self, element):
		return {edge for edge in self.constraints if edge.source is element}
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
		
	def rGetDescendants(self, element, Descendants = set()):
	
		#Base Case
		incidentEdges = self.getIncidentEdges(element)
		if len(incidentEdges) == 0:
			return element
			
		#Induction
		for edge in incidentEdges:
			Descendants.add(element)
			Descendants = self.rGetDescendants(edge.sink, Descendants)
		return Descendants
	
	def rGetDescendantEdges(self, element, Descendant_Edges = set()):
		#Base Case
		incident_Edges = self.getIncidentEdges(element)
		if len(incident_Edges) == 0:
			return Descendant_Edges
		
		#Induction
		Descendant_Edges=Descendant_Edges.union(incident_Edges)
		for edge in incident_Edges:
			Descendant_Edges = self.rGetDescendantEdges(edge.sink, Descendant_Edges)
			
		return Descendant_Edges
			
		
	def equivalentWithConstraints(self, other):
		for c in other.constraints:
			#First, narrow down edges to just those which are equivalent with constraint source
			suspects = {edge.source for edge in self.edges if edge.source.isEquivalent(c.source)}
			for suspect in suspects:
				print('suspect id: ', suspect.id)
				if self.constraintEquivalentWithElement(other, suspect, c.source):
					return True
		return False
		
		
	def constraintEquivalentWithElement(self, other, self_element, constraint_element):
		""" Returns True if element and constraint have equivalent descendant edge graphs"""
		#Assumes self_element is equivalent with constraint_element, but just in case
		if not self_element.isEquivalent(constraint_element):
			return False
		
		descendant_edges = self.rGetDescendantEdges(self_element)
		constraints = other.rGetDescendantConstraints(constraint_element)
		return rDetectEquivalentEdgeGraph(constraints, descendant_edges)
		
		
	def rGetDescendantConstraints(self, constraint_source, Descendant_Constraints = set()):
		#Base Case
		incident_constraints = self.getConstraints(constraint_source)
		if len(incident_constraints) == 0:
			return Descendant_Constraints
		
		#Induction
		Descendant_Constraints=Descendant_Constraints.union(incident_constraints)
		for c in incident_constraints:
			Descendant_Constraints = self.rGetDescendantConstraints(c.sink, Descendant_Constraints)
			
		return Descendant_Constraints
	
	###############################################################
	def isConsistent(self, other):
		""" Returns True if for every edge in other_graph, there is some consistent edge in self"""
		if rDetectConsistentEdgeGraph(Remaining = other.edges, Available = self.edges):
			print('consistent without constraints')
			if not self.equivalentWithConstraints(other):
				print('consistent with constraints')
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
		
def rDetectConsistentEdgeGraph(Remaining = set(), Available = set()):
	""" Returns True if all remaining edges can be assigned an equivalent non-used edge in self """
	if len(Remaining)  == 0:
		return True
		
	#No solution if there are more edges remaining then there are available edges
	if len(Remaining) > len(Available):
		return False

	other_edge = Remaining.pop()
	print('remaining ', len(Remaining))
	for prospect in Available:
		if prospect.isConsistent(other_edge):
			A = {item for item in Available if not (item is prospect)}
			if (rDetectConsistentEdgeGraph(Remaining, A)):
				return True
	return False
	
def rDetectEquivalentEdgeGraph(Remaining = set(), Available = set()):
	""" Returns True if all remaining edges can be assigned an equivalent non-used edge in self """
	if len(Remaining)  == 0:
		return True
		
	#No solution if there are more edges remaining then there are available edges
	if len(Remaining) > len(Available):
		return False

	other_edge = Remaining.pop()
	print('constraints remaining ', len(Remaining))
	for prospect in Available:
		if prospect.isEquivalent(other_edge):
			A = {item for item in Available if not (item is prospect)}
			if (rDetectEquivalentEdgeGraph(Remaining, A)):
				return True
	return False
	
def extractSubgraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element)
	Elements = G.rGetDescendants(element)
	Constraints = G.rGetDescendantConstraints(element)
	return Type(element.id,type = 'subgraph',Elements,Edges,Constraints)

class Belief(Graph):
	def __init__(self, id, type, name=None, Elements=set(), Edges = set(), Constraints = set()):
		super(Belief, self).__init__(Elements, Edges, Constraints)
		self.id = id
		self.type= type
		self.name = name
	
	# def isEquivalent(other_belief):
		# if self.story_element.isEquivalent(other_belief.story_element) \
		# and other_belief.story_element.isEquivalent(self.story_element):
			# return True:
		# return False
		
class Action(Graph):
	""" Action Graph: for step graph"""
	def __init__(self, id, type, name=None, Elements=set(), Edges=set(), Constraints = set()):
		super(Action,self).__init__(Elements,Edges,Constraints)
		self.id = id
		self.type = type
		self.name = name
		
	"""Determine if two Actions can be joined by a causal link"""
	def isConsistentAntecedentFor(self, action):
		effects = {egde.sink for edge in self.edges if edge.label == 'effect-of'}
		if len(effects) == 0:
			return False
		preconditions = {edge.sink for edge in self.edges if edge.label == 'precond-of'}
		if len(preconditions) == 0:
			return False
		prospects = {(eff,pre) for eff in effects for pre in preconditions if eff.isCoConsistent(pre)}
		if len(prospects)  == 0:
			return False
		return prospects
	
		
class Condition(Graph):
	""" A Literal used in causal link"""
	def __init__(self,id,type,name=None,Elements=set(), Edges = set(), Constraints = set()):
		super(Condition,self).__init__(Elements,Edges,Constraints)
		self.id = id
		self.type = type
		self.name  name
		
	def merge(self, other):
		#Do not assume equivalent, assume only consistency
		if not self.isEqual(other):
			if not self.isConsistent(other) and other.isConsistent(self):
				print('could not merge conditions')
				return False
			else:
				
		
def literalsToCondition(G1, G2, literal_1, literal_2, checked=False):
	if not checked and not literal_1.isCoConsistent(literal_2):
		return False
	
	if literal_1.name is None:
		name = literal_2.name
	else:
		name = literal_1.name
		
	
	if literal_1.num_args is None:
		if literal_2.num_args is None:
			print('need to put num_args in literals')
		else:
			num_args = literal_2
	else:
		num_args = literal_1.num_args
	
	#get elements and edges recursively from literal_1 in G_1
	L1 = extractSubgraphFromElement(G1,literal_1,Literal)
	L2 = extractSubgraphFromElement(G2,literal_2,Literal)
	
	edge 
	{edge for edge in L1.edges if edge.label is 'first-arg'}
	L1.merge(L2)
	return Condition(id=literal_1.id, type='condition')
	
	
		
class CausalLink(Edge):
	""" A causal link is an edge, s.t. the source and sink are actions, and the condition is itself an edge between a dummy element
		and the dependency literal element, rather than just a label"""
	def __init__(self, id, type, name=None, action1, action2, condition):
		super(CausalLink,self).__init__(source=action1,sink=action2,label=condition.id)
		self.id = id
		self.type = type
		self.name = name
		self.dependency = condition #A literal element#
		
	def isInternallyConsistent(self):
		effects = {egde.sink for edge in self.edges if edge.label == 'effect-of' and edge.sink.id == self.condition.id}
		if len(effects) == 0:
			return False
		preconditions = {edge.sink for edge in self.edges if edge.label == 'precond-of' and edge.sink.id == self.condition.id}
		if len(preconditions) == 0:
			return False
		return True
		
	
	#def possiblyThreatenedBy(self,action):
	
	def threatenedBy(self,action):
		action_orderings = getOrderingsWith(action)
		
#Do I need this?
class Binding(Edge):
	def __init__(self, id, type, name=None, element1, element2, binding_type):
		super(Binding,self).__init__(element1,element2,binding_type)
		self.X = element1
		self.Y = element2
		self.id = id
		self.type = type
		self.name = name
		
	def isInternallyConsistent(self):
		if self.source.isIdentical(self.sink):
			return True
		
class Ordering(Edge):
	def __init__(self,action1,action2):
		super(Ordering, self).__init__(action1,action2,'<')
		
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

class Subplan(Element):
	def __init__(self,id,type,name=None,causal_links):
		super(Subplan,self).__init__(id,type,name)
		self.causal_links
		self.steps = {step.source for step in self.causal_links}.union({self.sink for step in self.causal_links})

class Motivation(Literal):
	def __init__(self, id, type='motivation', name='intends', num_args = 1, truth = True, intender, goal):
		super(Motivation,self).__init__(id,type,name,num_args,truth)
		self.actor = intender
		self.goal = goal
		
class IntentionFrame(Element):
	def __init__(self, id, type, name=None, actor, ms, goal, sat, subplan):
		super(IntentionFrame,self).__init__(id,type,name)
		self.ms = ms
		self.actor = actor
		self.goal = goal
		self.sat = sat
		self.subplan = subplan
		self.motivation = Motivation(id, intender=self.actor, goal = self.goal)
		
		
	def isInternallyConsistent(self):
		for effect in self.sat.getEffects():
			if not self.goal.isConsistent(effect):
				return False
		for step in self.subplan.steps:
			if not step.isAntecedent(self.sat,self.subplan.causal_links):
				return False
			if not self.actor in step.getActors():
				return False
		if not self.actor in self.sat.getActors():
			return False
		for effect in self.ms.getEffects():
			if not self.motivation.isConsistent(effect)
		if not self.motivation in self.ms.getEffects()
			return False
		
		return True
		
		
def DomainOperator(Graph):
	def __init__(self,id,type,name=None, Elements, Operator_Element, Edges,Constraints):
		super(DomainOperator,self).__init__(id,type,name,Elements,Edges,Constraints)
		self.Operator = Operator_Element
		Args = {i:arg for i in range(self.Operator.num_args) for arg in self.Elements if type(arg) is Argument and arg.arg_pos_dic[i]}
		
def Prerequisite(Graph):
	def __init__(self,id,type,name=None, Elements, Edges, Constraints):
		super(Prerequisite,self).__init__(id,type,name,Elements,Edges,Constraints)
		Causal_Links = {edge for edge in Edges if type(edge) is CausalLink}
		Orderings = {edge for edge in Edges if type(edge) is Ordering}
		Steps = {element for element in Elements if type(element) is Operator}
	
	def evaluateOperators(self,Operators):
		self.consistent_mappings = {step.id : {D.id for D in Operators if D.isConsistent(step)} for step in Steps}
		#TODO: check if two steps with nonempty intersection can be merged
		
		#{self.consistent_mappings[step.id].add(D.id) for step in Steps for D in Operators if D.isConsistent(step)}	
		#for D in Operators:
		#	{self.consistent_mappings[step.id].add(D.id) for step in Steps if D.isConsistent(step)}
			
	def evaluateCausalLinks(self)
		""" For every pair of steps, determine if consistent for causal link. 
			Create a "condition" by finding an source.effect that is consistent with a sink.precondition"""
		"""For every causal link Qi --Condition()--> Qj, find steps di = c-map[Qi.id] and dj = c-map[Qj.id] s.t. 
			Condition().Args[di.id] == Condition().Args[dj.id]
			For e"""
		{cl.id: {}}