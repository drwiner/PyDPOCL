from PlanElementGraph import *

class IntentionFrame(ElementGraph):
	""" 
		Intention Frame is an element graph plus a set of special elements
		Initially, 
	"""
	def __init__(self,id,type_graph='IntentionFrame',name=None, \
				Elements=None,\
				root_element = None,\
				actor=None,\
				ms=None,\
				sat=None,\
				goal=None,\
				Edges=None,\
				Constraints=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()
			
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
		
	
		

	def addStep(self, Action, Plan, action_already_in_plan = None):
		if action_already_in_plan == None:
			action_already_in_plan = True
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