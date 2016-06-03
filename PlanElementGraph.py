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
		
		
		if root_element is None:
			root_element = Operator(id + 201,type='Action')
			
		super(Action,self).__init__(	id,graph_type,name,\
										Elements,\
										root_element,\
										Edges,\
										Constraints\
									)

		""" Get Action arguments by position"""							
		# self.Args = {i:arg \
						# for i in range(self.root.num_args) \
							# for arg in self.elements \
								# if (type(arg) == Argument or type(arg) == Actor) \
								# and i in arg.arg_pos_dict}					
		self.Args = {}
		for arg in self.elements:
			if type(arg) == Argument or type(arg) == Actor:
				for op_id, pos in arg.arg_pos_dict.items():
					if op_id == self.root.id:
						self.Args[pos] = arg

				
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

	def print_graph(self):
		print('\n({}'.format(self.root.name),end = " ")

		for i in range(1,self.root.num_args+1):
			if i not in self.Args:
				print('__',end = " ")
			else:
				print('({}:{})'.format(self.Args[i].type,self.Args[i].id),end = " ")
		
		print(')')
		
	def instantiate(self, operator, PLAN):
		""" instantiates self as operator in PLAN
			RETURNS a set of plans, one for each instantiation which is internally consistent
			- To instantiate a step as an operator, 
							1) make a copy of operator with new IDs
							2) operator.absolve(step)
							3) swap operator for step in plan
		"""
		op_clone = operator.makeCopyFromID(self.id + 777,1)
		merges = op_clone.possible_mergers(self)
		# test = merges.pop()
		# test.root.print_element()
		# print('from op_clone.possible_mergers')
		# merges = {test}
		plans = set()
		id = PLAN.id + 1
		for merge in merges:
			Plan = PLAN.copyGen()
			Plan.swap(self.root, merge)
			if Plan.isInternallyConsistent():
				Plan.id = id 
				id = id + 1
				plans.add(Plan)
		return plans
		
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type,name=None,\
		Elements=set(), root_element = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		self.labels = ['first-arg','second-arg','third-arg','fourth-arg']
		
	def getArgList(self):

		
		return [self.getNeighborsByLabel(self.root, self.labels[i]) for i in range(self.root.num_args)]
		
	def print_graph(self, motive = False, actor_id = -1):
		args = self.getArgList()
		if motive:
			print('intends {}'.format(actor_id), end=" ")
		print('{}({}'.format(self.root.truth,self.root.name), end=" ")
		for i, arg in enumerate(args):
			if len(arg) == 0:
				str = '__'
			else:
				this_arg = arg.pop()
				str = this_arg.id
			print(str, end=" ") 
		print(')')	
		
		
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
				actor=None,\
				ms=None,\
				sat=None,\
				goal=None,\
				Edges=set(),\
				Constraints=set()):
		if actor is None:
			print('need to select consistent_actor before instantiation')
			
			actor=Actor(id+1,type='actor')
		if ms is None:
			ms = Operator(id+2,type='Action', roles={id:'motivating-step'}, executed = False)
		if sat is None:
			sat = Operator(id+3, type='Action', roles={id:'satisfying-step'}, executed = False)
		if goal is None:
			goal = Literal(id+ 4, type='Condition', roles={id: 'goal'}, truth = None)
		
		self.root = root_element
		self.ms = ms
		self.intender = actor
		self.goal = goal
		self.sat = sat
		self.motivation = Motivation(id + 5, intender=self.intender, goal = self.goal)	
		
		if root_element is None:
			root_element = IntentionFrameElement(	id,type, \
													ms =self.ms, \
													motivation = self.motivation,\
													intender = self.intender,\
													goal = self.goal,\
													sat = self.sat\
													)
												
		Edges.update({	Edge(root_element, actor, 'intender-of'), \
						Edge(root_element, ms, 'motivating-step-of'), \
						Edge(root_element, sat, 'sat-step-of'),\
						Edge(root_element, goal, 'goal-of'),\
						Edge(sat, goal, 'effect-of'), \
						Edge(ms, self.motivation, 'effect-of'),\
						Edge(sat, actor, 'actor-of')\
						})
		#########################################################################################
		super(IntentionFrame,self).__init__(id,type,name,Elements,root_element,Edges,Constraints)
		#########################################################################################
		
		self.updateSteps()
		
		self.constraints.add(Ordering(ms,sat))
		self.constraints.update({Ordering(step, sat) for step in self.Steps if not step.id == sat.id})
		self.constraints.update({Ordering(ms, step) for step in self.Steps})
		""" recursively decide on an actor and update orphan status for each actor, then for each step"""
		# If there were any steps with just one consenting actor, then that would be a good place to start
			
	def updateSteps(self):
		self.Steps = {self.getElementGraphFromElement(element,Action) \
						for element in self.elements \
							if element.type == 'Action' and element.id != self.ms.id}
		return self

	def addStep(self, Action, Plan):
		""" Adding a step to an intention frame
				Return False if not added:
					Does the Action have a consenting actor, that is inconsistent with intender?
					Is there an ordering s.t. Operator is necessarily ordered before source?
																			  or after sat?
				Change status of operator
					Operator may no longer be an orphan
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
		# for effect in self.sat.getEffects():
			# if not self.goal.isConsistent(effect):
				# return False
				
		# for step in self.subplan.elements:
			# #All steps must be isTransitiveClosure_isAntecedent
			# if not step.isTransitiveClosure_isAntecedent(self.sat):
				# return False
			# if not self.intender in step.getActors():
				# return False
		
		# if not self.intender in self.sat.getActors():
			# return False
		# for effect in self.ms.getEffects():
			# if not self.motivation.isConsistent(effect):
				# return False
		# if not self.motivation in self.ms.getEffects():
			# return False
		
		return True
	
	def print_frame(self):
		Goal = self.getElementGraphFromElement(self.goal, Condition)
		Goal.print_graph(motive=True,actor_id = self.intender.id)
		
class PlanElementGraph(ElementGraph):

	def __init__(self,id,type_graph ='PlanElementGraph',name=None, \
				Elements = set(), \
				planElement = None, \
				Edges = set(), \
				Constraints = set()):
		
		self.updatePlan(Elements,Edges,Constraints)
		
		if planElement is None:
			planElement = PlanElement(\
										id =id, \
										type=type_graph, \
										name=name,\
										Steps = self.Steps, \
										Orderings = self.Orderings,\
										CausalLinks = self.Causal_Links,\
										IntentionFrames = self.IntentionFrames\
									)
									
		super(PlanElementGraph,self).__init__(\
												id,\
												type_graph,\
												name,\
												Elements,planElement,\
												Edges,\
												Constraints\
											)
	
	def updatePlan(self, Elements = None,Edges = None,Constraints = None):
		if Elements is None:
			Elements = self.elements
		if Edges is None:
			Edges = self.edges
		if Constraints is None:
			Constraints = self.constraints
		self.Steps = {element for element in Elements if type(element) is Operator}
		self.Orderings = {edge for edge in Constraints if type(edge) is Ordering}
		self.Causal_Links = {edge for edge in Edges if type(edge) is CausalLink}
		self.IntentionFrames = {element for element in Elements if type(element) is IntentionFrameElement}
		return self
											
	def getConsistentActors(self, subseteq):
		""" Given subseteq of steps in self.Steps, return set of consistent actors
		"""
		step = next(iter(self.Steps))
		S = copy.deepcopy(self.Steps)
		S = S - {action for action in S if action.id != step.id}
		return self.rPickActorFromSteps(remaining_steps = S,potential_actors = step.consenting_actors)
			
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
			
			Strategy:	For each actor in potential_actors, remove if not consistent with any step actors
		"""
		
		if len(remaining_steps) == 0:
			return potential_actors
		if len(potential_actors) == 0:
			return set()
		
		step = remaining_steps.pop()
		
		for actor in potential_actors:
			prospects = {prospect for prospect in step.consenting_actors if actor.isConsistent(prospect)}
			if len(prospects) == 0:
				potential_actors.remove(actor)
			else:
				potential_actors.update(prospects)
		return self.rPickActorFromSteps(remaining_steps, potential_actors)
	
	
	def isInternallyConsistent(self):
		return True
	
	def print_plan(self):
		self.updatePlan()
		print('\nPLAN', self.id)
		print('steps:')
		for step in self.Steps:
			step.print_element()
		print('frames:')
		for frame in self.IntentionFrames:
			Goal = self.getElementGraphFromElement(frame.goal, Condition)
			#if self.intender
			Goal.print_graph(motive=True,actor_id = frame.intender.id)
			#frame.print_frame()
		