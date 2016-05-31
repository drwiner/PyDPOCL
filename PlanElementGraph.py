from ElementGraph import *

class Belief(ElementGraph):
	def __init__(self, id, type, name=None, \
				Elements = set(), \
				root_element=None, \
				Edges = set(), \
				Constraints = set()\
				):
		
		super(Belief, self).__init__(id,type,name,Elements, root_element, Edges, Constraints)

class Action(ElementGraph):
	def __init__(self,id,graph_type,name=None, \
				Elements = set(), \
				root_element = None, \
				Edges = set(), \
				Constraints = set()\
				):
		
		super(Action,self).__init__(	id,graph_type,name,\
										Elements,\
										root_element,\
										Edges,\
										Constraints\
									)

									
		Args = 		{i:arg \
							for i in range(self.root.num_args) \
							for arg in self.elements \
										if (type(arg) == Argument) \
										and i in arg.arg_pos_dict\
					}
				
	def mergeArgs(self, other, remove = False):
		"""For every other.arg dicionary value of the form ID: value, create self.root_element.id: value"""
		#Remove = True: completely replace arg dictionary after finding positions. 
			#Only makes sense for arguments in domain operators
		#For all arguments in other.args i:arg
			#if i already in self.Args, do not add
			#Else, if 'i' not in self.Args, add self.Args.update({i:arg})
			#Add self.id:value to the arg.arg_pos_dict each key,value where key is other.id
	
		for pos,arg in other.Args.items():
			if not pos in self.Args:
				self.Args.update({pos:arg})
			#Remove id from other
			if remove:
				arg.arg_pos_dict = {self.root.id : pos}
			arg.arg_pos_dict.update({self.root.id : pos })
		return self
									
				
	def mergeEdgesFromSource(self, other, edge_source, mergeable_edges = set()):
		"""Override ElementGraph, need to make sure we merge args for a Domain Operator"""
		if edge_source.merge(other.root) is None:
			return None
		
		self.mergeArgs(self,other)
							
		return super(Action,self).mergeEdgesFromSource( self,\
																other,\
																edge_source,\
																mergeable_edges\
																)
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
										if eff.isConsistent(pre)\
					}
					
		if len(prospects)  == 0:
			return False
			
		return prospects
		
	# @staticmethod
	# def operatorToAction(Operator, action_id):
		# """ given a domain operator, create an action which is a copy of the operator but with merged args"""
		# root_id = Operator.root_element.id
		# copy_operator = Operator.copyGen()
		# copy_operator.update({action_id:value}\
								# for key,value in copy_operator)	
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type,name=None,\
		Elements=set(), literal_root = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type,name,Elements,literal_root,Edges,Constraints)
		#self.labels = labels = ['first-arg','second-arg','third-arg','fourth-arg']

		
class CausalLink(Edge):
	""" A causal link is an edge, s.t. the source and sink are actions, and the condition is itself an edge between a dummy element
		and the dependency literal element, rather than just a label"""
	def __init__(self, id, type, name=None, action1 = None, action2 = None, condition = None):
		super(CausalLink,self).__init__(source=action1,sink=action2,label=condition.id)
		self.id = id
		self.type = type
		self.name = name
		self.dependency = condition #A literal element#
		
	def isInternallyConsistent(self):
		effects = 	{egde.sink \
						for edge in self.edges \
							if edge.label == 'effect-of' \
							and edge.sink.id == self.condition.id\
					}
					
		if len(effects) == 0:
			return False
			
		preconditions = {edge.sink \
							for edge in self.edges \
								if edge.label == 'precond-of' \
								and edge.sink.id == self.condition.id\
						}
						
		if len(preconditions) == 0:
			return False
		return True
		
	
	#def possiblyThreatenedBy(self,action):
	
	def threatenedBy(self,action):
		action_orderings = getOrderingsWith(action)
		
#Do I need this?
class Binding(Edge):
	def __init__(self, id, type, name=None, element1 = None, element2 = None, binding_type = None):
	
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
				actor=None):

		super(IntentionFrame,self).__init__(id,type,name, \
											Elements, \
											source=source, \
											initial=initial, \
											sink=sink, \
											goal = goal, \
											Edges = Edges, \
											Constraints = Constraints, \
											)
			
		self.ms = source #Will have no outgoing 
		self.intender = actor
		self.goal = goal
		self.sat = sink
		self.motivation = Motivation(id, \
									intender=self.intender, \
									goal = self.goal\
									)
		self.root = IntentionFrameElement(  id = self.id,type='intention_frame', \
											ms =self.ms, \
											motivation = self.motivation,\
											intender = self.intender,\
											goal = self.goal,\
											sat = self.sat,\
											steps = self.Steps\
										)
		
	def isInternallyConsistent(self):
		for effect in self.sat.getEffects():
			if not self.goal.isConsistent(effect):
				return False
		for step in self.subplan.elements:
			#All steps must be isTransitiveClosure_isAntecedent
			if not step.isTransitiveClosure_isAntecedent(self.sat):
				return False
			if not self.intender in step.getActors():
				return False
		if not self.intender in self.sat.getActors():
			return False
		for effect in self.ms.getEffects():
			if not self.motivation.isConsistent(effect):
				return False
		if not self.motivation in self.ms.getEffects():
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
										Steps = Steps, \
										Bindings = Bindings,\
										Orderings = Orderings,\
										CausalLinks = CausalLinks,\
										IntentionFrames = IntentionFrames\
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
		