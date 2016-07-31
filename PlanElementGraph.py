from OrderingGraph import *
from collections import deque
import uuid
import random

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
		
		if Edges == None:
			Edges = set()
		if Constraints == None:
			Constraints = set()

		if root_element is None:
			root_element = Operator(uuid.uuid1(200),type='Action')
			
		if Elements == None:
			Elements = {root_element}
			
		super(Action,self).__init__(id,type_graph,name,Elements,root_element,Edges,Constraints)

		""" Get Action arguments by position"""											
		#self.Args = {}
		#self.updateArgs()
				
		""" Get consenting actors"""		
		self.updateConsentingActors(scratch = True)
											
		#print('num_CONSENTING actors = {} in action {}'.format(len(self.consenting_actors),self.id))
		
		""" Determine if Action is an orphan"""
		#self.isOrphan()
				

	def updateActionParams(self):
		self.updateConsentingActors()
		#self.updateArgs()
		#self.isOrphan()
				
	# def updateArgs(self):

		# for arg in self.elements:
			# if type(arg) == Argument or type(arg) == Actor:
				# for op_id, pos in arg.arg_pos_dict.items():
					# if op_id == self.root.id:
						# self.Args[pos] = arg
						
	def updateConsentingActors(self,scratch = None):
		if scratch == None:
			scratch = False
		if scratch:
			self.consenting_actors = set()
		self.consenting_actors.update({edge.sink \
										for edge in self.edges \
											if edge.source is self.root \
											and edge.label == 'actor-of'})
											
	# def isOrphan(self):
		# for actor in self.consenting_actors:
			# if self.root.id not in actor.orphan_dict:
				# actor.orphan_dict[self.root.id] = True
				# self.is_orphan = True
			# elif actor.orphan_dict[self.root.id] == True:
				# self.is_orphan = True
				
	# @classmethod
	# def makeElementGraph(cls, elementGraph, element):
		# return cls(				element.id, \
								# element.type, \
								# name=None,\
								# Elements = elementGraph.rGetDescendants(element),\
								# root_element = element,\
								# Edges = elementGraph.rGetDescendantEdges(element),\
								# Constraints = elementGraph.rGetDescendantConstraints(element))
	
	def makeCopyFromID(self, start_from, old_element_id = None):
		"""
			Makes copy of step-induced subgraph and changes ids
			Non-equality constraints wiped
		"""
		new_self = self.copyGen()
		old_id = self.id
		new_self.id = start_from
		nei = -1
		
		#While changing IDs, look for the element which used to have old_element.id and let 'nei' = new element id
		if not old_element_id is None:
			ole = {element for element in new_self.elements if element.id == old_element_id}
			if not ole:
				print('could not find old element id {} in old Action {}'.format(old_element_id, self.id))
			else:
				old_element = ole.pop()
		
		for element in new_self.elements:
			element.id = uuid.uuid1(start_from)
		
		if not old_element_id is None:
			nei = old_element.id
			
		#Wipe non-equality constraints clean
		new_self.neqs = set()
		
		
		# for element in new_self.elements:
			# element.id = uuid.uuid1(start_from)
			# if not old_element_id is None and not found:
				# if element.id == old_element_id:
					# found = True
					# nei = element.id
			
		#new_id = new_self.root.id
		# for i, arg in new_self.Args.items():
			# for id,pos in arg.arg_pos_dict.items():
				# if id == old_id:
					# arg.arg_pos_dict[new_id] = arg.arg_pos_dict.pop(old_id)
					

		return new_self, nei

	
											

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
		self.Args = []''' temporary, no Args list'''
		for i in range(1,self.root.num_args+1):
			if i not in self.Args:
				print('__',end = " ")
			else:
				print('({}:{})'.format(self.Args[i].type,self.Args[i].id),end = " ")
		
		print(')')
		
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
		
	def __repr__(self):
		return self.root
		
		
		
class PlanElementGraph(ElementGraph):
	"""
		Plan element graph = Plan
		is-a element graph
		has-a set of flaws
		has-a set of action elements
		has-a ordering graph
		has-a causal graph
		has-a constraint graph which encodes inequality constraints
		has-a dummy init and dummy goal step
	"""
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
		self.flaws = deque() #sort by heuristic?
		self.initial_dummy_step = None
		self.final_dummy_step = None
		self.OrderingGraph = OrderingGraph(id = uuid.uuid1(5))
		self.CausalLinkGraph = CausalLinkGraph(id = uuid.uuid1(6))
		
		if planElement is None:
			planElement = PlanElement(id =id, type=type_graph,name=name)
		

		#Edges.update( {Edge(planElement,IF, 'frame-of') for IF in self.IntentionFrames})
		#Edges.update( {Edge(planElement,step, 'step-of') for step in self.Steps})
									
		super(PlanElementGraph,self).__init__(id,type_graph,name,Elements,planElement,Edges,Constraints)
		
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
		self.Orderings = self.OrderingGraph.edges
		self.Causal_Links = self.CausalLinkGraph.edges
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
	
	
	def instantiatePartialStep(self, partial, operator_choices, complete_steps = None):
		if operator_choices == None:
			return None
		if partial == None:
			return None
		if complete_steps == None:
			complete_steps = set()
			
		rnd =floor(random.random()*100)
		Step = new_self.getElementGraphFromElementId(partial.id, Action)
		operatorClones = {op.makeCopyFromID(rnd) for op in operator_choices}
		for op in operatorClones:
			#nStep = Step.copyGen()
			complete_steps.update(op.getInstantiations(Step))
		return complete_steps

	
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

		