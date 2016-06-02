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

		""" Get Action arguments by position"""							
		self.Args = {i:arg \
						for i in range(self.root.num_args) \
							for arg in self.elements \
								if (type(arg) == Argument) \
								and i in arg.arg_pos_dict}
				
		""" Get consenting actors"""
		self.consenting_actors = set()			
		self.consenting_actors.update({edge.sink \
										for edge in self.edges \
											if edge.source is self.root \
											and edge.label == 'actor-of'})
		
		""" Determine if Action is an orphan"""
		for actor in self.consenting_actors:
			if self.root.id not in actor.orphan_dict:
				actor.orphan_dict[self.root.id] = True
			elif actor.orphan_dict[self.root.id] == True:
				self.is_orphan = True
				break
	
	def makeCopyFromID(self, start_from, increment = 1):
		new_self = self.copyGen()
		old_id = self.root.id
		for element in new_self.elements:
			element.id = start_from
			start_from = start_from + increment
		new_id = new_self.root.id
		for i, arg in new_self.Args.items():
			for id,pos in arg.arg_pos_dict.items():
				if id == old_id:
					arg.arg_pos_dict[new_id] = arg.arg_pos_dict.pop(old_id)
		return new_self
	
											

	def isConsistentAntecedentFor(self, action):
		"""Returns set of (self.effect, action.precondition) that are coConsistent"""
		effects = 	{egde.sink \
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
		Elements=set(), root_element = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		#self.labels = labels = ['first-arg','second-arg','third-arg','fourth-arg']
		
	# def makeElementGraph(self,element):
		# return Condition(		id=element.id, \
								# type= element.type, \
								# name=None,\
								# Elements = self.rGetDescendants(element),\
								# root_element = element,\
								# Edges = self.rGetDescendantEdges(element),\
								# Constraints = self.rGetDescendantConstraints(element)\
								# )
		
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
		if not action1.type == 'Action' or not action2.type == 'Action':
			print('cannot order non-actions')
			return None
		super(Ordering, self).__init__(action1,action2,'<')
		
	
class IntentionFrame(ElementGraph):
	""" 
		Intention Frame is an element graph plus a set of special elements
		Initially, 
	"""
	def __init__(self,id,type='IntentionFrame',name=None, \
				Elements=set(),\
				root_element = None,\
				actor=Actor(id= id+1,type='actor'),\
				ms=Operator(id = id+2,type='Action', roles={id:'motivating-step'}, executed = False),\
				sat=Operator(id = id+3, type='Action', roles={id:'satisfying-step'}, executed = False),\
				goal=Literal(id =id + 4, type='Condition', roles={id: 'goal'}, truth = True),\
				Edges=set(),\
				Constraints=set()):
				
		self.ms = ms
		self.intender = actor
		self.goal = goal
		self.sat = sat
		self.motivation = Motivation(id= id + 5, intender=self.intender, goal = self.goal)	
		if root_element is None:
			root_element = IntentionFrameElement(  id,type, \
												ms =self.ms, \
												motivation = self.motivation,\
												intender = self.intender,\
												goal = self.goal,\
												sat = self.sat
												)
												
		Edges.update({	Edge(root_element, actor, 'actor-of'), \
						Edge(root_element, ms, 'motivating-step-of'), \
						Edge(root_element, sat, 'sat-step-of'),\
						Edge(root_element, goal, 'goal-of'),\
						Edge(sat, goal, 'effect-of'), \
						Edge(ms, self.motivation, 'effect-of')\
						Edge(sat, actor, 'actor-of'),
						})

						
		
		self.Steps = \
			{step for step in \
				{self.getElementGraphFromElement(element, Action) \
					for element in self.elements \
						if element.type=='Action' \
						and element.id != self.ms.id\
				}\
			}
		
		Constraints.update({ Ordering(ms,sat)})
		Constraints.update( {Ordering(step, sat) for step in self.Steps if not step.isIdentical(sat)})
		Constraints.update( {Ordering(ms, step) for step in self.Steps})
		""" recursively decide on an actor and update orphan status for each actor, then for each step"""
		# If there were any steps with just one consenting actor, then that would be a good place to start
		if len(self.intender.arg_pos_dict) == 0:
			s = next(iter(self.Steps))
			consistent_actors = self.rPickActorFromSteps(remaining_steps = copy.deepcopy(self.Steps - {s}),s.consenting_actors)
			
		super(IntentionFrame,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
	

	def rPickActorFromSteps(self, remaining_steps = set(), potential_actors = set()):
		""" Pick a step and for each actor in consenting_actors, 
			if consistent with potential_actors, 
			invoke rPickActorFromSteps(remaining_steps-{step},potential_actors+{actor})
			
			Purpose:
						In CPOCL, intention frames are initialized with an actor. In BiPOCL,
							we may say that two steps are in the same plan.
						Are there any other situations when we have to do the following:
						
			Problem:	Given a set of steps with consenting actors, find the subset of actors
							that are consistent with one actor in every step.
			
			Strategy:	for each actor in potential_actors, remove if not consistent with any step actors
		"""
		
		
		if len(remaining_steps) == 0:
			return potential_actors
		if len(potential_actors) == 0:
			return
		
		step = remaining_steps.pop()
		
		for actor in potential_actors
			prospects = {prospect for prospect in step.consenting_actors if actor.isConsistent(prospect)}
			if len(prospects) == 0:
				potential_actors.remove(actor)
			else:
				potential_actors.update(prospects)
		potential_actors = self.rPickActorFromSteps(remaining_steps, potential_actors)
		
					
		return potential_actors
		

	def addStep(self, Action, Plan):
		""" Adding a step to an intention frame
				Return False if not added:
					Does the Action have a consenting actor, that is inconsistent with intender?
					Is there an ordering s.t. Operator is necessarily ordered before source?
																			  or after sat?
						
				Change status of operator
					Operator is no longer an orphan
					If intender is None but operator has an actor, or vice versa, then fill in
					
					
		"""
		
		""" Pick Which Consenting Actor"""
		if self.intender is None:
			print('intention frame', self.id, 'has no intender, but needss one to add step')
			return False
			
		if len(Action.consenting_actors) == 0:
			print('Action', Action.id, 'has no consenting actors, but needs one to add to intention frame', self.id)
			return False
		
		this_actor = None
		if not self.intender in Action.consenting_actors:
			found = False
			for actor in Action.consenting_actors:
				if self.intender.isConsistent(actor):
					this_actor = actor
					found = True
					break
			if not found:
				print('Action', Action.id, 'has no consenting actors consistent with intender of intention frame', self.id)
				return False

		"""Check ordering constraints"""
		if not self.source is None:
			if Plan.necessarilyOrdered(Action.root, self.source):
				return False
		if not self.sat is None:
			if Plan.necessarilyOrdered(self.sat, Action.root):
				return False
		else:
			print('ought to be satisfying step in intention frame', self.id, 'if we are adding a step...', Action.id)
			
		""" Make it so"""
		
		self.Steps.add(Action)
		
		if not self.sat is None:
			Plan.addOrdering(Action.root, self.sat)
		if not self.source is None:
			Plan.addOrdering(self.source, Action.root)
			
		false_detected = False
		for actor in Action.consenting_actors:
			for op_id, status in actor.orphan_dict.items():
				if op_id == Action.root.id and actor is this_actor:
					this_actor.orphan_dict[op_id] = False
					break
			if False in actor.orphan_dict.values():
				false_detected = True
				
		self.intender.combine(this_actor)
		
		if not false_detected:
			Action.is_orphan = False
			
		return self
		
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
		