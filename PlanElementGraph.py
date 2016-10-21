from OrderingGraph import OrderingGraph, CausalLinkGraph
from Flaws import Flaw, FlawLib, TCLF
from uuid import uuid4
from Element import Argument, Element, Operator, Literal
from Graph import Edge
from ElementGraph import ElementGraph
from GlobalContainer import GC
import copy
import collections
from clockdeco import clock


class Action(ElementGraph):
	# stepnumber = 2
	def __init__(self, ID=None, type_graph=None, name=None, Elements=None, root_element=None, Edges=None):

		if type_graph is None:
			type_graph = 'Action'

		if Edges is None:
			Edges = set()

		if root_element is None:
			root_element = Operator()

		if Elements is None:
			Elements = {root_element}

		self.nonequals = set()
		self.is_decomp = False

		super(Action, self).__init__(ID, type_graph, name, Elements, root_element, Edges)
		self.replaced_ID = root_element.replaced_ID

	def __hash__(self):
		return hash(arg for arg in self.Args) ^ hash(self.root.name)

	def __eq__(self, other):
		if not isinstance(other, ElementGraph):
			return False
		if self.root.name == other.root.name:
			if self.Args == other.Args:
				return True
		return False

	# @property
	# def executed(self):
	# 	return self.root.executed

	def RemoveSubgraph(self, elm):
		edges = list(self.edges)
		elm = self.getElementById(elm.ID)

		if isinstance(elm, Literal):
			self.elements.remove(elm)

		link = None
		for edge in list(self.edges):
			if edge.source == elm:
				edges.remove(edge)
			if link is None:
				if edge.sink == elm:
					link = edge
		edges.remove(link)
		self.edges = set(edges)
		return link

	@property
	def Preconditions(self):
		self.updatePreconditionsOrEffects('precond-of')
		return [Condition.subgraph(self, pre) for pre in self.preconditions]

	@property
	def Effects(self):
		self.updatePreconditionsOrEffects('effect-of')
		return [Condition.subgraph(self, eff) for eff in self.effects]

	def updatePreconditionsOrEffects(self, label):
		if label == 'effect-of':
			self.effects = self.getPreconditionsOrEffects(label)
		elif label == 'precond-of':
			self.preconditions = self.getPreconditionsOrEffects(label)

	def getPreconditionsOrEffects(self, label):
		return [edge.sink for edge in self.edges if edge.label == label]

	def __getattr__(self, name):
		if name == 'preconditions':
			self.preconditions = self.getPreconditionsOrEffects('precond-of')
			return self.preconditions
		elif name == 'effects':
			self.effects = self.getPreconditionsOrEffects('effect-of')
			return self.effects
		elif name == 'Args':
			self.updateArgs()
			return self.Args
		else:
			raise AttributeError('no attribute {}'.format(name))

	@property
	def stepnumber(self):
		return self.root.stepnumber

	def replaceInternals(self):
		self.ID = uuid4()
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.ID = uuid4()

	def _replaceInternals(self):
		self.ID = uuid4()
		for elm in self.elements:
			if not isinstance(elm, Argument):
				elm.replaced_ID = uuid4()

	def deepcopy(self, replace_internals=False, _replace_internals=False):
		new_self = copy.deepcopy(self)
		if replace_internals:
			new_self.replaceInternals()
		if _replace_internals:
			new_self._replaceInternals()
		return new_self

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
		args = str([arg.name for arg in self.Args])
		if hasattr(self.root, 'executed'):
			exe = self.root.executed
			if exe is None:
				exe = ''
			else:
				exe += '-'
		else:
			exe = 'ex'
		id = str(self.root.ID)[19:23]
		return '{}{}-{}-{}'.format(exe, self.root.name, self.root.stepnumber, id) + args


