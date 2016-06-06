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
	def __init__(self,id,type_graph,name=None,Elements = set(), root_element = None, Edges = set(),Constraints = set()):

		if root_element is None:
			root_element = Operator(id + 201,type='Action')
			
		super(Action,self).__init__(id,type_graph,name,Elements,root_element,Edges,Constraints)

		""" Get Action arguments by position"""											
		self.Args = {}
		self.updateArgs()
				
		""" Get consenting actors"""
		self.consenting_actors = set()			
		self.updateConsentingActors()
											
		#print('num_CONSENTING actors = {} in action {}'.format(len(self.consenting_actors),self.id))
		
		""" Determine if Action is an orphan"""
		self.isOrphan()
				

	def updateActionParams(self):
		self.updateConsentingActors()
		self.updateArgs()
		self.isOrphan()
				
	def updateArgs(self):

		for arg in self.elements:
			if type(arg) == Argument or type(arg) == Actor:
				for op_id, pos in arg.arg_pos_dict.items():
					if op_id == self.root.id:
						self.Args[pos] = arg
						
	def updateConsentingActors(self,scratch = False):
		if scratch:
			self.consenting_actors = set()
		self.consenting_actors.update({edge.sink \
										for edge in self.edges \
											if edge.source is self.root \
											and edge.label == 'actor-of'})
											
	def isOrphan(self):
		for actor in self.consenting_actors:
			if self.root.id not in actor.orphan_dict:
				actor.orphan_dict[self.root.id] = True
				self.is_orphan = True
			elif actor.orphan_dict[self.root.id] == True:
				self.is_orphan = True
				
	# @classmethod
	# def makeElementGraph(cls, elementGraph, element):
		# return cls(				element.id, \
								# element.type, \
								# name=None,\
								# Elements = elementGraph.rGetDescendants(element),\
								# root_element = element,\
								# Edges = elementGraph.rGetDescendantEdges(element),\
								# Constraints = elementGraph.rGetDescendantConstraints(element))
	
	def makeCopyFromID(self, start_from, increment = 1):
		new_self = self.copyGen()
		old_id = start_from
		start_from += increment
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
		#op_clone= operator.makeCopyFromID(self.id + 777,1)
		instances = operator.getInstantiations(self)
		
		plans = set()
		id = PLAN.id + 1
		for instance in instances:
			print('merge : {}'.format(instance.id))
			#instance.print_graph()
			Plan = PLAN.copyGen()
			Plan.swap(self.root, instance)
			print(type(Plan))
			if Plan.isInternallyConsistent():
				Plan.id = id 
				id += 1
				Plan.updateIntentionFrameAttributes()
				plans.add(Plan)
			print('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
		return plans
		
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type_graph,name=None,\
		Elements=set(), root_element = None, Edges = set(), Constraints = set()):
		
		super(Condition,self).__init__(id,type_graph,name,Elements,root_element,Edges,Constraints)
		self.labels = ['first-arg','sec-arg','third-arg','fourth-arg']
		
	def getArgList(self):

		
		return [self.getNeighborsByLabel(self.root, self.labels[i]) for i in range(self.root.num_args)]
		
	def print_graph(self, motive = False, actor_id = -1):
		args = self.getArgList()
		if motive:
			print('intends {}'.format(actor_id), end=" ")
		print('{truth}({name}'.format(truth='not' if not self.root.truth else '',name=self.root.name), end=" ")
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
	def __init__(self, id, type_graph, name=None, action1 = None, action2 = None, condition = None):
		super(CausalLink,self).__init__(source=action1,sink=action2,label=condition.id)
		self.id = id
		self.type = type_graph
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
	def __init__(self,id,type_graph='IntentionFrame',name=None, \
				Elements=set(),\
				root_element = None,\
				actor=None,\
				ms=None,\
				sat=None,\
				goal=None,\
				Edges=set(),\
				Constraints=set()):
		if actor is None:
			#print('need to select consistent_actor before instantiation')
			actor=Actor(id+1,type='actor')

		if ms is None:
			ms = Operator(id+2,type='Action', roles={id:'motivating-step'}, executed = False)
			
		if sat is None:
			sat = Operator(id+3, type='Action', roles={id:'satisfying-step'}, executed = False)
			
		if goal is None:
			goal = Literal(id+ 4, type='Condition', roles={id: 'goal'}, truth = None)
			
			
		Elements.add(actor)
		Elements.add(ms)
		Elements.add(sat)	
		Elements.add(goal)
		
		self.root = root_element
		self.ms = ms
		self.intender = actor
		self.goal = goal
		self.sat = sat
		self.motivation = Motivation(id + 5, intender=self.intender, goal = self.goal)	
		
		if root_element is None:
			root_element = IntentionFrameElement(	id,type_graph, \
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
		super(IntentionFrame,self).__init__(id,type_graph,name,Elements,root_element,Edges,Constraints)
		#########################################################################################
		
		self.Steps = {step for step in self.elements if type(step) is Operator}
		
		#self.constraints.add(Ordering(ms,sat))
		#self.constraints.update({Ordering(step, sat) for step in self.Steps if not step.id == sat.id})
		#self.constraints.update({Ordering(ms, step) for step in self.Steps})
		
	
		

	def addStep(self, Action, Plan, action_already_in_plan = True):
		""" Adding a step to an intention frame
				Return False if not added:
					Does the Action have a consenting actor, that is inconsistent with intender?
					Is there an ordering s.t. Operator is necessarily ordered before source?
																			  or after sat?
				Change status of operator
					Operator may no longer be an orphan
					
			RETURN new plan with step in intention frame
		"""
		if not action_already_in_plan:
			print('action_already_in_plan = false for plan {}; functionality not finished'.format(Plan.id))
		
		""" Pick Which Consenting Actor"""
		if len(Action.consenting_actors) == 0:
			print('Action', Action.id, 'has no consenting actors, but needs one to add to intention frame', self.id)
			return False
		
		consistent_actors = Plan.getConsistentActors(self.Steps)
		if len(consistent_actors) == 0:
			print('Cannot add step {} to plan {} because there are no consistent actors in {}'.format(Action.id, Plan.id, Plan.id))
			return False
			
		"""Check ordering constraints"""
		if Plan.necessarilyOrdered(Action.root, self.source):
			print('Cannot add action {} to plan {} because of ordering constraint {} < {}'.format(Action.id,Plan.id,Action.root.id,self.source.id))
			return False
		if Plan.necessarilyOrdered(self.sat, Action.root):
			print('Cannot add action {} to plan {} because of ordering constraint {} < {}'.format(Action.id,Plan.id,self.sat.id,Action.root.id))
			return False
			
		new_plan = plan.copyGen()
		new_plan.Steps.add(Action.root)
		new_plan.elements.update(Action.elements)
		new_plan.edges.update(Action.edges)
		new_plan.constraints.update(Action.constraints)
		this_frame_element.getElementById(self.root.id)
		consistent_actors = new_plan.getConsistentActors(self.Steps)
		if len(consistent_actors) == 0:
			print('After simulation, cannot add step {} to plan {} because there are no consistent actors which unify'.format(Action.id, new_plan.id))
			return False

			
		""" Make it so"""
		#Add ordering
		new_plan.addOrdering(Action.root, this_frame_element.sat)
		new_plan.addOrdering(this_frame_element.ms, Action.root)
			
		#Orphan status
		if len(consistent_actors) == 1:
			this_frame_element.intender = consistent_actors.pop()
			for op_id, status in this_frame_element.intender.orphan_dict.items():
				if op_id == Action.root.id:
					this_frame_element.intender.orphan_dict[op_id] = False
					break
		#Update if action is an orphan
		Action.isOrphan()
			
		return new_plan
	
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
		

		#Edges.update( {Edge(planElement,IF, 'frame-of') for IF in self.IntentionFrames})
		#Edges.update( {Edge(planElement,step, 'step-of') for step in self.Steps})
									
		super(PlanElementGraph,self).__init__(\
												id,\
												type_graph,\
												name,\
												Elements,planElement,\
												Edges,\
												Constraints\
											)
		
		
		self.updateIntentionFrameAttributes()
	
	def updateIntentionFrameAttributes(self):
		{element.external_update(self) for element in self.elements if type(element) is IntentionFrameElement}
			#Keeps intention frame element attributes up to date
			#Must be done after super instantation because needs edges
	
	def updatePlan(self, Elements = None,Edges = None,Constraints = None):
		""" Updating plans to have accurate top-level Sets"""
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
		""" Given subseteq of step elements in plan, return set of consistent actors (i.e. an actor that could be a consenting actor in each)
		"""
		step = next(iter(subseteq))
		print('step {} used for starting actors'.format(step.id))
		Step = self.getElementGraphFromElement(step,Action)
		#print('NUMBER OF CONSENTING ACTORS TO START WITH IN GET CNSISTENT ACTORS {}'.format(len(Step.consenting_actors)))
		S = copy.deepcopy(subseteq)
		S = S - {action for action in S if action.id != step.id}
		return self.rPickActorFromSteps(remaining_steps = S,potential_actors = Step.consenting_actors)
			
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
		step = self.getElementGraphFromElement(step,Action)
		
		to_remove = set()
		to_add = set()
		for actor in potential_actors:
			prospects = {prospect for prospect in step.consenting_actors if actor.isConsistent(prospect)}
			if len(prospects) == 0:
				to_remove.add(actor)
				#potential_actors.remove(actor)
			else:
				to_add.update(prospects)
		potential_actors = potential_actors - to_remove
		potential_actors.update(to_add)
		return self.rPickActorFromSteps(remaining_steps, potential_actors)
	
	
	def isInternallyConsistent(self):
		return True
		
	# def instantiate(self, step_element_, operator):
		# """	Instantiates a step_element type = operator with operator Action (elementgraph) 
			# Returns the set of plans in which the step_element is instantiated. 
			# Could be more than one way to instantiate given partial element
			
			# P1.instantiate(s, operator)
		# """
		# #self.updatePlan()
		# step = self.getElementGraphFromElementId(step_element_id, Action)
		# #print('in-plan step: {}'.format(step.id))
		# return step.instantiate(operator, self)

	def rInstantiate(self, remaining = set(), operators = set(), complete_plans = set()):
		"""	Recursively instantiate a step in self with some operator
			Return set of plans with all steps instantiated
			
			plan.rInstantiate(steps_Ids, {operator_1, operator_2})
		"""
		self.updatePlan()
		#remaining = {step for step in self.Steps if not step.instantiated}
		print('rInstantiate: {},\t remaining: {}'.format(self.id, len(remaining)))
		
		#BASE CASE
		if len(remaining) == 0:
			complete_plans.add(self)
			print('\nsuccess!, adding new plan {}\n'.format(self.id))
			return complete_plans
		else:
			print('rInstantiate remainings List:')
			for r in remaining:
				print('\t\t\t {}'.format(r))
			print('\n')
			
		#INDUCTION
		step_id = remaining.pop()
		new_plans = set()
		new_ids = {step_id + n for n in range(10,len(operators)+1)}
		new_self = self.copyGen()
		step = new_self.getElementGraphFromElementId(step_id, Action)
		print('\n___instantiating___\n')
		
		""" instantiate with every operator"""
		for op in operators:
			new_self = self.copyGen()
			step = new_self.getElementGraphFromElementId(step_id, Action)
			new_id = new_ids.pop()
			op_clone = op.makeCopyFromID(new_id,1)
			print('\n Attempting instantiation with step {} and op clone {} formally {}\n'.format(step.id,op_clone.id,op.id))
			new_ps = step.instantiate(op_clone, new_self) 
			new_plans.update(new_ps)
			#print('{} new plans from instantiating {} from operator {}-{} in plan {}'.format(len(new_ps),step.id, op.id, op.root.name, self.id))
			
		""" If completely empty, then this branch terminates"""
		if len(new_plans) == 0:
			return set()
		
		completed_plans_before= len(complete_plans)
		
		""" For each version, continue with remaining steps, choosing any operator"""
		for plan in new_plans:
			print('\ncalling rInstantiate with new_plans, now with remaining:',end = " ")
			for r in remaining:
				print('\t {}'.format(r), end= " ")
			print('\n')
			complete_plans = plan.rInstantiate(remaining, operators, complete_plans)
		
		""" if no path returns a plan, then this branch terminates"""
		if completed_plans_before >= len(complete_plans):
			return set()
			
		#Each return from rInstantiate is a set of unique plans with all steps instantiated
		#for plan in new_plans:
			#complete_plans = plan.rInstantiate(operators,complete_plans)
		
		return complete_plans

	
	def print_plan(self):
		self.updatePlan()
		print('\n----------------')
		print('PLAN', self.id)
		print('________________')

		print('steps:')
		for step in self.Steps:
			step.print_element()
		for edge in self.edges:
			edge.print_edge()
		print('frames:')
		for frame in self.IntentionFrames:
			print('frame id {}:'.format(frame.id), end=" ")
			Goal = self.getElementGraphFromElement(frame.goal, Condition)
			Goal.print_graph(motive=True,actor_id = frame.intender.id)
		print('----------------\n')

		