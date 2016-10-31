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

#readonly ground step
class GStep:

	def __init__(self, operator, args, preconditions, effects, stepnum):
		self.Args = args
		self.ID = uuid4()
		self.Preconditions = []
		self.Effects = []
		self.extendPreconditions(preconditions)
		self.extendEffects(effects)
		self.root = operator
		self.name = operator.name
		self.stepnumber = stepnum
		self.root.stepnumber = stepnum
		self.nonequals = set()
		self.is_decomp = False
		#self.replaced_ID = uuid4()

	def extendEffects(self, iter):
		for lit in iter:
			self.addEff(lit)

	def extendPreconditions(self, iter):
		for lit in iter:
			self.addPre(lit)

	def addEff(self, eff):
		eff.index = len(self.Effects)
		self.Effects.append(eff)
	def addPre(self, pre):
		pre.index = len(self.Preconditions)
		self.Preconditions.append(pre)

	def addPreOrEff(self, lit, group):
		lit.index = len(group)
		group.append(lit)

	def __hash__(self):
		return hash(self.ID)

	def __eq__(self, other):
		return self.stepnumber == other.stepnumber

	def replaceInternals(self):
		self.ID = uuid4()
		for pre in self.Preconditions:
			pre.ID = uuid4()
		for eff in self.Effects:
			eff.ID = uuid4()

	def deepcopy(self, replace_internals=False):
		new_self = copy.deepcopy(self)
		if replace_internals:
			new_self.replaceInternals()
		return new_self

	def __repr__(self):
		args = str([arg.name if not isinstance(arg, ElementGraph) else arg for arg in self.Args])
		return '{}-{}-{}'.format(self.name, self.stepnumber, str(self.ID)[19:23]) + args


class Cond:
	def __init__(self, pred_name, tup, lit_num, trudom, height):
		self.ID = uuid4()
		self.name = pred_name
		self.litnumber = lit_num
		self.Args = []
		self.truth = trudom
		self.extend(tup)
		self.height = height

	def __len__(self):
		return len(self.Args)

	def __getitem__(self, position):
		return self.Args[position]

	def __hash__(self):
		return self.litnumber #hash(self.ID)

	def __eq__(self, other):
		if isinstance(other, Condition):
			return self.name == other.name and self.Args == other.Args and self.truth == other.truth
		return self.litnumber == other.litnumber

	def deepclone(self):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		return new_self

	def append(self, arg):
		arg.index = len(self)
		self.Args.append(arg)

	def extend(self, iter):
		for arg in iter:
			self.append(arg)

	def isOpposite(self, other):
		if self.getOppLitNum() == other.litnumber:
			return True
		return False
		#return self.name == other.name and self.truth != other.truth and self.Args == other.Args

	def getOppLitNum(self):
		if self.truth:
			return self.litnumber + 1
		else:
			return self.litnumber - 1

	def __repr__(self):
		args = str([arg if not isinstance(arg, Argument) else arg.name for arg in self])
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
		self.Steps = []

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

	@classmethod
	def Actions_2_Plan(cls, Actions, h):
		# Used by Plannify

		if not checkHeight(Actions, h):
			return None

		Plan = cls(name='Action_2_Plan')
		for action in Actions:
			Plan.append(action)

		#elements = set().union(*[A.elements for A in Actions])
	#	edges = set().union(*[A.edges for A in Actions])
		#Plan = cls(name='Action_2_Plan', Elements=elements, Edges=edges)
	#	for edge in Plan.edges:
		#	if edge.label == 'effect-of':
		#		elm = Plan.get_by_id(edge.sink.ID)
		#		elm.replaced_ID = edge.sink.replaced_ID

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

	@property
	def heuristic(self):
		return sum(oc.heuristic for oc in self.flaws.flaws)

	@property
	def cost(self):
		return len(self.Steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent()

	# @property
	# def Steps(self):
	# 	return [element for element in self.elements if type(element) is Operator]
	#
	# @property
	# def Step_Graphs(self):
	# 	return [Action.subgraph(self, step) for step in self.Steps]

	# @property
	# def Steps_Sorted(self):
	# 	pass

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
	#	F = [('|' + ''.join([str(flaw) + '\n|' for flaw in T]), T.name) for T in self.typs if len(T) > 0]
		# flaw_lib_string = str(['\n {}: \n {} '.format(flaws, name) + '\n' for flaws, name in F])
	#	return '______________________\n|FLAWLIBRARY: \n|' + ''.join(['\n|{}: \n{}'.format(name, flaws) for
#																	  flaws, name in F]) + '______________________'
#
		c = '\ncost {} + heuristic {}'.format(self.cost, self.heuristic)
		steps = [''.join('\t' + str(step.index) + ': ' + str(step) + '\n' for step in self)]
		order = [''.join('\t' + str(ordering.source) + ' < ' + str(ordering.sink) + '\n' for ordering in
			self.OrderingGraph.edges)] #if ordering.source.stepnumber != self.initial_dummy_step.stepnumber and
			#ordering.sink.stepnumber != self.final_dummy_step.stepnumber)]
		#steps = str([''.join(str(Action.subgraph(self, step))) + '\n' for step in self.Steps]))
		links = [''.join('\t' + str(cl) + '\n' for cl in self.CausalLinkGraph.edges)]
		#orderings = self.OrderingGraph.__repr__()
		#links = self.CausalLinkGraph.__repr__()
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