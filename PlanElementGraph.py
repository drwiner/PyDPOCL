from ElementGraph import *
import uuid

class Belief(ElementGraph):
	def __init__(self, id, type, name=None, \
				Elements = None, \
				root_element=None, \
				Edges = None, \
				Constraints = None\
				):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()
		
		super(Belief, self).__init__(id,type,name,Elements, root_element, Edges, Constraints)

class Action(ElementGraph):
	def __init__(self,id,type_graph,name=None,Elements = None, root_element = None, Edges = None,Constraints = None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()

		if root_element is None:
			root_element = Operator(uuid.uuid1(200),type='Action')
			
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
						
	def updateConsentingActors(self,scratch = None):
		if scratch == None:
			scratch = False
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
	
	def makeCopyFromID(self, start_from, increment = None, old_element_id = None):
		"""
			Makes copy of step-induced subgraph and changes ids
				Includes, updating the argument list
		"""
		if increment == None:
			increment = 1
		new_self = self.copyGen()
		old_id = self.id
		new_self.id = start_from
		
		for element in new_self.elements:
			if not old_element_id is None:
				if element.id == old_element_id:
					oei = old_element_id
			element.id = uuid.uuid1(start_from)
			
		new_id = new_self.root.id
		for i, arg in new_self.Args.items():
			for id,pos in arg.arg_pos_dict.items():
				if id == old_id:
					arg.arg_pos_dict[new_id] = arg.arg_pos_dict.pop(old_id)
					
		if old_element_id is None:
			return new_self
		else:
			return new_self, oei
	
											

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

	def print_action(self):
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
		
		instances = operator.getInstantiations(self)
		plans = set()
		id = PLAN.id + 1
		for instance in instances:
			Plan = PLAN.copyGen()
			Plan.id = id 
			id += 1
			Plan.mergeGraph(instance)
			action = Plan.getElementGraphFromElementId(self.id, Action)
			#if not operator.canAbsolve(action):
			#	print('Original Plan {}: constraints of partial step {} are detected in operator {}'.format(PLAN.id, self.id, operator.id))
			#	continue
			if Plan.isInternallyConsistent():
				Plan.updateIntentionFrameAttributes()
				print('adding plan {}'.format(Plan.id))
				plans.add(Plan)
			print('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
		return plans
		
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,id,type_graph,name=None,\
		Elements=None, root_element = None, Edges = None, Constraints = None):
		
		super(Condition,self).__init__(id,type_graph,name,Elements,root_element,Edges,Constraints)
		self.labels = ['first-arg','sec-arg','third-arg','fourth-arg']
		
	def getArgList(self):
		return [self.getNeighborsByLabel(self.root, self.labels[i]) for i in range(self.root.num_args)]
		
	def print_graph(self, motive = None, actor_id = None):
		if motive == None:
			motive = False
		if actor_id == None:
			actor_id = -1
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
		if len(effects) > 1:
			print('multiple effects with dependency id?')
			return False
			
		preconditions = {edge.sink \
							for edge in self.edges \
								if edge.label == 'precond-of' \
								and edge.sink.id == self.condition.id\
						}
						
		if len(preconditions) == 0:
			return False
		if len(preconditions) >1:
			print('multiple preconditions with dependecy id?')
			return False
			
		return True
		
	
	#def possiblyThreatenedBy(self,action):
	
	def threatenedBy(self,action):
		action_orderings = getOrderingsWith(action)	
		
class Ordering(Edge):
	def __init__(self,action1,action2):
		if not action1.type == 'Action' or not action2.type == 'Action':
			print('cannot order non-actions')
			return None
		super(Ordering, self).__init__(action1,action2,'<')
		
class PlanElementGraph(ElementGraph):

	def __init__(self,id,type_graph =None,name=None, \
				Elements = None, \
				planElement = None, \
				Edges = None, \
				Constraints = None):
				
		if type_graph == None:
			type_graph = 'PlanElementGraph'
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges=  set()
		if Constraints == None:
			Constraints = set()
		
		self.updatePlan(Elements,Edges,Constraints)
		self.flaws = [] #sort by heuristic via Planner.py
		
		if planElement is None:
			planElement = PlanElement(id =id, type=type_graph,name=name)
		

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
		S = copy.deepcopy(subseteq)
		S = S - {action for action in S if action.id == step.id}
		return self.rPickActorFromSteps(remaining_steps = S, potential_actors = Step.consenting_actors)
			
	def rPickActorFromSteps(self, remaining_steps = None, potential_actors = None):
		if remaining_steps == None:
			remaining_steps = set()
		if potential_actors == None:
			potential_actors = set()
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
		
		print('rpickActorFromSteps')
		step = remaining_steps.pop()
		step.print_element()
		print('above was chosen\n')
		step = self.getElementGraphFromElementId(step.id,Action)
		
		to_remove = set()
		to_add = set()
		for actor in potential_actors:
			print('potential actor: ')
			actor.print_element()
			print('prospects: ')
			for p in step.consenting_actors:
				p.print_element()
			prospects = {prospect for prospect in step.consenting_actors if actor.isConsistent(prospect)}
			print('consistent prospects: ')
			for p in prospects:
				p.print_element()
			if len(prospects) == 0:
				to_remove.add(actor)
				#potential_actors.remove(actor)
			else:
				to_add.update(prospects)
		
		potential_actors = potential_actors - to_remove
		potential_actors.update(to_add)
		return self.rPickActorFromSteps(remaining_steps, potential_actors)
	
	
	def isInternallyConsistent(self):
		""" 
			With respect to constraint sources
			With respect to orderings (no cycles)
			With respect to causal links (?)
			With respect to intention frame elements
				consenting actors
				causal antecedence of sat
			
		"""
		return super(PlanElementGraph,self).isInternallyConsistent()
		
	def detectFlaws(self):
		self.detectOpenPreconditionFlaws()
		self.detectThreatenedCausalLinkFlaws()
		self.detectUnsatisfiedIntentionFrameFlaws()
		self.detectIntentFlaws()
		self.detectOpenMotivationFlaws()
		return self
		
	def detectOpenPreconditionFlaws(self):
		pass
		
	def detectThreatenedCausalLinkFlaws(self):
		pass
	
	def detectUnsatisfiedIntentionFrameFlaws(self):
		pass
		
	def detectIntentFlaws(self):
		pass
		
	def detectOpenMotivationFlaws(self):
		pass

	def rInstantiate(self, remaining = None, operators = None, complete_plans = None):
		if remaining == None:
			remaining = set()
		if operators == None:
			operators = set()
		if complete_plans == None:
			complete_plans = set()
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
		new_ids = {step_id + n + 35 for n in range(1,len(operators)+10)}
		print('\nids:')
		for d in new_ids:
			print(d, end= " ")
		print('\n')
		
		""" instantiate with every operator"""
		for op in operators:
			new_id = new_ids.pop()
			new_self = self.copyGen()
			new_self.id = self.id + new_id
			step = new_self.getElementGraphFromElementId(step_id, Action)
			op_clone = op.makeCopyFromID(new_id,1)
			#print('\n Plan {} ___instantiating_{}__with operator clone {}\n'.format(new_self.id, step_id, op_clone.id))
			print('\n Plan {} Attempting instantiation with step {} and op clone {} formally {}\n'.format(new_self.id, step.id,op_clone.id,op.id))
			new_ps = step.instantiate(op_clone, new_self) 
			print('\n returned {} new plans originally from {}\n'.format(len(new_ps), self.id))
			for p in new_ps:
				p.print_plan()
				print('\n')
			print('end new plans')
			new_plans.update(new_ps)
			#print('{} new plans from instantiating {} from operator {}-{} in plan {}'.format(len(new_ps),step.id, op.id, op.root.name, self.id))
			
		""" If completely empty, then this branch terminates"""
		if len(new_plans) == 0:
			return set()
		
		completed_plans_before= len(complete_plans)
		
		""" For each version, continue with remaining steps, choosing any operator"""
		for plan in new_plans:
			print('\ncalling rInstantiate with new_plan {}, now with remaining:'.format(plan.id),end = " ")
			for r in remaining:
				print('\t {}'.format(r), end= ", ")
			print('\n')
			#rem = {rem_id for rem_id in remaining}
			complete_plans.update(plan.rInstantiate({rem_id for rem_id in remaining}, operators, complete_plans))
		
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
		print('Constraints:')
		for c in self.constraints:
			c.print_edge()
		print('----------------\n')

		