class Condition(ElementGraph):
	""" A Literal used in causal link"""

	def __init__(self, ID=None, type_graph=None, name=None, Elements=None, root_element=None, Edges=None,
				 Restrictions=None):
		if type_graph is None:
			type_graph = 'Condition'
		if ID is None:
			ID = root_element.ID
		if root_element is None:
			root_element = Literal()
		if Elements is None:
			Elements = {root_element}
		if name is None:
			name = root_element.name

		super(Condition, self).__init__(ID, type_graph, name, Elements, root_element, Edges, Restrictions)
		self.replaced_ID = root_element.replaced_ID

	def __hash__(self):
		return hash(self.ID) ^ hash(self.root.name) ^ hash(self.root.truth) ^ hash(self.root.replaced_ID)

	@property
	def truth(self):
		return self.root.truth

	def __eq__(self, other):
		if not isinstance(other, ElementGraph):
			return False
		if self.root.name == other.root.name and self.root.truth == other.root.truth:
			if self.Args == other.Args:
				return True
		return False

	def isConsistent(self, other):
		if isinstance(other, ElementGraph):
			return self.isConsistentSubgraph(other)
		if isinstance(other, Literal):
			return self.root.isConsistent(other)

	def isOpposite(self, other):
		return self.name == other.name and self.truth != other.truth and self.Args == other.Args

	def numArgs(self):
		if not hasattr(self, 'Args'):
			self.updateArgs()
		return len([arg for arg in self.Args if arg.name is not None])

	def __repr__(self):
		self.updateArgs()
		args = str([arg.name for arg in self.Args])
		t = ''
		if not self.root.truth:
			t = 'not-'
		return '{}{}'.format(t, self.root.name) + args


