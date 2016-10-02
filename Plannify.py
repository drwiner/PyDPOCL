import itertools
from PlanElementGraph import Condition, Action, PlanElementGraph
from Graph import Edge
import copy
from Ground import Antestep

def consistentConditions(GSIS, DP):
	"""
	@param GSIS:  Ground Sink Step
	@param DP: Link Condition
	@return: GSIS preconditions consistent with Dependency
	"""
	c_precs = set()
	for pre in GSIS.preconditions:
		if not pre.isConsistent(DP.root):
			continue
		PC = Condition.subgraph(GSIS, pre)
		if DP.Args != PC.Args:
			continue
		c_precs.add(pre.replaced_ID)
	return c_precs

def partialUnify(PS, _map):
	if _map is False:
		return False
	NS = PS.deepcopy()
	for elm in NS.elements:
		if elm in _map:
			g_elm = _map[elm]
			elm.merge(g_elm)
			elm.replaced_ID = g_elm.replaced_ID
	NS.root.stepnumber = PS.root.stepnumber
	return NS

def Unify(P, G):
	#new_elms = {elm for elm in G if elm.name not in (elm.name for elm in P.elements)}
	NG = G.deepcopy(replace_internals = True)
	P.elements.update({elm for elm in NG.elements if elm.replaced_ID not in (elm.replaced_ID for elm in P.elements)})
	P.edges.update({Edge(P.getElmByRID(edge.source.replaced_ID), P.getElmByRID(edge.sink.replaced_ID),edge.label)
					for edge in NG.edges})

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

# def GroundWorlds(Sub_Libs, GL):
# 	return itertools.product(*[list(GL[SL[SL.position].stepnumber]) for SL in Sub_Libs])

def Plannify(RQ, GL):
	#An ActionLib for steps in RQ - ActionLib is a container w/ all of its possible instances as ground steps
	Libs = [ActionLib(i, RS, GL) for i, RS in enumerate([Action.subgraph(RQ, step) for step in RQ.Steps])]

	#A World is a combination of one ground-instance from each step
	Worlds = productByPosition(Libs)

	#A Planet is a plan s.t. all steps are "arg_name consistent", but a step may not be equiv to some ground step
	Planets = [PlanElementGraph.Actions_2_Plan(W) for W in Worlds if isArgNameConsistent(W)]

	#Linkify installs orderings and causal links from RQ/decomp to Planets, rmvs Planets which cannot support links
	has_links = Linkify(Planets, RQ)

	#Groundify is the process of replacing partial steps with its ground step, and removing inconsistent planets
	Plans = Groundify(Planets, GL, has_links)

	return Plans


def Linkify(Planets, RQ, GL):
	#Planets are plans containing steps which may not be ground steps from GL
	orderings = RQ.OrderingGraph.edges
	if len(orderings) > 0:
		for Planet in Planets:
			GtElm = Planet.getElementById
			Planet.OrderingGraph.edges = {Edge(GtElm(ord.source.ID), GtElm(ord.sink.ID),'<') for ord in orderings}

	links = RQ.CausalLinkGraph.edges
	if len(links) == 0:
		return False

	removable = set()
	for link in links:
		DP = None
		if not link.label.arg_name is None:
			DP = Condition.subgraph(RQ, link.label)

		for i, Planet in enumerate(Planets):
			src = Planet.getElementById(link.source.ID)
			snk = Planet.getElementById(link.sink.ID)
			if DP is None:
				if not src.stepnumber in GL.ante_dict[snk.stepnumber]:
					removable.add(i)
					break
			else:
				for cpr in consistentConditions(GL[snk.stepnumber], DP):
					if not src.stepnumber in GL.id_dict[cpr]:
						removable.add(i)
						break
					else:
						#ought we store possible consistent conditions?
						pass
			if not i in removable:
				Planet.CausalLinkGraph.edges.add(src,snk,link.label)
		Planets[:] = [Planet for i, Planet in enumerate(Planets) if not i in removable]
		if len(Planets) == 0:
			raise ValueError('no Planet could support links in {}'.format(RQ.name))

	return True


def Groundify(Planets, GL, has_links):
	Discovered_Planets = set()
	Removable_Planets = set()

	for Planet in Planets:
		for step in Planet.Steps:
			Step = Action.subgraph(Planet, step)
			Unify(Step, GL[step.stepnumber])

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
			for pre in lw:
				#remove the precondition and let prelink.sink = effect
				eff_token = GL.getConsistentEffect(Action.subgraph(NP, link.source), pre)
				try:
					pre_link = NP.RemoveSubgraph(pre)
				except:
					raise ValueError('condition {} in Link World {} not found in plan {}'.format(pre,lw,Plan))
				pre_link.sink = eff_token
			Discovered_Planets.append(NP)

	return Discovered_Planets


		for link in Planet.CausalLinkGraph.edges:
			DP = None
			if not link.label.arg_name is None:
				DP = Condition.subgraph(Planet, link.label)
			else:
				#create new worlds for each possible causal link
				Sink = Action.subgraph(Planet, link.sink)
				for pre in Sink.preconditions:
					try:
						eff = GL.getConsistentEffect(Action.subgraph(Planet,link.source),pre)
					except:
						continue

					#NP = Planet.deepcopy()
					pre_link = NP.RemoveSubgraph(pre)
					pre_link.sink = eff
					Discovered_Planets.add(NP)
					Removable_Planets.add(Planet)

				{dep for dep in GL.id_dict}
				consistentConditions(link.sink.stepnumber, DP)


class ActionLib:
	def __init__(self, i, RS, GL):
		#RS.root.stepnumber = stepnum
		self.position = i
		RS.root.position = i
		self.RS = RS
		self.root = RS.root
		self._subtopics = []
		for gs in GL:
			if not gs.root.isConsistent(self.RS.root):
				continue
			possible_map = gs.isConsistentSubgraph(self.RS, return_map=True)
			if possible_map is False:
				continue
			self.append(partialUnify(self.RS,possible_map),gs.stepnumber)
		if len(self) == 0:
			raise ValueError('no gstep compatible with RS {}'.format(self))

	def __len__(self):
		return len(self._subtopics)

	def __getitem__(self, position):
		return self._subtopics[position]

	def __setitem__(self, key, value):
		self._subtopics[key] = value

	def append(self, item, stepnum):
		item.root.stepnumber = stepnum
		self._subtopics.append(item)

	@property
	def edges(self):
		return self.RS.edges

	@property
	def elements(self):
		return self.RS.elements

	def __contains__(self, item):
		return item in self._subtopics

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

		#LinkLib is a library of potential conditions, just 1 if already specified
		self._conditions = []

		if not link.label.arg_name is None:
			self._conditions = [link.label]
		else:
			# add new condition for each potential condition
			self._conditions = GL.getPotentialLinkConditions(link.source.stepnumber, link.sink.stepnumber)

	def __len__(self):
		return len(self._conditions)
	def __getitem__(self, position):
		return self._conditions[position]

	def __repr__(self):
		return '{}-- link-pos {} --> {}'.format(self.source, self.position, self.sink)
