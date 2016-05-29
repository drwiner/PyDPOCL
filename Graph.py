from Element import *

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
		
	def isCoConsistent(self,other):
		if self.isCoConsistent(other) and other.isCoConsistent(self):
			return True
			
		return False

	def isEquivalent(self, other):
		if self.source.isEquivalent(other.source) and self.sink.isEquivalent(other.sink) and self.label == other.label:
			return True
		return False
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		"""Returns merge other.sink into self.sink"""
		#Assume source is already equal and edge label is already equal
		if not self.source.isEqual(other.source):
			return False
		#Assume edges are co-consistent
		if not self.isCoConsistent(other):
			return False
		
		return self.sink.merge(other.sink)

class Graph(Element):
	"""A graph is an element with elements, edges, and constraints"""
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
			
	def getIncidentEdges(self, element):
		return {edge for edge in self.edges if edge.source is element}
	def getNeighbors(self, element):
		return set(edge.sink for edge in self.edges if edge.source is element)
	def getParents(self, element):
		return set(edge.source for edge in self.edges if edge.sink is element)
	def getNeighborsByLabel(self, element, label):
		return set(edge.sink for edge in self.edges if edge.source is element and edge.label is label)
	def getIncidentEdgesByLabel(self, element, label):
		return {edge for edge in self.edges if edge.source is element and edge.label is label}
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
		
	def isCoConsistent(self,other):
		if self.isConsistent(other) and other.isConsistent(self):
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
	""" Returns True if all remaining edges can be assigned a consistent non-used edge in self """
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
	
class ElementGraph(Graph):
	"""An element graph is a graph with a root"""
	
	def __init__(self,id,type,name=None, Elements = set(), root_element = None, Edges = set(), Constraints = set()):
		super(ElementGraph,self).__init__(id,type,name,Elements,Edges,Constraints)
		self.root = root
	
	def getElementGraphFromElement(self, element):
		if self.root is element:
			return self
		
		return ElementGraph(element.id, type='element %s' %subgraph, name=self.name\
			self.rGetDescendants(element)\
			root=element\
			self.rGetDescendantEdges(element)\
			self.rGetDescendantConstraints(element))
			
	def rMerge(self, other, self_element = self.root, other_element = other.root, consistent_merges = {self}):
		incidentEdges = self.getIncidentEdges(self_element)
		otherEdges = other.getIncidentEdges(other_element)
		
		#Base Case
		if len(incidentEdges) == 0 and len(otherEdges) == 0:
			return consistent_merges
			
		#Induction
		consistent_edges = \
				{(edge,other) for edge in incidentEdges for other in otherEdges \
					if edge.isCoConsistent(other)\
				}
		
		#For each pair of consistent edges which are not equivalent (if they are equivalent, then ignore), 
			#edit the 'n' merge-graphs where both are separated edges, where 'n' is the number of consistent_merges
			#another 'n' merge-graph where both are merged into the first-arg,
		#Then, rMerge, but from self_element.sink and other_element.sink
		
		#Get the eelementgraph from the sink1, and the 
		for edge,other in consistent_sinks:	
			if not edge.isEqual(other):
				for consistent_merge in consistent_merges:
					consistent_merges = consistent_merge.rMerge(other,edge.sink, other.sink, consistent_merges)
					new_merge = copy.deepcopy(consistent_merge)
					edge.Merge(other)
					consistent_merges = new_merge.rMerge(other,edge.sink, other.sink, consistent_merges)
				element_graph_merge.add()
				merge = copy.deepcopy(edge).Merge(other)
				
				
				merge_graph = self.getElementGraphFromElement(sink_merge)
				sink1_graph = self.getElementGraphFromElement(sink1)
				sink2_graph = other.getElementGraphFromElement(sink2)
				
				merge_graph.rMerge(sink2_graph, consistent_merges)
				sink1_graph.rMerge(sink2_graph, consistent_merges)
	

def getElementGraphMerge(one,other):
	
	if not one.isCoConsistent(other):
		return set()
		
	
	possible_worlds = {element_graph for element_graph in {}}
		
	if one.root.name is None:
		if other.root.name is None:
			print('if this were a literal, needs a name')
		else:
			one.root.name = other.root.name	

	if type(one.root) == 'Literal':
		if one.root.num_args is None:
			if other.root.num_args is None:
				print('need to put num_args in literals')
				return None
			else:
				self.root.num_args = other.root.num_args
				
	if type(one.root) == 'Operator':
		preconditions = {edge for edge in }
		#For each pair of co-consistent preconditions (one.precondition, other.precondition), 
			#If they both have the same name,
				#Create new ElementGraphs EG1,EG2, where EG1 makes them the same precondition, and EG2 keeps them separated
		#Do same for each pair of effects.
			#Don't need to do this for consenting actor
	#Action, Condition, 
		""" BUT, then there will be a combinatorial explosion of different ElementGraphs for each permuation,
			especially more complex ElementGraphs.
			What if, for each element in an ElementGraph, we store a set of possible mergers?"""
				
				
		"""TODO: with literals, there are no edges with same label. With steps, there are. 
			With steps, consider the unnamed step which contains two same-named literals. (e.g. to preconditions (at x loc) and (at y loc))
			Where self has (at arg1 loc) and other has (at None loc). 
			Two options, combine the literals or let there be two preconditions in merged Condition.
			Ought we store a list of alternatives? Ought this method not be a class method?"""

class Belief(ElementGraph):
	def __init__(self, id, type, name=None, Elements = set(), root_element=None, Edges = set(), Constraints = set()):
		super(Belief, self).__init__(id,type,name,Elements, root_element, Edges, Constraints)
	
	# def isEquivalent(other_belief):
		# if self.story_element.isEquivalent(other_belief.story_element) \
		# and other_belief.story_element.isEquivalent(self.story_element):
			# return True:
		# return False
		