class PlanElementGraph(ElementGraph):
	def __init__(self, ID=None, type_graph=None, name=None, Elements=None, plan_elm=None, Edges=None,
				 Restrictions=None):

		if ID is None:
			ID = uuid4()
		if type_graph is None:
			type_graph = 'PlanElementGraph'
		if Elements is None:
			Elements = set()
		if Edges is None:
			Edges = set()
		if Restrictions is None:
			Restrictions = set()

		self.OrderingGraph = OrderingGraph()
		self.CausalLinkGraph = CausalLinkGraph()

		self.flaws = FlawLib()
		self.solved = False
		self.initial_dummy_step = None
		self.final_dummy_step = None

		if plan_elm is None:
			plan_elm = Element(ID=ID, typ=type_graph, name=name)

		super(PlanElementGraph, self).__init__(ID, type_graph, name, Elements, plan_elm, Edges, Restrictions)

	def __hash__(self):
		return hash(self.name) ^ hash(self.typ) ^ hash(self.ID)

	@classmethod
	def Actions_2_Plan(cls, Actions):
		# Used by Plannify

		elements = set().union(*[A.elements for A in Actions])
		edges = set().union(*[A.edges for A in Actions])
		Plan = cls(name='Action_2_Plan', Elements=elements, Edges=edges)
		for edge in Plan.edges:
			if edge.label == 'effect-of':
				elm = Plan.getElementById(edge.sink.ID)
				elm.replaced_ID = edge.sink.replaced_ID

		Plan.OrderingGraph = OrderingGraph()
		Plan.CausalLinkGraph = CausalLinkGraph()
		# Plan.Steps = [A.root for A in Actions]
		return Plan

	def UnifyActions(self, P, G):
		# Used by Plannify

		NG = G.deepcopy(replace_internals=True)
		for edge in list(NG.edges):

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

	#@clock
	def __lt__(self, other):
		if self.cost + self.heuristic != other.cost + other.heuristic:
			return (self.cost + self.heuristic) < (other.cost + other.heuristic)
		elif self.heuristic != other.heuristic:
			return self.heuristic < other.heuristic
		elif self.cost != other.cost:
			return self.cost < other.cost
		elif len(self.flaws) != len(other.flaws):
			return len(self.flaws) < len(other.flaws)
		else:
			return self.OrderingGraph < other.OrderingGraph


	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		return new_self

	def RemoveSubgraph(self, literal):
		edges = list(self.edges)
		elm = self.getElementById(literal.ID)
		link = None
		self.elements.remove(elm)

		for edge in list(self.edges):
			if edge.source == elm:
				edges.remove(edge)
			if link is None:
				if edge.sink == elm:
					link = edge
		edges.remove(link)
		self.edges = set(edges)
		return link

	def ReplaceSubgraphs(self, literal_old, literal_new):
		edges = list(self.edges)
		elm = self.getElementById(literal_old.ID)
		link = None
		self.elements.remove(elm)

		for edge in list(self.edges):
			if edge.source == elm:
				edges.remove(edge)
			if link is None:
				if edge.sink == elm:
					link = edge
		edges.remove(link)
		link.sink = literal_new
		self.edges = set(edges)
		self.edges.add(link)
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

	def relaxedPre(self, GL, pre, visited=None):
		if visited is None:
			visited = collections.defaultdict(int)

		antecedents = GL.id_dict[pre.replaced_ID]

		if len(antecedents) == 0:
			return 1000

		for ant in antecedents:
			if len(GL[ant].preconditions) == 0:
				visited[ant] = 1
				return 1

		if self.initial_dummy_step.stepnumber not in antecedents:
			least = 1000
			for ante in antecedents:

				if ante in visited.keys():
					v = visited[ante]
				else:
					visited[ante] = 1000
					v = self.relaxedStep(GL, GL[ante], visited)
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
			oc.heuristic = c
			# print('flaw: {} , heuristic = {}'.format(oc,c))
			value += c

		return value

	@property
	def heuristic(self):
		return self.calculateHeuristic(GC.SGL)

	@property
	def cost(self):
		return len(self.Steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent() and \
			   super(PlanElementGraph, self).isInternallyConsistent()

	@property
	def Steps(self):
		return [element for element in self.elements if type(element) is Operator]

	@property
	def Step_Graphs(self):
		return [Action.subgraph(self, step) for step in self.Steps]


	def detectTCLFperCL(self, GL, causal_link):
		detectedThreatenedCausalLinks = set()
		nonThreats = self.CausalLinkGraph.nonThreats
		for step in self.Steps:
			self.testThreat(GL, nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def detectTCLFperStep(self, GL, step):
		detectedThreatenedCausalLinks = set()
		nonThreats = self.CausalLinkGraph.nonThreats
		for causal_link in self.CausalLinkGraph.edges:
			self.testThreat(GL, nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def testThreat(self, GL, nonThreats, causal_link, step, dTCLFs):
		if step in nonThreats[causal_link]:
			return
		if step == causal_link.source or step == causal_link.sink:
			nonThreats[causal_link].add(step)
			return
		if self.OrderingGraph.isPath(causal_link.sink, step):
			nonThreats[causal_link].add(step)
			return
		if self.OrderingGraph.isPath(step, causal_link.source):
			nonThreats[causal_link].add(step)
			return
		if step.stepnumber not in GL.threat_dict[causal_link.sink.stepnumber]:
			nonThreats[causal_link].add(step)
			return
		if test(Action.subgraph(self, step), causal_link):
			dTCLFs.add(TCLF((step, causal_link), 'tclf'))
		nonThreats[causal_link].add(step)

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
		#step = self.lastAdded
		#for eff in step.Effects:
		#	print(eff)
		#step
		#if step is None:

		for causal_link in self.CausalLinkGraph.edges:

			for step in self.Steps:
			#print('checking step {} for cl {}'.format(step, causal_link))
			# defense 1
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

				if step.stepnumber not in GL.threat_dict[causal_link.sink.stepnumber]:
					nonThreats[causal_link].add(step)
					continue

			#	print('still checking')

				if test(Action.subgraph(self, step), causal_link):
					detectedThreatenedCausalLinks.add(TCLF((step, causal_link), 'tclf'))
			# for eff in step.Effects:
			# 	if eff.isOpposite(causal_link.label):
			# 		detectedThreatenedCausalLinks.add(TCLF((step.root, causal_link), 'tclf'))
			# 		break

			nonThreats[causal_link].add(step)

		return detectedThreatenedCausalLinks

	def __repr__(self):
		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps = str([Action.subgraph(self, step) for step in self.Steps])
		orderings = self.OrderingGraph.__repr__()
		links = self.CausalLinkGraph.__repr__()
		return 'PLAN: ' + str(
			self.ID) + c + '\n*Steps: \n{' + steps + '}\n*Orderings:\n {' + orderings + '}\n*CausalLinks:\n {' + links + '}'

#@clock
def test(step, causal_link):
	for eff in step.Effects:
		if eff.isOpposite(causal_link.label):
			return True
	return False