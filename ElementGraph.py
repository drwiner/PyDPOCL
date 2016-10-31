from Restrictions import Restriction
from uuid import uuid4
from Graph import Graph, Edge
from GlobalContainer import GC
from Element import Operator, Literal, Argument
import copy

#if you subclass ElementGraph, please inform the authorities
#This class is essentially an experimental middle man between Graph.py and Graphs in PlanElementGraph.py use for
# prototyping.
class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""

	def __init__(self, ID=None, type_graph=None, name=None, Elements=None, root_element=None, Edges=None,
				 Restrictions=None):
		if type_graph is None:
			type_graph = 'ElementGraph'

		super(ElementGraph, self).__init__(ID, type_graph, name, Elements, Edges, Restrictions)

		#Element graph has a specific root... This class is a useless middleman and is scheduled for demolition.
		self.root = root_element

	#Nice and simple.
	def __eq__(self, other):
		if type(other) is not ElementGraph:
			if self.root.name == other.name:
				pass
			return False
		if self.root.name == other.root.name:
			if self.Args == other.Args:
				return True
		return False

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid4()
		return new_self

	def isConsistent(self, other):
		if isinstance(other) is not ElementGraph:
			return self.root.isConsistent(other)

		#may have issue with inital and goal dummy steps - check here
		if self.name == 'dummy_init' or self.name == 'dummy_goal':
			if other.name == 'dummy_init' or other.name =='dummy_goal':
				if self.name == other.name:
					return True
				else:
					raise NameError("{} vs {}, assert ==".format(self.name, other.name))
		if self.Args == other.Args:
			return True
		return False

	@classmethod
	def subgraph(cls, EG, e):
		"""
		INPLACE subgraph - still references same parent
		"""
		elm = EG.get_by_id(e.ID)
		edges = EG.rGetDescendantEdges(elm)
		elms = {edge.source for edge in edges}|{edge.sink for edge in edges}|{elm}
		new_EG = cls(root_element=elm, Elements=elms, Edges=edges)
		new_EG.updateArgs()
		return new_EG


	@property
	def Steps(self):
		return [element for element in self.elements if type(element) is Operator]

	@property
	def Step_Graphs(self):
		return [Action.subgraph(self, step) for step in self.Steps]

	def getSingleArgByLabel(self, label):
		for edge in self.edges:
			if edge.source == self.root:
				if edge.label == label:
					return edge.sink
		return None

	def updateArgs(self):
		self.Args = []
		for label in GC.ARGLABELS:
			arg = self.getSingleArgByLabel(label)
			if arg is None:
				break
			else:
				self.Args.append(arg)

	def replaceArg(self, original, replacer):

		self.elements.add(replacer)
		incoming = {edge for edge in self.edges if edge.sink == original}
		for edge in incoming:
			edge.sink = replacer


	def replaceArgs(self, arg_tuple):
		"""
		A method to replace all args, as ordered by their args in self.Args, by the args in tuple
		@param arg_tuple: a tuple of args ordered by their replacement of args in self
		@return: none
		"""
		if not len(arg_tuple) == len(self.Args):
			raise ValueError('cannot replace Args, arg_tuple too long/short for %s' % self.name)

		for i, arg in enumerate(arg_tuple):
			original = self.getSingleArgByLabel(GC.ARGLABELS[i])
			self.replaceArg(original, arg)
		self.updateArgs()


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
		self.height = root_element.height

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
		elm = self.get_by_id(elm.ID)

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
		args = str([arg.name if not isinstance(arg, ElementGraph) else arg for arg in
				   self.Args])
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

	@classmethod
	def makeCondition(cls, pred_name, tup, lit_num, trudom):
		parent = Literal(name=pred_name, truth=trudom)
		elements = {parent}.union(set(tup))
		edges = {Edge(parent, t, GC.ARGLABELS[i]) for i, t in enumerate(tup)}
		condition = cls(Elements=elements, root_element=parent, Edges=edges)
		#condition.replaced_ID = uuid4()
		condition.litnumber = lit_num
		condition.Args = [t for t in tup]
		return condition

	def replaceInternals(self):
		new_self = copy.deepcopy(self)
		new_self.root.ID = uuid4()
		return new_self

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
		args = str([arg.name if not isinstance(arg, Action) else arg for arg in self.Args])
		t = ''
		if not self.root.truth:
			t = 'not-'
		return '{}{}'.format(t, self.root.name) + args