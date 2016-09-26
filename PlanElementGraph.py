from OrderingGraph import *
from Flaws import *
from collections import deque
import uuid
import random
import itertools
from clockdeco import clock

class Action(ElementGraph):
	#stepnumber = 2
	def __init__(self,ID,type_graph,name=None,Elements = None, root_element = None, Edges = None):
		
		if Edges == None:
			Edges = set()

		if root_element is None:
			root_element = Operator(uuid.uuid1(200),typ='Action')
			
		if Elements == None:
			Elements = {root_element}

		self.nonequals = set()
			
		super(Action,self).__init__(ID,type_graph,name,Elements,root_element,Edges,Restrictions = None)


	def RemoveSubgraph(self, elm):
		before = elm.ID
		elm = self.getElementById(elm.ID)
		if elm is None:
			print('o')
		link = None
		to_remove = set()
		for edge in self.edges:
			if edge.source == elm:
				to_remove.add(edge)
			if link is None:
				if edge.sink == elm:
					link = edge
		self.elements -= {elm}
		self.edges -= to_remove
		return link

	def getPreconditionsOrEffects(self, label):
		return {edge.sink for edge in self.edges if edge.label == label}

	def __getattr__(self, name):
		if name == 'preconditions':
			self.preconditions = self.getPreconditionsOrEffects('precond-of')
			return self.preconditions
		elif name == 'effects':
			self.effects = self.getPreconditionsOrEffects('effect-of')
			return self.effects
		else:
			raise AttributeError('no attribute {}'.format(name))

	@property
	def stepnumber(self):
		return self.root.stepnumber

	def replaceInternals(self):
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.ID = uuid.uuid1(self.root.stepnumber)


	def _replaceInternals(self):
		#self.ID = uuid.uuid1(self.root.stepnumber)
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.replaced_ID = uuid.uuid1(self.root.stepnumber)

				#elm.ID = elm.replaced_ID
				#elm.ID = uuid.uuid1(self.root.stepnumber)

		
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
		if hasattr(self.root, 'executed'):
			exe = self.root.executed
			if exe is None:
				exe = 'ex'
		else:
			exe = 'ex'

		return '{}-{}-{}'.format(exe, self.root.name, self.root.arg_name) + args
		
		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,ID,type_graph,name=None,Elements=None, root_element = None, Edges = None, Restrictions = None):
		
		super(Condition,self).__init__(ID,type_graph,name,Elements,root_element,Edges,Restrictions)
		self.labels = ['first-arg','sec-arg','third-arg','fourth-arg']

	def isConsistent(self, other):
		return self.isConsistentSubgraph(other)

	def numArgs(self):
		if not hasattr(self, 'Args'):
			self.updateArgs()
		return len({arg for arg in self.Args if not arg.name is None})

	def __repr__(self):
		self.updateArgs()
		args = str([' {}-{} '.format(arg.name, arg.typ) for arg in self.Args])
		return '{}-{}{}'.format(self.root.truth, self.root.name, self.typ) + args

		
