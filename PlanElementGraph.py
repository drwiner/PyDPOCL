from OrderingGraph import *
from Flaws import *
from collections import deque
from uuid import uuid1 as uid
import random
import itertools
from clockdeco import clock

class DiscArg(ElementGraph):
	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None):
		super(DiscArg, self).__init__(ID, type_graph, name, Elements, root_element, Edges)
		self.typ = root_element.typ


class Action(ElementGraph):
	#stepnumber = 2
	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None):
		
		if Edges == None:
			Edges = set()

		if root_element is None:
			root_element = Operator(uid(200),typ='Action')
			
		if Elements == None:
			Elements = {root_element}

		self.nonequals = set()
			
		super(Action,self).__init__(ID, type_graph, name, Elements, root_element, Edges)

	# @property
	# def executed(self):
	# 	return self.root.executed

	def RemoveSubgraph(self, elm):
		elm = self.getElementById(elm.ID)
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
		self.ID = uid(self.root.stepnumber)
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.ID = uid(self.root.stepnumber)


	def _replaceInternals(self):
		self.ID = uid(self.root.stepnumber)
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.replaced_ID = uid(self.root.stepnumber)

	def deepcopy(self, replace_internals=False):
		new_self = copy.deepcopy(self)
		if replace_internals:
			new_self.replaceInternals()
		return new_self

				#elm.ID = elm.replaced_ID
				#elm.ID = uid(self.root.stepnumber)

		
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
		if isinstance(other, ElementGraph):
			return self.isConsistentSubgraph(other)
		if isinstance(other, Operator):
			return self.root.isConsistent(other)

		
	def __repr__(self):
		self.updateArgs()
		args = str(self.Args)
		if hasattr(self.root, 'executed'):
			exe = self.root.executed
			if exe is None:
				exe = 'ex'
		else:
			exe = 'ex'
		id = str(self.root.ID)[19:23]
		return '{}-{}-{}-{}'.format(exe, self.root.name, self.root.stepnumber,id) + args

		
class Condition(ElementGraph):
	""" A Literal used in causal link"""
	def __init__(self,ID,type_graph,name=None,Elements=None, root_element = None, Edges = None, Restrictions = None):
		
		super(Condition,self).__init__(ID,type_graph,name,Elements,root_element,Edges,Restrictions)
		self.labels = ['first-arg','sec-arg','third-arg','fourth-arg']

	# @property
	# def truth(self):
	# 	return self.root.truth

	def isConsistent(self, other):
		if isinstance(other, ElementGraph):
			return self.isConsistentSubgraph(other)
		if isinstance(other, Literal):
			return self.root.isConsistent(other)

	def numArgs(self):
		if not hasattr(self, 'Args'):
			self.updateArgs()
		return len({arg for arg in self.Args if not arg.name is None})

	def __repr__(self):
		self.updateArgs()
		args = str([' {}-{} '.format(arg.name, arg.typ) for arg in self.Args])
		return '{}-{}{}'.format(self.root.truth, self.root.name, self.typ) + args

		
