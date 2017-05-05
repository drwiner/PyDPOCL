from Ground_Compiler_Library.OrderingGraph import OrderingGraph, CausalLinkGraph
from Ground_Compiler_Library.Flaws import Flaw, FlawLib, TCLF
from uuid import uuid4
from Ground_Compiler_Library.Element import Argument, Element, Operator, Literal
from Ground_Compiler_Library.Graph import Edge
from Ground_Compiler_Library.ElementGraph import ElementGraph
import copy
import collections
from clockdeco import clock


class GStep:
	"""
	Read-Only Ground Step
	"""

	def __init__(self, operator, args, preconditions, stepnum, height):

		# READ-ONLY ATTRIBUTES #
		# schema refers to the name of the operator
		self.schema = operator
		# Args are Argument or Actor "Element" types
		self.Args = args
		# ID used as "instance ID"
		self.ID = uuid4()
		# preconds is a list of GCond
		self.preconds = preconditions
		# stepnum is the ground step constructor type
		self.stepnum = stepnum
		self.stepnumber = stepnum
		# height is 0 when primitive
		self.height = height

		self.cndts = None
		self.cndt_map = None
		self.threat_map = None
		self.threats = None


		# INSTANCE ATTRIBUTES #
		# risks are number of threat instances
		self.risks = list()
		self.choices = list()
		# choices are instances of cndt antecedents
		# self.num_choices = 0
		# open preconditions which need causal link
		self.open_preconds = list(self.preconds)

	# public methods #

	def setup(self, step_to_cndt, precond_to_cndt, step_to_threat, precond_to_threat):
		"""
		:param step_to_cndt: dict of form GStep -> GStep^k such as D[stepnum] -> [cndt antecedent step nums]
		:param precond_to_cndt: dict of form GLiteral -> GStep^k such as D[pre.ID] -> [cndt antecedent step nums]
		:param step_to_threat: dict of form GLiteral -> Gstep^k such as D[stepnum] -> [cndt threat step nums]
		"""
		self.cndts = list(step_to_cndt[self.stepnum])
		self.cndt_map = {pre.ID: list(precond_to_cndt[pre.ID]) for pre in self.preconds}
		self.threats = list(step_to_threat[self.stepnum])
		self.threat_map = {pre.ID: list(precond_to_threat[pre.ID]) for pre in self.preconds}

	def instantiate(self, default_refresh=None, default_None_is_to_refresh_open_preconds=None):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		if default_refresh is None:
			self.risks = list()
			self.choices = list()
		if default_None_is_to_refresh_open_preconds is None:
			self.open_preconds = list(self.preconds)
		return new_self

	def fulfill(self, pre):
		if self.cndt_map is None:
			raise AttributeError('Cndt Map not found; run setup(xyz) first')
		if pre.ID not in self.cndt_map:
			raise ValueError('{} not found in cndt_map, id={}'.format(pre, pre.ID))
		if pre not in self.preconds:
			raise ValueError('{} found in cndt_map w/ id={}, but {} not found in preconds'.format(pre, pre.ID, pre))
		# remove precondition from open precond
		if pre in self.open_preconds:
			self.open_preconds.remove(pre)
		else:
			print('pre: {} not found in {} to remove'.format(pre, self))

	def update_choices(self, plan):
		choices = set()
		for pre in self.open_preconds:
			choice_nums = self.cndt_map[pre.ID]
			for step in plan.steps:
				if plan.OrderingGraph.isPath(self, step):
					continue
				if step.stepnum in choice_nums:
					choices.add(step)
		self.choices = list(choices)

	def is_cndt(self, other):
		return other.stepnum in self.cndts

	def is_threat(self, other):
		return other.stepnum in self.threats

	# private hooks #

	def __hash__(self):
		return hash(self.ID)

	def __eq__(self, other):
		return self.stepnum == other.stepnum

	def __str__(self):
		args = str([arg.name if not isinstance(arg, ElementGraph) else arg for arg in self.Args])
		return str(self.schema) + args

	def __repr__(self):
		return self.__str__()


class GLiteral:
	"""
	A READ-ONLY Ground Literal / Condition
	"""
	def __init__(self, pred_name, arg_tup, trudom, _id, is_static):
		self.name = pred_name
		self.Args = list(arg_tup)
		self.truth = trudom
		self.ID = _id
		self.is_static = is_static

	def instantiate(self):
		return copy.deepcopy(self)

	def __hash__(self):
		return hash(self.ID)

	def __len__(self):
		return len(self.Args)

	def __eq__(self, other):
		if not isinstance(other, GLiteral):
			return False
		return self.name == other.name and self.Args == other.Args and self.truth == other.truth

	def __repr__(self):
		args = str([arg if not isinstance(arg, Argument) else arg.name for arg in self.Args])
		#args = str([arg.name if not isinstance(arg, Action) else arg for arg in self.Args])
		t = ''
		if not self.truth:
			t = 'not-'
		return '{}{}'.format(t, self.name) + args

#@clock
def test(step, causal_link):
	for eff in step.Effects:
		if eff.isOpposite(causal_link.label):
			return True
	return False

def topoSort(plan):
	OG = copy.deepcopy(plan.OrderingGraph)
	L =[]
	S = {plan.initial_dummy_step}
	while len(S) > 0:
		n = S.pop()
		L.append(n)
		for m_edge in OG.getIncidentEdges(n):
			OG.edges.remove(m_edge)
			if len({edge for edge in OG.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	return L

def checkHeight(listActions, height):
	for a in listActions:
		if a.height == height:
			return True
	return False