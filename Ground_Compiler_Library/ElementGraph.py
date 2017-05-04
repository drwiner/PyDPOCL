from Ground_Compiler_Library.Restrictions import Restriction
import uuid
from Ground_Compiler_Library.Graph import Graph
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

		elm = EG.getElementById(e.ID)
		edges = EG.rGetDescendantEdges(elm)
		elms = {edge.source for edge in edges}|{edge.sink for edge in edges}|{elm}
		new_EG = cls(root_element=elm, Elements=elms, Edges=edges)
		new_EG.updateArgs()
		return new_EG


	def getSingleArgByLabel(self, label):
		for edge in self.edges:
			if edge.source == self.root:
				if edge.label == label:
					return edge.sink
		return None

	def updateArgs(self):
		self.Args = []
		for i in range(10):
			arg = self.getSingleArgByLabel(i)
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
			original = self.getSingleArgByLabel(i)
			self.replaceArg(original, arg)
		self.updateArgs()
