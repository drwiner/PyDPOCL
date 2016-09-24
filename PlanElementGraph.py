from OrderingGraph import *
from Flaws import *
from collections import deque
import uuid
import random
import itertools
from clockdeco import clock

class Action(ElementGraph):
	stepnumber = 2
	def __init__(self,ID,type_graph,name=None,Elements = None, root_element = None, Edges = None,Restrictions = None):
		
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()

		if root_element is None:
			root_element = Operator(uuid.uuid1(200),typ='Action')
			
		if Elements == None:
			Elements = {root_element}
			
		super(Action,self).__init__(ID,type_graph,name,Elements,root_element,Edges,Restrictions)
		
		""" Get consenting actors"""		
		self.updateConsentingActors(scratch = True)

		self.nonequals = set()
											
		#print('num_CONSENTING actors = {} in action {}'.format(len(self.consenting_actors),self.id))
		
		""" Determine if Action is an orphan"""
		#self.isOrphan()

	def RemoveSubgraph(self, elm):
		link = None
		to_remove = set()
		for edge in self.edges:
			if edge.source == elm:
				to_remove.add(edge)
			if link is None:
				if edge.sink == elm:
					edge.sink = Element(ID = -1)
					link = edge
		self.elements -= {elm}
		self.edges -= to_remove
		return link

	def getPreconditionsOrEffects(self, label):
		return {edge.sink for edge in self.edges if edge.label == label}

	def subgraph(self, element, Type = None):
		if Type == None:
			Type = eval(element.typ)
		new_self = self.getElementGraphFromElement(element, Type)
		new_self.updateArgs()
		return new_self

	def subgraphFromID(self, element_ID, Type = None):
		return self.subgraph(self.getElementById(element_ID), Type)
						
	def updateConsentingActors(self,scratch = None):
		pass
		if scratch == None:
			scratch = False
		if scratch:
			self.consenting_actors = set()
		self.consenting_actors.update({edge.sink for edge in self.edges if edge.source is self.root	and edge.label == 'actor-of'})
											
	# def isOrphan(self):
		# for actor in self.consenting_actors:
			# if self.root.id not in actor.orphan_dict:
				# actor.orphan_dict[self.root.id] = True
				# self.is_orphan = True
			# elif actor.orphan_dict[self.root.id] == True:
				# self.is_orphan = True

	def instantiateOperator(self, old_element_id=None):
		"""
			Makes copy of step-induced subgraph and changes ids
		"""
		new_self = self.copyGen()
		new_self.ID = Action.stepnumber

		#While changing IDs, look for the element which used to have old_element.id and let 'nei' = new element id
		if not old_element_id is None:
			old_element = new_self.getElementById(old_element_id)
			if not old_element:
				raise ValueError('could not find old element id {} in old Action {}'.format(old_element_id, self.ID))

		#Replace all element IDs
		for element in new_self.elements:
			element.ID = uuid.uuid1(new_self.ID)

		new_self.root.arg_name = Action.stepnumber
		Action.stepnumber+=1

		#But we save
		if not old_element_id is None:
			nei = old_element.ID
			return new_self, nei

		return new_self

	def replaceInternals(self):
		self.ID = Action.stepnumber
		self.root.arg_name = Action.stepnumber
		#Action.stepnumber += 1

		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.ID = uuid.uuid1(self.ID)

	def isConsistentAntecedentFor(self, consequent, effect = None):
		"""Returns set of (self.effect, action.precondition) that are coConsistent"""
		if effect == None:
			effects = {edge.sink for edge in self.edges if edge.label == 'effect-of'}
		else:
			effects = {effect}
				
		if len(effects) == 0:
			return False
			
		preconditions = {edge.sink for edge in consequent.edges if edge.label == 'precond-of'}
		if len(preconditions) == 0:
			return False

		prospects = {(eff,pre) for eff in effects for pre in preconditions if self.subgraph(eff).isConsistent(
			consequent.subgraph(pre))}
					
		if len(prospects)  == 0:
			return False
			
		return prospects
		
	# '''for debugging'''
	# def getConditions(self):
		# pres = {edge for edge in self.edges if edge.label == 'precond-of'}
		# effs = {edge for edge in self.edges if edge.label == 'effect-of'}
		# print('Preconditions:\n')
		# for pre in pres:
			# pre.sink
		# print('Effects:\n')
		# for eff in effs:
			# eff.sink

	def isConsistent(self, other):
		""" an action is consistent just when one can absolve the other"""
		return self.isConsistentSubgraph(other)

		
	def __repr__(self):
		self.updateArgs()
		args = str(self.Args)
		exe = self.root.executed
		if exe == None:
			exe = 'ex'
		return '{}-{}-{}'.format(exe, self.root.name, self.root.arg_name) + args
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,ID,type_graph,name=None,Elements=None, root_element = None, Edges = None, Restrictions = None):
		
		super(Condition,self).__init__(ID,type_graph,name,Elements,root_element,Edges,Restrictions)
		self.labels = ['first-arg','sec-arg','third-arg','fourth-arg']
		
	def getArgList(self):
		return [self.getNeighborsByLabel(self.root, self.labels[i]) for i in range(self.root.num_args)]

	def isConsistent(self, other):
		return self.isConsistentSubgraph(other)

	def numArgs(self):
		if not hasattr(self, 'Args'):
			self.updateArgs()
		return len({arg for arg in self.Args if not arg.name is None})

	def subgraph(self, element, Type = None):
		if Type == None:
			Type = eval(element.typ)
		new_self = self.getElementGraphFromElement(element, Type)
		new_self.updateArgs()
		return new_self
			
	def __repr__(self):
		self.updateArgs()
		args = str([' {}-{} '.format(arg.name, arg.typ) for arg in self.Args])
		return '{}-{}{}'.format(self.root.truth, self.root.name, self.typ) + args
		
		
		
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
	def __init__(self,ID,type_graph =None,name=None,
				Elements = None,
				planElement = None,
				Edges = None,
				 Restrictions = None):
				 #, non_static_preds = None):
				
		if type_graph == None:
			type_graph = 'PlanElementGraph'
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges=  set()
		if Restrictions == None:
			Restrictions = set()
		#if non_static_preds == None:
		#	non_static_preds = set()
		
		self.OrderingGraph = OrderingGraph(ID = uuid.uuid1(5))
		self.CausalLinkGraph = CausalLinkGraph(ID = uuid.uuid1(6))
		self.updatePlan(Elements)


		self.flaws = FlawLib()
		self.initial_dummy_step = None
		self.final_dummy_step = None
		
		
		if planElement is None:
			planElement = PlanElement(ID =ID, typ=type_graph,name=name)
		

		#Edges.update( {Edge(planElement,IF, 'frame-of') for IF in self.IntentionFrames})
		#Edges.update( {Edge(planElement,step, 'step-of') for step in self.Steps})
									
		super(PlanElementGraph,self).__init__(ID,type_graph,name,Elements,planElement,Edges,Restrictions)
		
		self.updateIntentionFrameAttributes()

	def __lt__(self, other):
		return (self.cost + self.heuristic) < (other.cost + other.heuristic)

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid1(21)
		return new_self


	@property
	def heuristic(self):
		#return self.flaws.heuristic
		return len(self.flaws) + len(self.flaws.nonreusable)

	@property
	def cost(self):
		return len(self.Steps)

	def subgraph(self, element, Type = None):
		if Type == None:
			Type = eval(element.typ)
		return self.getElementGraphFromElement(element, Type)


	def subgraphFromID(self, element_ID, Type = None):
		return self.subgraph(self.getElementById(element_ID), Type)

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent() and \
			   super(PlanElementGraph, self).isInternallyConsistent()


	def updateIntentionFrameAttributes(self):
		for element in self.elements:
			if type(element) == IntentionFrameElement:
				element.external_update(self)
			#Keeps intention frame element attributes up to date
			#Must be done after super instantation because needs edges
	
	def updatePlan(self, Elements = None,Restrictions = None):
		""" Updating plans to have accurate top-level Sets"""
		if Elements is None:
			Elements = self.elements
		self.Steps = {element for element in Elements if type(element) is Operator}
		self.Orderings = self.OrderingGraph.edges
		self.Causal_Links = self.CausalLinkGraph.edges
		self.IntentionFrames = {element for element in Elements if type(element) is IntentionFrameElement}
		return self
											
	def getConsistentActors(self, subseteq):
		""" Given subseteq of step elements in plan, return set of consistent actors (i.e. an actor that could be a consenting actor in each)
		"""
		step = next(iter(subseteq))
		print('step {} used for starting actors'.format(step.ID))
		Step = self.subgraph(step,Action)
		S = copy.deepcopy(subseteq)
		S = S - {action for action in S if action.ID == step.ID}
		return self.rPickActorFromSteps(remaining_steps = S, potential_actors = Step.consenting_actors)
			
	def rPickActorFromSteps(self, remaining_steps = None, potential_actors = None):
		if remaining_steps == None:
			remaining_steps = set()
		if potential_actors == None:
			return set()
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
		print(step)
		step = self.getElementGraphFromElementID(step.ID,Action)
		
		to_remove = set()
		to_add = set()
		for actor in potential_actors:
			print('potential actor: {}'.format(actor))
			print('prospects: ')
			for p in step.consenting_actors:
				print(p)
			prospects = {prospect for prospect in step.consenting_actors if actor.isConsistent(prospect)}
			print('consistent prospects: ')
			for p in prospects:
				print(p)
			if len(prospects) == 0:
				to_remove.add(actor)
				#potential_actors.remove(actor)
			else:
				to_add.update(prospects)
		
		potential_actors -= to_remove
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
		Step = new_self.getElementGraphFromElementID(partial.ID, Action)
		operatorClones = {op.instantiateOperator() for op in operator_choices}
		for op in operatorClones:
			#nStep = Step.copyGen()
			complete_steps.update(op.UnifyWith(Step))
		return complete_steps
		
	'''for debugging'''
	def getActions(self):
		return list(self.getElementGraphFromElement(step,Action) for step in self.Steps)

	@clock
	def detectThreatenedCausalLinks(self):
		"""
		A threatened causal link flaw is a tuple <causal link edge, threatening step element>
			where if s --p--> t is a causal link edge and s_threat is the threatening step element,
				then there is no ordering path from t to s_threat,
				no ordering path from s_threat to s,
				there is an effect edge from s_threat to a literal false-p',
				and p' is consistent with p after flipping the truth attribute
		"""

		detectedThreatenedCausalLinks = set()
		for causal_link in self.CausalLinkGraph.edges:
			nonThreats = self.CausalLinkGraph.nonThreats
			dependency = self.subgraph(causal_link.label,Condition)
			reverse_dependency = copy.deepcopy(dependency)
			# Reverse the truth status of the dependency
			if reverse_dependency.root.truth == True:
				reverse_dependency.root.truth = False
			else:
				reverse_dependency.root.truth = True

			for step in self.Steps:
				if step in nonThreats[causal_link]:
					continue
				# First, ignore steps which either are the source and sink of causal link, or which cannot be ordered
				# between them
				if step == causal_link.source or step == causal_link.sink:
					nonThreats[causal_link].add(step)
					continue
				if self.OrderingGraph.isPath(causal_link.sink, step):
					nonThreats[causal_link].add(step)
					continue
				if self.OrderingGraph.isPath(step, causal_link.source):
					nonThreats[causal_link].add(step)
					continue

				# Is condition consistent?
				num_edges = len(dependency.edges)
				count = 0
				effects = self.getNeighborsByLabel(step, 'effect-of')
				for eff in effects:
					if eff in nonThreats[causal_link]:
						continue
					cond_graph = self.subgraph(eff, Condition)
					if len(cond_graph.edges) > num_edges:
						if cond_graph.isConsistentSubgraph(reverse_dependency):
							detectedThreatenedCausalLinks.add(Flaw((step, eff, causal_link), 'tclf'))
							count+=1
						#else:
						#always add that it's not a threat anymore, because we don't want to reconsider the same tclf
						#nonThreats[causal_link].add(eff)
					elif num_edges >= len(cond_graph.edges):
						if reverse_dependency.isConsistentSubgraph(cond_graph):
							detectedThreatenedCausalLinks.add(Flaw((step, eff, causal_link), 'tclf'))
							count+=1
						#else:
						#	nonThreats[causal_link].add(eff)
					nonThreats[causal_link].add(eff)
				if count == 0:
					nonThreats[causal_link].add(step)

		return detectedThreatenedCausalLinks

	def __repr__(self):
		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps =  str([self.getElementGraphFromElement(step,Action) for step in self.Steps])
		orderings = self.OrderingGraph.__repr__()
		links = self.CausalLinkGraph.__repr__()
		return 'PLAN: ' + str(self.ID) + c + '\n*Steps: \n{' + steps + '}\n *Orderings:\n {' + orderings + '}\n ' \
																								   '*CausalLinks:\n {' + links + '}'