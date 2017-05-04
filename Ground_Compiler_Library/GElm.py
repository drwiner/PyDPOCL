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

	def setup(self, step_to_cndt, precond_to_cndt, step_to_threats):
		"""
		:param step_to_cndt: dict of form GStep -> GStep^k such as D[step_num] -> [cndt antecedent step nums]
		:param precond_to_cndt: dict of form GLiteral -> GStep^k such as D[pre.ID] -> [cndt antecedent step nums]
		:param step_to_threat: dict of form GLiteral -> Gstep^k such as D[step_num] -> [cndt threat step nums]
		"""
		self.cndts = list(step_to_cndt[self.stepnum])
		self.cndt_map = {pre.ID: list(precond_to_cndt[pre.ID]) for pre in self.preconds}
		self.threats = list(step_to_threats[self.stepnum])

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
		self.open_preconds.remove(pre)
		# update choices to just those which are needed to fulfill open conditions

	def update_choices(self, steps):
		self.choices = [choice for pre in self.open_preconds for choice in self.cndt_map[pre.ID] if choice in steps]

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


class Plan:
	def __init__(self, name, Restrictions=None):
		self.name = name
		self.ID = uuid4()
		self.OrderingGraph = OrderingGraph()
		self.CausalLinkGraph = CausalLinkGraph()
		self.flaws = FlawLib()
		self.solved = False
		self.initial_dummy_step = None
		self.final_dummy_step = None
		self.steps = []

	def __hash__(self):
		return hash(self.ID)

	def __len__(self):
		return len(self.steps)

	def __getitem__(self, position):
		return self.Steps[position]

	def append(self, step):
		step.index = len(self)
		step.root.index = len(self)
		self.steps.append(step.root)
		self.Steps.append(step)

	def extend(self, iter):
		for step in iter:
			self.append(step)

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

	@property
	def heuristic(self):
		return sum(oc.heuristic for oc in self.flaws.flaws)

	@property
	def cost(self):
		return len(self.Steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent()

	def detectTCLFperCL(self, GL, causal_link):
		detectedThreatenedCausalLinks = set()
		for step in self:
			self.testThreat(GL, self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def detectTCLFperStep(self, GL, step):
		detectedThreatenedCausalLinks = set()
		for causal_link in self.CausalLinkGraph.edges:
			self.testThreat(GL, self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def testThreat(self, GL, nonThreats, causal_link, step, dTCLFs):
		if step.index in nonThreats[causal_link]:
			return
		if step.root == causal_link.source or step.root == causal_link.sink:
			return
		if self.OrderingGraph.isPath(causal_link.sink, step.root):
			nonThreats[causal_link].add(step.index)
			return
		if self.OrderingGraph.isPath(step, causal_link.source):
			nonThreats[causal_link].add(step.index)
			return
		if step.stepnumber not in GL.threat_dict[causal_link.label.litnumber]:
		#if step.stepnumber not in GL.threat_dict[causal_link.sink.stepnumber]:
			nonThreats[causal_link].add(step.index)
			return
	#	if test(self[step.index], causal_link):
		dTCLFs.add(TCLF((step.root, causal_link), 'tclf'))
		nonThreats[causal_link].add(step.index)

	#@clock
	def detectThreatenedCausalLinks(self, GL):
		detectedThreatenedCausalLinks = set()
		for causal_link in self.CausalLinkGraph.edges:
			for step in self:
				self.testThreat(GL, self.CausalLinkGraph.nonThreats, causal_link, step, detectedThreatenedCausalLinks)
		return detectedThreatenedCausalLinks

	def __repr__(self):

		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps = [''.join('\t' + str(step.index) + ': ' + str(step) + '\n' for step in self)]
		order = [''.join('\t' + str(ordering.source) + ' < ' + str(ordering.sink) + '\n' for ordering in
			self.OrderingGraph.edges)]
		links = [''.join('\t' + str(cl) + '\n' for cl in self.CausalLinkGraph.edges)]
		return 'PLAN: ' + str(self.ID) + c + '\n*Steps: \n' + ''.join(['{}'.format(step) for step in steps]) + \
			   '*Orderings:\n' + \
			   ''.join(['{}'.format(o) for o in order]) + '*CausalLinks:\n' + ''.join(['{}'.format(link) for link in links]) + '}'

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