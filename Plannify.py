import itertools
from PlanElementGraph import Condition, Action, PlanElementGraph
import copy
from Ground import Antestep

def consistentConditions(GSIS, DP):
	"""

	@param GSIS:  Ground Sink Step
	@param DP: Link Condition
	@return: GSIS preconditions cosnistent with Dependency
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

def partialUnify(AS, _map):
	if _map is False:
		return False
	NS = AS.RS.deepcopy()
	for elm in NS.elements:
		if elm in _map:
			g_elm = _map[elm]
			elm.merge(g_elm)
			elm.replaced_ID = g_elm.replaced_ID
	NS.root.stepnumber = AS.root.stepnumber
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


def GroundWorlds(Sub_Libs, GL):
	return itertools.product(*[list(GL[SL[SL.position].stepnumber]) for SL in Sub_Libs])

def Plannify(RQ, GL):
	Topics = [SubLib(i, RS, GL) for i, RS in enumerate([Action.subgraph(RQ, step) for step in RQ.Steps])]
	Worlds = itertools.product(*[list(Topics[T.position]) for T in Topics])
	Planets = [PlanElementGraph.Actions_2_Plan([W for W in Worlds if isArgNameConsistent(W)])]


	Ground_Worlds = GroundWorlds(
		[SubLib(i, RS, GL) for i, RS in enumerate([Action.subgraph(RQ, step) for step in
																			 RQ.Steps])]
		,GL)

	Planets = [PlanElementGraph.Actions_2_Plan([GW for GW in Ground_Worlds if isArgNameConsistent(GW)])]

	links = RQ.CausalLinkGraph.edges


	Linkify(Planets, RQ, GL)

def Linkify(Planets, RQ, GL):
	links = RQ.CausalLinkGraph.edges
	for link in links:
		for Plan in Planets:
			Plan.getElementById(link.source.ID)
	#For each planet, How can we replace with link source and sink in RQ with the

	for link in links:

		DP = None
		if not link.label.arg_name is None:
			DP = Condition.subgraph(RQ, link.label)

		Removable_Worlds = []
		Additional_Worlds = []
		for Plan in Planets:
			# position assigned during _Assignment
			wlsis = Plan.Steps[link.sink.position].stepnumber
			wlsos = Plan.Steps[link.source.position].stepnumber
			if DP is None:  # then limit just by valid antecedent stepnumbers
				# by default
				Removable_Worlds.append(World)
				if not wlsos in GL.ante_dict[wlsis]:
					continue
				for pre in GL[wlsis].preconditions:
					if not wlsos in GL.id_dict[pre.replaced_ID]:
						continue


class TopicLib:
	def __init__(self, RQ, GL, objects):
		RQ.updatePlan()
		self._planets = Plannify(RQ,GL)
		self.
		#= [SubLib(i, RS, GL) for i, RS in enumerate([Action.subgraph(RQ, step) for step in
																#		RQ.Steps])]

		#self.Possible_Worlds = self.permutations
		self.Possible_Worlds = self.GroundWorlds(GL)
		if len(RQ.Steps) > 1:
			self.Narrow_To_Plans(GL)
			if len(RQ.CausalLinkGraph.edges) > 0:
				self.Narrow_By_Links(RQ, GL)
		for PW in self.Possible_Worlds:
			for world in PW:
				print(GL[world.stepnumber])
			print('\n')

	def groundWorld(self, World, GL):
		#For each step in the world, if the step is not a link-source, then get its ground counterpart
			#if the step is a link source,
			# if the ground step is not already in the slot, then get the ground step from pre_dict where the pre is the link condition
			#if there is no link condition, then, how to determine which condition it is that connects it? Is there a reverse dictionary lookup (for key,value pair, if value == antecdent, then key is the precondition.replaced_ID. Then, use pre_dict[replaced_ID] to get the modified antecedent with missing effect
		pass

	def __len__(self):
		return len(self._topics)

	def __getitem__(self, position):
		return self._topics[position]

	#def remove(self, AS, position):
	#	self._topics[AS.position].remove(position)

	def Narrow_To_Plans(self, GL):
		Possible_Worlds = [] #maybe set()
		Action_Permutations = self.permutations

		#APT = action permutation tuple
		for APT in Action_Permutations:

			#PGS = Partially Ground Step
			if isArgNameConsistent([PGS for PGS in APT]):
				Possible_Worlds.append(PlanElementGraph.Actions_2_Plan([PGS.GroundWorld(GL) for PGS in APT]))

		self.Possible_Worlds = Possible_Worlds

	def Narrow_By_Links(self, RQ, GL):
		links = RQ.CausalLinkGraph.edges
		for link in links:

			DP = None
			if not link.label.arg_name is None:
				DP = Condition.subgraph(RQ, link.label)

			Removable_Worlds = []
			Additional_Worlds = []
			for World in self.Possible_Worlds:
				# position assigned during _Assignment
				wlsis = World[link.sink.position].stepnumber
				wlsos = World[link.source.position].stepnumber

				if DP is None: #then limit just by valid antecedent stepnumbers
					#by default
					Removable_Worlds.append(World)
					if not wlsos in GL.ante_dict[wlsis]:
						continue
					for pre in GL[wlsis].preconditions:
						if not wlsos in GL.id_dict[pre.replaced_ID]:
							continue

						New_World = copy.deepcopy(World)

						effect_token = GL.getConsistentEffect(S_Old, pre)
						pre_link = plan.RemoveSubgraph(pre)
						pre_link.sink = effect_token


						RetargetPrecondition
								eff = GL.eff_dict[pre.replaced_ID]
								New_World.action.removeSubgraph(pre)
							New_World[link.source.position] = GL.pre_dict[pre.replaced_ID]
							Additional_Worlds.append(New_World)

						#self.Possible_Worlds.remove(World)

				else: #link has a condition,
					Removable_Worlds.append(World)
					for cpr in consistentConditions(GL[wlsis], DP):
						if not wlsos in GL.id_dict[cpr]:

							#self.Possible_Worlds.remove(World)
							break
			#for world in Removable_Worlds:
			#	self.Possible_Worlds.remove(world)
			self.Possible_Worlds.extend(Additional_Worlds)


			if len(self.Possible_Worlds) == 0:
				raise ValueError('Cannot satisfy link {} criteria in decomp operator {}'.format(link, RQ.name))

	#I'm keeping this as a potential/candidate comparison for time-complexity analysis: b/c in this one,
# we don't limit plans first by whether they have consistent arg_name : value pairs.


	@property
	def permutations(self):
		return itertools.product(*[list(self[SL.position]) for SL in self])

	def __repr__(self):
		return str([world for world in self.Possible_Worlds])


def _(RS, GL):
	#returns list of gs stepnums
	r = [gs.stepnumber for gs in GL if gs.isConsistentSubgraph(RS)]


class SubLib:
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

	def GroundWorld(self, GL):
		return tuple(GL[step.stepnumber] for step in self)

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