class PlanElementGraph(ElementGraph):

	GL = None

	def __init__(self, ID, type_graph=None, name=None, Elements=None, plan_elm=None, Edges=None, Restrictions=None):
				
		if type_graph == None:
			type_graph = 'PlanElementGraph'
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges=  set()
		if Restrictions == None:
			Restrictions = set()
		
		self.OrderingGraph = OrderingGraph(ID=uid(5))
		self.CausalLinkGraph = CausalLinkGraph(ID=uid(6))

		self.flaws = FlawLib()
		self.initial_dummy_step = None
		self.final_dummy_step = None

		if plan_elm is None:
			plan_elm = PlanElement(uid=ID, typ=type_graph, name=name)
									
		super(PlanElementGraph,self).__init__(ID, type_graph, name, Elements, plan_elm, Edges, Restrictions)


	@classmethod
	def Actions_2_Plan(cls, Actions):
		# Used by Plannify

		elements = set().union(*[A.elements for A in Actions])
		edges = set().union(*[A.edges for A in Actions])
		Plan = cls(uid(2), name='Action_2_Plan', Elements=elements, Edges=edges)
		for edge in Plan.edges:
			if edge.label == 'effect-of':
				elm = Plan.getElementById(edge.sink.ID)
				elm.replaced_ID = edge.sink.replaced_ID

		Plan.OrderingGraph = OrderingGraph(ID=uid(5))
		Plan.CausalLinkGraph = CausalLinkGraph(ID=uid(6))
		#Plan.Steps = [A.root for A in Actions]
		return Plan

	def UnifyActions(self, P, G):
		#Used by Plannify

		NG = G.deepcopy(replace_internals=True)
		for edge in NG.edges:

			if edge.sink.replaced_ID == -1:
				sink = copy.deepcopy(edge.sink)
				sink.replaced_ID = edge.sink.ID
				self.elements.add(sink)
			else:
				sink = P.getElmByRID(edge.sink.replaced_ID)
				if sink is None:
					sink = copy.deepcopy(edge.sink)
					self.elements.add(sink)

			source = P.getElmByRID(edge.source.replaced_ID)
			if source is None:
				source = copy.deepcopy(edge.source)
				self.elements.add(source)

			self.edges.add(Edge(source, sink, edge.label))

	def Unify(self, other, bindings = None):
		#Unify two ground subplans
		#Combine elements,
		#Combine
		pass

	def Integrate(U, W, V, B):
		#W is [1,..., k] where  1--> k are the indices of V.Steps
		_map = {}
		for i, step in enumerate(W):
			if step in V.Steps:
				#don't add B if
				if (u.ID, v.ID, 1) in B:
					continue
				# then, add this step,
				U.AddSubgraph(Action.subgraph(V,step))
				_map[step] = step
			else:

				# if u and v must be distinct
				if (u.ID, v.ID, 0) in B:
					continue
				if (_, v.ID, 1) in B:
					if not _ == u.ID:
						continue
				# else, this v-step is to be reused by u-step
				_map[step] = U.Steps[i]

		for ordering in V.OrderingGraph.edges:
			U.OrderingGraph.addEdge(_map[ordering.source], _map[ordering.sink])
		for link in V.CausalLinkGraph.edges:
			#get the effect of the mapped u-step (possibly former vstep)
			condition = Action.subgraph(U,_map[link.source]).getElmByRID(link.label.replaced_ID)
			U.CausalLinkGraph.addEdge(_map[link.source],_map[link.sink],condition)
		return U

	def __lt__(self, other):
		return (self.cost + self.heuristic) < (other.cost + other.heuristic)

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uid(21)
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

	def AddSubgraph(self, subgraph):
		self.elements.update(subgraph.elements)
		self.edges.update(subgraph.edges)


	def relaxedStep(self, GL, step, visited):

		cost = 0
		for pre in step.preconditions:
			v = self.relaxedPre(GL, pre, visited)
			cost += v

		return cost

	def relaxedPre(self, GL, pre, visited = None):
		if visited == None:
			visited = collections.defaultdict(int)

		antecedents = GL.id_dict[pre.replaced_ID]

		if len(antecedents) == 0:
			return 1000


		if not self.initial_dummy_step.stepnumber in antecedents:
			least = 1000
			for ante in antecedents:

				if ante in visited.keys():
					v = visited[ante]
				else:
					visited[ante] = 1000
					v = self.relaxedStep(GL, GL[ante],visited)
					visited[ante] = v
				if v < least:
					least = v
			return least + 1
		return 0

	def calculateHeuristic(self, GL):
		value = 0

		for oc in self.flaws.flaws:
			_, pre = oc.flaw
			c = self.relaxedPre(GL, pre)
			oc.heuristic=c
			#print('flaw: {} , heuristic = {}'.format(oc,c))
			value += c

		return value

	@property
	def heuristic(self):

		"""
		Strategy: number of steps, dropping deletes, needed to fulfill all open conditions
		GList: story_GL.id_dict[pre.replaced_ID] for pre in step.preconditions
					while init.stepnumber not in story_GL.id_dict[pre.replaced_ID:

		@return:
		"""
		try:
			from GlobalContainer import GC
			if self.name == 'story':
				return self.calculateHeuristic(GC.SGL)
			return self.calculateHeuristic(GC.DGL)
		except:
			return 0

		#return len(self.flaws) + k

	# + len(self.flaws.nonreusable)
		#return self.flaws.heuristic

	@property
	def cost(self):
		#if not hasattr(self, 'Steps'):
			#self.updatePlan()
		return len(self.Steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent() and \
			   super(PlanElementGraph, self).isInternallyConsistent()

	@property
	def Steps(self):
		return [element for element in self.elements if type(element) is Operator]

	'''for debugging'''
	def getActions(self):
		return list(Action.subgraph(self,step) for step in self.Steps)

	#@clock
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

				if not step.stepnumber in GL.threat_dict[causal_link.sink.stepnumber]:
					nonThreats[causal_link].add(step)
					continue

				detectedThreatenedCausalLinks.add(Flaw((step, causal_link), 'tclf'))

		return detectedThreatenedCausalLinks

	def __repr__(self):
		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps =  str([Action.subgraph(self, step) for step in self.Steps])
		orderings = self.OrderingGraph.__repr__()
		links = self.CausalLinkGraph.__repr__()
		return 'PLAN: ' + str(self.ID) + c + '\n*Steps: \n{' + steps + '}\n *Orderings:\n {' + orderings + '}\n ' '*CausalLinks:\n {' + links + '}'

class BiPlan:
	""" A container class for story and discourse plans, so they behave as a single plan. A tuple with functionality """
	weight = 2
	def __init__(self, Story, Disc):
		self.insert(Story)
		self.insert(Disc)

	def isInternallyConsistent(self):
		return self.S.isInternallyConsistent() and self.D.isInternallyConsistent()

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.S.ID = uid(21)
		new_self.D.ID = uid(22)
		return new_self

	@property
	def heuristic(self):
		return self.S.heuristic + self.weight*self.D.heuristic

	@property
	def cost(self):
		return self.S.cost + self.weight*self.D.cost

	def __lt__(self, other):
		return (self.cost + self.heuristic) < (other.cost + other.heuristic)

	def num_flaws(self):
		return len(self.S.flaws) + len(self.D.flaws)

	def next_flaw(self):
		try:
			if len(self.S.flaws.statics) > 0:
				return 0, self.S.flaws.next()
			elif len(self.D.flaws) > 0:
				return 1, self.D.flaws.next()
			else:
				return 0, self.S.flaws.next()
		except:
			raise ValueError("shouldn't get here if no more flaws")

	def insert(self, kplan):
		if kplan.name == 'story':
			self.S = kplan
		else:
			self.D = kplan

	def __repr__(self):
		return self.S.__repr__() + self.D.__repr__()