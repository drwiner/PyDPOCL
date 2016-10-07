import itertools
from PlanElementGraph import Action, PlanElementGraph, Condition
from Graph import Edge
from clockdeco import clock

@clock
def Plannify(RQ, GL):
	#An ActionLib for steps in RQ - ActionLib is a container w/ all of its possible instances as ground steps
	print('ActionLibs')
	Libs = [ActionLib(i, RS, GL) for i, RS in enumerate([Action.subgraph(RQ, step) for step in RQ.Steps])]

	#A World is a combination of one ground-instance from each step
	Worlds = productByPosition(Libs)

	print('Planets')
	#A Planet is a plan s.t. all steps are "arg_name consistent", but a step may not be equiv to some ground step
	Planets = [PlanElementGraph.Actions_2_Plan(W) for W in Worlds if isArgNameConsistent(W)]

	print('Linkify')
	#Linkify installs orderings and causal links from RQ/decomp to Planets, rmvs Planets which cannot support links
	has_links = Linkify(Planets, RQ, GL)

	print('Groundify')
	#Groundify is the process of replacing partial steps with its ground step, and removing inconsistent planets
	Plans = Groundify(Planets, GL, has_links)

	print('returning consistent')
	return [Plan for Plan in Plans if Plan.isInternallyConsistent()]

@clock
def Unify(U, V, B = None):
	if B is None:
		B = set()
	#Create library of possible U-steps to reuse steps in V
	Reuse = [[u for u in U.Steps if u.stepnumber == v.stepnumber].append(v) for v in V.Steps]

	#Create step lists where either "u" is reused to unify with "v" or "v" is added
	Worlds = itertools.product(*Reuse)

	#Create new U-Plans to Integrate V info (links and orderings) or add v-steps not reused (or both)
	Plans = [U.Integrate(W, V) for W in Worlds]

	return [Plan for Plan in Plans if Plan.isInternallyConsistent()]


def partialUnify(PS, _map):
	if _map is False:
		return False
#	NS = PS.deepcopy()
	import copy
	NS = copy.deepcopy(PS)
	effects = [edge.sink for edge in NS.edges if edge.label == 'effect-of']
	for elm in effects:
		if elm in _map:
			g_elm = _map[elm]
			elm.merge(g_elm)
			elm.replaced_ID = g_elm.replaced_ID

	NSE = iter(NS.elements)
	for elm in NSE:
		if elm in _map:
			g_elm = _map[elm]
			elm.merge(g_elm)
			elm.replaced_ID = g_elm.replaced_ID
			if elm.replaced_ID == -1:
				# this is an object/constant
				ge = copy.deepcopy(g_elm)
				ge.replaced_ID = ge.ID
				NS.assign(elm,ge)
				#elm.replaced_ID = g_elm.ID
				#elm.ID = g_elm.ID
	NS.root.stepnumber = PS.root.stepnumber
	return NS

def isArgNameConsistent(Partially_Ground_Steps):
	"""
		@param Partially_Ground_Steps <-- partially ground required steps (PGRS), reach required step associated with ground step
	"""
	arg_name_dict = {}

	for PGS in Partially_Ground_Steps:
		for elm in PGS.elements:
			if not elm.arg_name is None:
				if elm.arg_name in arg_name_dict.keys():
					if not elm.isConsistent(arg_name_dict[elm.arg_name]):
						return False
				else:
					arg_name_dict[elm.arg_name] = elm
	return True

def productByPosition(Libs):
	return itertools.product(*[list(Libs[T.position]) for T in Libs])

def Linkify(Planets, RQ, GL):
	#Planets are plans containing steps which may not be ground steps from story_GL
	orderings = RQ.OrderingGraph.edges
	if len(orderings) > 0:
		for Planet in Planets:
			GtElm = Planet.getElementById
			try:
				Planet.OrderingGraph.edges = {Edge(GtElm(ord.source.ID), GtElm(ord.sink.ID),'<') for ord in orderings}
			except:
				raise AttributeError('why can I not use add ordering here?')

	links = RQ.CausalLinkGraph.edges
	if len(links) == 0:
		return False

	removable = set()
	for link in links:
		for i, Planet in enumerate(Planets):
			src = Planet.getElementById(link.source.ID)
			snk = Planet.getElementById(link.sink.ID)
			cond = Planet.getElementById(link.label.ID)

			if not src.stepnumber in GL.ante_dict[snk.stepnumber]:
				removable.add(i)
				continue

			if not GL.hasConsistentPrecondition(GL[snk.stepnumber],cond):
				removable.add(i)
				continue

			Planet.CausalLinkGraph.addEdge(src, snk, cond)
			Planet.OrderingGraph.addEdge(src,snk)


		Planets[:] = [Planet for i, Planet in enumerate(Planets) if not i in removable]
		removable = set()
		if len(Planets) == 0:
			raise ValueError('no Planet could support links in {}'.format(RQ.name))

	return True