class PlanElementGraph(ElementGraph):

	def __init__(self,ID,type_graph =None,name=None,Elements = None, planElement = None, Edges = None,
				 Restrictions = None):
				
		if type_graph == None:
			type_graph = 'PlanElementGraph'
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges=  set()
		if Restrictions == None:
			Restrictions = set()
		
		self.OrderingGraph = OrderingGraph(ID = uuid.uuid1(5))
		self.CausalLinkGraph = CausalLinkGraph(ID = uuid.uuid1(6))
		self.updatePlan(Elements)

		self.flaws = FlawLib()
		self.initial_dummy_step = None
		self.final_dummy_step = None

		if planElement is None:
			planElement = PlanElement(ID =ID, typ=type_graph,name=name)
									
		super(PlanElementGraph,self).__init__(ID,type_graph,name,Elements,planElement,Edges,Restrictions)

	def __lt__(self, other):
		return (self.cost + self.heuristic) < (other.cost + other.heuristic)

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid1(21)
		return new_self

	def RemoveSubgraph(self, literal):
		elm = self.getElementById(literal.ID)
		link = None
		to_remove = set()
		for edge in self.edges:
			if edge.source == elm:
				to_remove.add(edge)
			if link is None:
				if edge.sink == elm:
					link = edge
		self.elements -= {elm}
		self.edges -= to_remove
		return link


	def relaxedStep(self, GL, pre, goal_effs, count = None):
		if count == None:
			count = 0

		if len(goal_effs) == 0:
			return count

		antecedents = GL.id_dict[pre.replaced_ID]
		if not self.initial_dummy_step.stepnumber in antecedents:
			count+=1
			least = 1000
			for ante in antecedents:
				v = self.relaxedStep(GL, GL[ante], count)
				if v < least:
					least = v
			return count + least
		else:
			#goal = GL[self.final_dummy_step.stepnumber]
			#for eff in goal.effects:
			for ge in goal_effs:
				if ge.replaced_ID in GL.eff_dict[pre.replaced_ID]:
					goal_effs-={ge}
					break
			return count


		##while self.initial_dummy_step.stepnumber not in GL.id_dict[pre] for pre in step

	def calculateHeuristic(self, GL):
		value = 0
		for oc in self.flaws.OCs():
			_, pre = oc.flaw
			c = self.relaxedStep(GL,pre,GL[-2].effects,0)
			value += c
		return value

	@property
	def heuristic(self, GL):

		"""
		Strategy: number of steps, dropping deletes, needed to fulfill all open conditions
		GList: GL.id_dict[pre.replaced_ID] for pre in step.preconditions
					while init.stepnumber not in GL.id_dict[pre.replaced_ID:

		@return:
		"""
		#return self.flaws.heuristic
        #replace with
		return len(self.flaws) + len(self.flaws.nonreusable)

	@property
	def cost(self):
		return len(self.Steps)

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent() and \
			   super(PlanElementGraph, self).isInternallyConsistent()


	def updatePlan(self, Elements = None):
		""" Updating plans to have accurate top-level Sets"""
		if Elements is None:
			Elements = self.elements
		self.Steps = {element for element in Elements if type(element) is Operator}
		self.Orderings = self.OrderingGraph.edges
		self.Causal_Links = self.CausalLinkGraph.edges
		#self.IntentionFrames = {element for element in Elements if type(element) is IntentionFrameElement}
		return self

	'''for debugging'''
	def getActions(self):
		return list(Action.subgraph(self,step) for step in self.Steps)

	@clock
	def detectThreatenedCausalLinks(self, GL):
		"""
		A threatened causal link flaw is a tuple <causal link edge, threatening step element>
			where if s --p--> t is a causal link edge and s_threat is the threatening step element,
				then there is no ordering path from t to s_threat,
				no ordering path from s_threat to s,
				there is an effect edge from s_threat to a literal false-p',
				and p' is consistent with p after flipping the truth attribute
		"""

		detectedThreatenedCausalLinks = set()
		nonThreats = self.CausalLinkGraph.nonThreats
		for causal_link in self.CausalLinkGraph.edges:
			for step in self.Steps:

				#defense 1
				if step in nonThreats[causal_link]:
					continue

				# defense 2-4 - First, ignore steps which either are the source and sink of causal link, or which cannot
				#  be ordered between them
				if step == causal_link.source or step == causal_link.sink:
					nonThreats[causal_link].add(step)
					continue
				if self.OrderingGraph.isPath(causal_link.sink, step):
					nonThreats[causal_link].add(step)
					continue
				if self.OrderingGraph.isPath(step, causal_link.source):
					nonThreats[causal_link].add(step)
					continue

				count = 0
				Step = Action.subgraph(self,step)
				for eff in Step.effects:
					if eff.ID in GL.threat_dict[causal_link.label.replaced_ID]:
						detectedThreatenedCausalLinks.add(Flaw((step, eff, causal_link), 'tclf'))
						count += 1

				if count == 0:
					nonThreats[causal_link].add(step)

		return detectedThreatenedCausalLinks

	def __repr__(self):
		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps =  str([Action.subgraph(self, step) for step in self.Steps])
		orderings = self.OrderingGraph.__repr__()
		links = self.CausalLinkGraph.__repr__()
		return 'PLAN: ' + str(self.ID) + c + '\n*Steps: \n{' + steps + '}\n *Orderings:\n {' + orderings + '}\n ' \
																								   '*CausalLinks:\n {' + links + '}'