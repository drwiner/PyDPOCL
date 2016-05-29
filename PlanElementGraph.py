from Graph import *

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