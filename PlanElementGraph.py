from ElementGraph import *

class Belief(ElementGraph):
	def __init__(self, id, type, name=None, \
				Elements = set(), \
				root_element=None, \
				Edges = set(), \
				Constraints = set()\
				):
		
		super(Belief, self).__init__(id,type,name,Elements, root_element, Edges, Constraints)

class DomainOperator(ElementGraph):
	def __init__(self,id,type,name=None, \
				Elements = set(), \
				root_element = None, \
				Edges = set(), \
				Constraints = set()\
				):
		
		super(DomainOperator,self).__init__(id,type,name,\
											Elements,\
											root_element,\
											Edges,\
											Constraints\
											)
		Args = {i:arg \
					for i in range(self.root.num_args) \
					for arg in self.elements \
						if type(arg) is Argument \
						and arg.arg_pos_dic[i]\
				}
				
	def mergeEdgesFromSource(self, other, edge_source = self.root, mergeable_edges):
		"""Override ElementGraph, need to make sure we merge args"""
		if edge_source.merge(other.root) is None:
			return None
			
		subgraph = other.getElementGraphFromElement(other.root,type(self))
		
		#Goal, access each arg via the element.Args dictionary
		#for each entry of the form old_id: pos, create entry new_id: pos
		other.getElementGraphFromElement(other.root,type(self))\
			.Args.union_update({edge_source.id: value} \
								for key,value in subgraph.Args \
									if key==other.root.id\
							)
							
		return super(DomainOperator,self).mergeEdgesFromSource( self,\
																other,\
																edge_source,\
																mergeable_edges\
																)
		
class Action(DomainOperator):
	""" Action Graph: for step graph"""
	def __init__(self, id, type, name=None, \
				Elements=set(), \
				root_element = None, \
				Edges=set(), \
				Constraints = set()\
				):
		
		super(Action,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		
	def isConsistentAntecedentFor(self, action):
		"""Returns set of (self.effect, action.precondition) that are coConsistent"""
		effects = {egde.sink \
						for edge in self.edges \
								if edge.label == 'effect-of'\
				}
				
		if len(effects) == 0:
			return False
			
		preconditions = {edge.sink \
								for edge in self.edges \
										if edge.label == 'precond-of'\
						}
		if len(preconditions) == 0:
			return False
			
		prospects = {(eff,pre) \
								for eff in effects \
								for pre in preconditions \
										if eff.isCoConsistent(pre)\
					}
					
		if len(prospects)  == 0:
			return False
			
		return prospects
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type,name=None,\
		Elements=set(), literal_root = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type,name,Elements,literal_root,Edges,Constraints)
		#self.labels = labels = ['first-arg','second-arg','third-arg','fourth-arg']
	
	def rMerge(self, other, self_element = self.root, other_element = other.root, consistent_merges = set()):
		""" Returns set of consistent merges, which are Edge Graphs of the form self.merge(other)""" 
		#self_element.merge(other_element)
		
		otherEdges = other.getIncidentEdges(other_element)
		
		#BASE CASE
		if len(otherEdges) == 0:
			return consistent_merges.add(self)
			
		
		consistent_edge_pairs = self.getConsistentEdgePairs(self.getIncidentEdges(self_element), \
															otherEdges\
															)

		#INDUCTION	
		
		#First, merge inconsistent other edges, do this on every path
		mergeEdgesFromSource(other, \
							self.element, \
							other_element, \
							getInconsistentEdges(\
												otherEdges,\
												consistent_edge_pairs\
												)\
							) 
		
		#Assimilation Merge: see if we can merge the sinks.
		num_copies = len(consistent_edge_pairs) #
		consistent_merges.union_update({\
										self.copyGen().rMerge(\
																other, \
																e.sink, \
																o.sink, \
																consistent_merges\
															) \
															for (e,o) in consistent_edge_pairs \
										})

		#Accomodation Merge: see if we can add the sink's element graph
		#Don't check if type is Condition/literal, because if edges are consistent, \
			#then they share label, and literals have unique labels
	
		return consistent_merges		
	
		
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
	def __init__(self,id,type,name=None, \
				Elements = set(),\
				source = None, \
				initial = None, \
				sink = None, \
				goal=None, \
				Edges = set(), \
				Constraints = set(),  \
				):
		
		super(Subplan,self).__init__(id,type,name, Elements, sink, Edges, Constraints)
		
		self.goal = goal
		self.source =  source
		self.initial = initial
		self.rhetorical_charge = Rhetorical_charge
		self.Steps = \
			{step for step in \
				{self.getElementGraphFromElement(element, Action) \
					for element in self.elements \
						if type(element)==Operator \
						and element.id != source.id\
				}\
			}
		#self.causal_links
		#self.steps = {step.source for step in self.causal_links}.union({self.sink for step in self.causal_links})
	
class IntentionFrame(Subplan):
	def __init__(self,id,type,name=None, \
				Elements=set(),\
				source=None,\
				initial=None,\
				sink=None,\
				goal=None,\
				Edges=set(),\
				Constraints=set(),\
				intender=None):

		super(IntentionFrame,self).__init__(id,type,name, \
											Elements, \
											source=source, \
											initial=initial, \
											sink=sink, \
											goal, \
											Edges, \
											Constraints, \
											)
			
		self.ms = source #Will have no outgoing 
		self.intender = actor
		self.goal = goal
		self.sat = sink
		self.motivation = Motivation(id, \
									intender=self.actor, \
									goal = self.goal\
									)
		self.root = IntentionFrameElement(  self.id,type='intention_frame', \
											ms=self.ms, \
											motivation=self.motivation\
											intender=self.intender\
											goal=self.goal\
											sat=self.sat\
											subplan=self.Steps\
										)
		
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
		
class PlanElementGraph(ElementGraph):

	def __init__(self,id,type,name=None, \
				Elements = set(), \
				planElement = None, \
				Edges = set(), \
				Constraints = set()):
		
		self.Steps = {element for element in Elements if type(element) is Operator}
		self.Bindings = {edge for edge in Edges if type(edge) is Binding}
		self.Orderings = {edge for edge in Edges if type(edge) is Ordering}
		self.Causal_Links = {edge for edge in Edges if type(edge) is CausalLink}
		self.IntentionFrames = {element for element in Elements if type(element) is IntentionFrameElement}
		
		if planElement is None:
			planElement = PlanElement(\
										id =self.id, \
										type='plan element', \
										name=self.name,\
										Steps, \
										Bindings,\
										Orderings,\
										CausalLinks,\
										IntentionFrames\
									)
									
		super(PlanElementGraph,self).__init__(\
												id,\
												type,\
												name,\
												Elements,planElement,\
												Edges,\
												Constraints\
											)
	
	def evaluateOperators(self,Operators):
		"""
			1) Go through steps and determine consistent operators
				- To instantiate a step as an operator, copy operator and operator.rMerge(step)
				- In plan, step.mergeAt(copyoperator) ('take its family')
				- Successfully instantiated argument adopter

			2) For each causal link (source,sink,condition), 
				narrow down consistent mappings to just those which are consistent 
				given assignment of positions to arguments

			3) rMerge(self, other, self_element = self.root, other_element = other.root, consistent_merges = set())
		"""
		self.consistent_mappings = {step.id :  {\
												D.id for D in Operators \
													if D.isConsistent(step)\
												} for step in Steps \
									}
		