class Action(ElementGraph):
	""" Action Graph: for step graph"""
	def __init__(self, id, type, name=None, Elements=set(), root_element = None, Edges=set(), Constraints = set()):
		super(Action,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		
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
	
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type,name=None,\
		Elements=set(), literal_root = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type,name,Elements,literal_root,Edges,Constraints)
		self.labels = labels = ['first-arg','second-arg','third-arg','fourth-arg']
		
	def mergeFrom(self, other):
		super(Condition,self).mergeFrom(other)
		
		for i in range(num_args):
			self_edge_to_args = self.getIncidentEdgesByLabel(self.root, self.labels[i]).pop()
				if len(self_edge_to_args) == 0:
					other_edge_to_args = other.getIncidentEdgesByLabel(other.root, self.labels[i]).pop()
					if len(other_edge_to_args) > 0:
						self.edges.add(Edge(self.root,other_edge_to_args.sink, other_edge_to_args.label))
		
	#def fromSubgraph(self,subplan):
	
def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element)
	Elements = G.rGetDescendants(element)
	Constraints = G.rGetDescendantConstraints(element)
	return Type(element.id,type = element.type, name=element.name, Elements, Edges, Constraints)			
	
		
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
		
		
class Subplan(ElementGraph):
	def __init__(self,id,type,name=None, Elements = set(),\
		source = None, initial = None, sink = None, goal=None, \
		Edges = set(), Constraints = set(),  Rhetorical_charge = None):
		
		super(Subplan,self).__init__(id,type,name, Elements, sink, Edges, Constraints)
		
		self.goal = goal
		self.source =  source
		self.initial = initial
		self.rhetorical_charge = Rhetorical_charge
		self.Steps = \
			{step for step in \
				{extractElementsubGraphFromElement(element) for element in self.elements \
					if type(element)==Operator and element.id != source.id\
				}\
			}
		#self.causal_links
		#self.steps = {step.source for step in self.causal_links}.union({self.sink for step in self.causal_links})


class Motivation(Literal):
	def __init__(self, id, type='motivation', name='intends', num_args = 1, truth = True, intender=None, goal=None):
		super(Motivation,self).__init__(id,type,name,num_args,truth)
		self.actor = intender
		self.goal = goal #Goal is a literal. THIS is a case where... a Literal has-a Literal
		
class IntentionFrameElement(Element):
	def __init__(self, id, type, name= None, ms, motivation, intender, goal, sat, steps):
		super(IntentionFrameElement,self).__init__(id,type,name)
		self.ms = ms
		self.motivation = motivation
		self.intender = intender
		self.goal = goal
		self.sat = sat
		self.subplan = subplan
		
class IntentionFrame(Subplan):
	def __init__(self,id,type,name=None, \
		Elements=set(),source=None,initial=None,sink=None,goal=None,\
		Edges=set(),Constraints=set(),Rhetorical_charge=None, intender=None):

		super(IntentionFrame,self).__init__(id,type,name, \
			Elements, source=source, initial=initial, sink=sink, goal, \
			Edges, Constraints, Rhetorical_charge)
			
		self.ms = source #Will have no outgoing 
		self.intender = actor
		self.goal = goal
		self.sat = sink
		self.motivation = Motivation(id, intender=self.actor, goal = self.goal)
		self.root = IntentionFrameElement(self.id,type='intention_frame', \
			ms=self.ms, \
			motivation=self.motivation\
			intender=self.intender\
			goal=self.goal\
			sat=self.sat\
			subplan=self.Steps)
		
		
	def isInternallyConsistent(self):
		for effect in self.sat.getEffects():
			if not self.goal.isConsistent(effect):
				return False
		for step in self.subplan.elements:
			#All steps must be isTransitiveClosure_isAntecedent
			if not step.isTransitiveClosure_isAntecedent(self.sat):
				return False
			if not self.actor in step.getActors():
				return False
		if not self.actor in self.sat.getActors():
			return False
		for effect in self.ms.getEffects():
			if not self.motivation.isConsistent(effect):
				return False
		if not self.motivation in self.ms.getEffects()
			return False
		
		return True
		
		
def DomainOperator(ElementGraph):
	def __init__(self,id,type,name=None, \
		Elements = set(), root_element = None, Edges = set(), Constraints = set()):
		
		super(DomainOperator,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		Args = {i:arg for i in range(self.root.num_args) for arg in self.elements if type(arg) is Argument and arg.arg_pos_dic[i]}
		
def PlanElement(Element):

	def __init__(self,id,type, name=None,\
		Steps=set(), Orderings=set(), Bindings = set(), CausalLinks=set(), IntentionFrames=set()):
		
		self.Steps = Steps
		self.Bindings = Bindings
		self.Orderings = Orderings
		self.CausalLinks = CausalLinks
		self.IntentionFrames = IntentionFrames
		
		
def PlanElementGraph(ElementGraph):

	def __init__(self,id,type,name=None, Elements, Edges, Constraints):
	
		Causal_Links = {edge for edge in Edges if type(edge) is CausalLink}
		Orderings = {edge for edge in Edges if type(edge) is Ordering}
		Steps = {element for element in Elements if type(element) is Operator}
		Bindings = {edge for edge in Edges if type(edge) is Binding}
		IntentionFrames = {}
		
		
		super(PlanElementGraph,self).__init__(id,type,name,Elements,Edges,Constraints)
		#Bindings = something to track possibly equivalent steps, or reverse
	
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