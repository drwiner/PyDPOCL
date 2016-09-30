import itertools
from PlanElementGraph import Condition, Action


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
	NS = AS.RS.deepcopy()
	for elm in NS.elements:
		if elm in _map:
			g_elm = _map[elm]
			elm.merge(g_elm)
			elm.replaced_ID = g_elm.replaced_ID
	NS.root.stepnumber = AS.root.stepnumber
	return NS

def isArgNameConsistent(Partially_Ground_Steps):
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

class AssignmentLib:
	def __init__(self, RQ, GL, objects):
		RQ.updatePlan()
		self._assignments = [_Assignment(i, RS) for i, RS in enumerate([Action.subgraph(RQ, step) for step in RQ.Steps])]
		self.makeAssignments(GL)
		self.Possible_Worlds = self.permutations
		if len(RQ.Steps) > 1:
			self.narrowByGroundElms()
			if len(RQ.CausalLinkGraph.edges) > 0:
				self.narrowByLinks(RQ, GL)
		for PW in self.Possible_Worlds:
			for world in PW:
				print(GL[world.stepnumber])
			print('\n')

	def makeAssignments(self, GL):
		for AS in self._assignments:
			for gs in GL:
				if not gs.root.isConsistent(AS.root):
					continue
				possible_map = gs.isConsistentSubgraph(AS, return_map=True)
				if possible_map is False:
					continue
				AS.append(partialUnify(AS, possible_map), gs.stepnumber)
			if len(AS) == 0:
				raise ValueError('no gstep compatible with RS {}'.format(AS))

	def __len__(self):
		return len(self._assignments)

	def __getitem__(self, position):
		return self._assignments[position]

	def remove(self, AS, position):
		self._assignments[AS.position].remove(position)

	def narrowByGroundElms(self):
		Possible_Worlds = []
		Action_Permutations = self.Possible_Worlds

		#APT = action permutation tuple
		for APT in Action_Permutations:

			#PGS = Partially Ground Step
			if isArgNameConsistent([PGS for PGS in APT]):
				Possible_Worlds.append(APT)

		self.Possible_Worlds = Possible_Worlds

	def narrowByLinks(self, RQ, GL):
		links = RQ.CausalLinkGraph.edges
		for link in links:

			DP = None
			if not link.label.arg_name is None:
				DP = Condition.subgraph(RQ, link.label)

			Removable_Worlds = []
			for World in self.Possible_Worlds:
				# position assigned during _Assignment
				wlsis = World[link.sink.position].stepnumber
				wlsos = World[link.source.position].stepnumber

				if DP is None: #then limit just by valid antecedent stepnumbers
					if not wlsos in GL.ante_dict[wlsis]:
						Removable_Worlds.append(World)
						#self.Possible_Worlds.remove(World)

				else: #link has a condition,
					for cpr in consistentConditions(GL[wlsis], DP):
						if not wlsos in GL.id_dict[cpr]:
							Removable_Worlds.append(World)
							#self.Possible_Worlds.remove(World)
							break
			for world in Removable_Worlds:
				self.Possible_Worlds.remove(world)


			if len(self.Possible_Worlds) == 0:
				raise ValueError('Cannot satisfy link {} criteria in decomp operator {}'.format(link, RQ.name))

	def constructWorld(self, World, GL):

		pass

	@property
	def permutations(self):
		return itertools.product(*[list(self[AS.position]) for AS in self])

	def __repr__(self):
		return str([world for world in self.Possible_Worlds])

class _Assignment:
	def __init__(self, i, RS):
		#RS.root.stepnumber = stepnum
		self.position = i
		RS.root.position = i
		self.RS = RS
		self.root = RS.root
		self._unifies = []

	def __len__(self):
		return len(self._unifies)

	def __getitem__(self, position):
		return self._unifies[position]

	def __setitem__(self, key, value):
		self._unifies[key] = value

	def append(self, item, stepnum):
		item.root.stepnumber = stepnum
		self._unifies.append(item)

	@property
	def edges(self):
		return self.RS.edges

	@property
	def elements(self):
		return self.RS.elements

	def __contains__(self, item):
		return item in self._unifies

	def __repr__(self):

		return self.RS.__repr__()