def Groundify(Planets, GL, has_links):

	for Planet in Planets:
		for step in Planet.Steps:
			Step = Action.subgraph(Planet, step)
			Planet.UnifyActions(Step, GL[step.stepnumber])

	if not has_links:
		#we're done
		return Planets

	Discovered_Planets = []
	for Plan in Planets:
		Libs = [LinkLib(i,link,GL) for i, link in enumerate(Plan.CausalLinkGraph.edges)]

		#LW = [plan1 [link1.condition, link2.condition,..., link-n.condition],
			#  plan2 [link1.condition, link2.condition, ..., link-m.condition],
		    #  plan-k [l1,...,lz]]
		LW = productByPosition(Libs)

		for lw in LW:
			NP = Plan.deepcopy()
			for _link in lw:
				pre_token = GL.getConsistentPrecondition(Action.subgraph(NP, _link.sink), _link.label)
				pre_link = NP.RemoveSubgraph(pre_token)
				pre_link.sink = _link.label

			Discovered_Planets.append(NP)

	return Discovered_Planets


class ActionLib:

	def __init__(self, i, RS, GL):
		#RS.root.stepnumber = stepnum
		self.position = i
		RS.root.position = i
		self.RS = RS
		self.root = RS.root
		self._cndts = []
		for gs in GL:
			if not gs.root.isConsistent(self.RS.root):
				continue
			elm_maps = gs.findConsistentSubgraph(self.RS)
			if len(elm_maps) == 0:
				continue
			for map in elm_maps:
				if len(map) == 0:
					self.RS.root.merge(gs.root)
					self.RS.root.replaced_ID = gs.root.replaced_ID
				self.append(partialUnify(self.RS, map), gs.stepnumber)
		if len(self) == 0:
			raise ValueError('no gstep compatible with RS {}'.format(self))

	def __len__(self):
		return len(self._cndts)

	def __getitem__(self, position):
		return self._cndts[position]

	def __setitem__(self, key, value):
		self._cndts[key] = value

	def append(self, item, stepnum):
		item.root.stepnumber = stepnum
		self._cndts.append(item)

	@property
	def edges(self):
		return self.RS.edges

	@property
	def elements(self):
		return self.RS.elements

	def __contains__(self, item):
		return item in self._cndts

	def __repr__(self):

		return self.RS.__repr__()




class LinkLib:

	def __init__(self, position, link, GL):
		"""
		@param position: in list of links of Planet
		@param link: ground steps
		@param Plan: Plan containing link
		@param GL: ground step library
		"""

		self.position = position
		self.source = link.source
		self.sink = link.sink
		self.condition = link.label

		#LinkLib is a library of potential conditions, just 1 if already specified
		self._links = []

		if not link.label.arg_name is None:
			#linked-by
			self._links = [Edge(link.source, link.sink, self.condition)]
		else:
			# add new condition for each potential condition
			self._links = GL.getPotentialEffectLinkConditions(link.source, link.sink)
			#self._links = story_GL.getPotentialLinkConditions(link.source, link.sink)

	def __len__(self):
		return len(self._links)

	def __getitem__(self, position):
		return self._links[position]

	def __repr__(self):
		return '{}-- link-pos {} --> {}'.format(self.source, self.position, self.sink)


class ReuseLib:
	def __init__(self, i, vstep, U):
		self.position = i
		self.step = vstep
		self._cndts = [ustep for ustep in U.Steps if ustep.stepnumber == vstep.stepnumber]
		self._cndts.append(vstep)



from uuid import uuid1 as uid
from Element import Argument, Actor, Operator, Literal
from ElementGraph import ElementGraph

class DiscLib:
	def __init__(self, i, story_element, DGL):
		self.arg_to_elm(i, story_element)
		self.findCandidates()

	def __len__(self):
		return len(self._cndts)

	def __getitem__(self, position):
		return self._cndts[position]

	def arg_to_elm(self, i, arg):

		if arg.typ == 'character' or arg.typ == 'actor':
			elm = Actor(ID=uid(i), name=arg.name, typ='character', arg_name=arg.arg_name)
		elif arg.typ == 'arg' or arg.typ == 'item' or arg.typ == 'place':
			elm = Argument(ID=uid(i), name=arg.name, typ=arg.typ, arg_name=arg.arg_name)
		elif arg.typ == 'step':
			elm = Operator(ID=uid(i), name=arg.name, typ='Action', arg_name=arg.arg_name)
		elif arg.typ == 'literal' or arg.typ == 'lit':
			elm = Literal(ID=uid(i), name=arg.name, typ='Condition', arg_name=arg.arg_name)
		else:
			raise ValueError('whose typ is this anyway? {}'.format(arg.typ))
		self.element = elm
		self.typ = elm.typ

	def findCandidates(self):
		cndts = []
		for dgl in DGL:
			for elm in dgl.elements:
				if isinstance(elm,ElementGraph):
					if elm.root.typ == self.typ:
						cndts.append(elm)
				elif isinstance(elm,Argument):
					if elm.isConsistent(self.element):
						cndts.append(elm)
		self._cndts = cndts