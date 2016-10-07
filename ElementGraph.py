from Restrictions import *
import uuid

class ElementGraph(Graph):
	"""An element graph is a graph with a root element"""
	arglabels = ['first-arg', 'sec-arg', 'third-arg', 'fourth-arg', 'fifth-arg']

	def __init__(self, ID, type_graph, name=None, Elements=None, root_element=None, Edges=None, Restrictions=None):
		if Elements == None:
			Elements = set()
		if Edges == None:
			Edges = set()
		if Restrictions == None:
			Restrictions = set()

		super(ElementGraph, self).__init__(ID, type_graph, name, Elements, Edges, Restrictions)
		self.root = root_element

	def deepcopy(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid.uuid1(21)
		return new_self


	def isConsistent(self, other):
		if isinstance(other) is not ElementGraph:
			return False
		#may have issue with inital and goal dummy steps - check here
		if self.name == 'dummy_init' or self.name == 'dummy_goal':
			if other.name == 'dummy_init' or other.name =='dummy_goal':
				print('Could be issue here')
				if self.name == other.name:
					return True
				else:
					raise NameError("{} vs {}, assert ==".format(self.name, other.name))
		if self.Args == other.Args:
			return True
		return False

	@classmethod
	def subgraph(cls, EG, elm):
		"""
			INPLACE subgraph - still references same parent
		"""
		elm = EG.getElementById(elm.ID)
		edges = EG.rGetDescendantEdges(elm)
		elms = {edge.source for edge in edges}|{edge.sink for edge in edges}|{elm}
		new_EG= cls(elm.ID, elm.typ, name=None, root_element=elm, Elements=elms, Edges=edges)
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
		for label in self.arglabels:
			arg = self.getSingleArgByLabel(label)
			if arg is None:
				break
			else:
				self.Args.append(arg)


	def getArgLabel(self, arg):
		incoming = {edge for edge in self.edges if edge.source == self.root and edge.sink == arg}
		for edge in incoming:
			if edge.label in self.arglabels:
				return self.arglabels.index(edge.label)

	def getArgLabels(self, arg_tuple):
		return tuple(self.getArgLabel(arg) for arg in arg_tuple)

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
			original = self.getSingleArgByLabel(self.arglabels[i])
			self.replaceArg(original, arg)
		self.updateArgs()

	def replaceArgsFromLabels(self, arg_list, label_tuple):
		#self.updateArgs()
		if not len(self.Args) >= label_tuple[-1]:
			raise ValueError('cannot replace Args, label_tuple references nonexistent arg in %s' % self.name)

		for i,index in enumerate(label_tuple):
			label = self.arglabels[index]
			original = self.getSingleArgByLabel(label)
			self.replaceArg(original, arg_list[i])
		self.updateArgs()


	def UnifyWithMap(self, mapping_tuples):
		"""

		@param mapping_tuples: [0] receives merge from [1]. All edges in self to [1] go to [0]
		@return: nothing
		"""
		if mapping_tuples == None:
			raise ValueError('must provide mapping tuples {(a b),(x,y), etc} for unify in elementgraph')

		for (receiver, old_element) in mapping_tuples:
			if not old_element in self.elements:
				raise ValueError('old element {} in mapping_tuple in UnifyActions was not found elements...'.format(old_element.ID))
			if not receiver in self.elements:
				raise ValueError('receiver element {} in mapping_tuple in UnifyActions was not found in elements...'.format(receiver.ID))
			receiver.merge(old_element)
			self.replaceWith(old_element, receiver)

	def createArgMapping(self, litTokenA, litTokenB):
		ConditionA = self.subgraph(litTokenA)
		ConditionA.updateArgs()
		ConditionB = self.subgraph(litTokenB)
		ConditionB.updateArgs()
		return zip(ConditionA.Args,ConditionB.Args)

	def createArgMappingWithOther(self, litTokenA, other, litTokenB):
		ConditionA = self.subgraph(litTokenA)
		ConditionA.updateArgs()
		ConditionB = other.subgraph(litTokenB)
		ConditionB.updateArgs()
		return zip(ConditionA.Args, ConditionB.Args)

def assimilate(EG, ee, pe):
	new_self = EG.deepcopy()
	self_source = new_self.getElementById(ee.source.ID)  # source from new_self
	self_source.merge(pe.source)  # source merge
	self_source.replaced_ID = pe.source.ID
	self_sink = new_self.getElementById(ee.sink.ID)  # sink from new_self
	self_sink.replaced_ID = pe.sink.ID
	self_sink.merge(pe.sink)  # sink merge
	return new_self


import unittest
class TestInstantiations(unittest.TestCase):
	def test_method(self):
		""" Test Idea:
				Create three conditions between pairs of two graphs
				1) G1 is a subset of G2
				2) G1 has a subset which equals a subset of G2, but G1 is not a subset of G2
				3) G1 has

		"""
		Elms = [Element(ID=0, name='0'), Element(ID=1, name='1'), Element(ID=2, name='2'), Element(ID=3, name='3')]
		edges = {Edge(Elms[0], Elms[1], 'k1'), Edge(Elms[0], Elms[2], 'k2'), Edge(Elms[0], Elms[3], 'k3'),
				 Edge(Elms[2], Elms[1], 'j'), Edge(Elms[3], Elms[1], 'j')}
		G = Graph(ID=10, typ='test', Elements=set(Elms), Edges=edges)

		assert True

	def test_consistency(self):
		pass

if __name__ ==  '__main__':
	unittest.main()