import itertools
from PlanElementGraph import Condition, Action


def consistentConditions(GL, Dependency, csm):
	c_precs = set()
	for pre in GL[csm].preconditions:
		if not pre.isConsistent(Dependency.root):
			continue
		Precondition = Condition.subgraph(GL[csm], pre)
		if Dependency.Args != Precondition.Args:
			continue
		c_precs.add(pre.replaced_ID)
	return c_precs

class AssignmentLib:
	def __init__(self, RQ, GL):
		self._assignments = [_Assignment(i, rs) for i, rs in enumerate([Action.subgraph(RQ, step) for step in RQ.Steps])]
		self.makeAssignments(GL)
		self.narrowByLinks(RQ, GL)

	def makeAssignments(self, GL):
		for rs in self._assignments:
			for gs in GL:
				if not gs.root.isConsistent(rs.root):
					continue
				possible_map = gs.isConsistentSubgraph(rs, return_map=True)
				if possible_map is False:
					continue
				rs._gstepnums.append(gs.stepnumber)
				rs._maps.append(possible_map)
			if len(rs) == 0:
				raise ValueError('no gstep compatible with rs {}'.format(rs))

	def __len__(self):
		return len(self._assignments)

	def __getitem__(self, position):
		if not type(position) is int:
			try:
				position = position.stepnumber
			except:
				raise ValueError('get item on assignments, trying to use {}'.format(position))
		return self._assignments[position]

	def __setitem__(self, key, value):
		self[key]._gstepnums = value

	def remove(self, rs, gstepnum):
		self._assignments[rs.stepnumber].remove(gstepnum)

	def narrowByLinks(self, RQ, GL):
		links = RQ.CausalLinkGraph.edges
		for link in links:
			cndt_sink_nums = self[link.sink.stepnumber]
			dependency = link.label
			if not dependency.arg_name is None:
				Dependency = Condition.subgraph(RQ, dependency)

			for csm in cndt_sink_nums:
				antes = GL.ante_dict[csm]

				if len(antes) == 0:
					self[link.sink] -= {csm}
					if len(self[link.sink.stepnumber]) == 0:
						raise ValueError('There is no link to satisfy the criteria of {}'.format(link))
					continue

				if dependency.arg_name is None:
					self[link.source.stepnumber] = list(antes)
					continue

				c_precs = consistentConditions(GL, Dependency, csm)
				self[link.source.stepnumber] = []
				for cp in c_precs:
					self[link.source.stepnumber].extend(list(GL.id_dict[cp]))
				if len(self[link.source.stepnumber]) == 0:
					raise ValueError('There is no link to satisfy the criteria of {}'.format(link))

	@property
	def permutations(self):
		return itertools.product(*[list(self[rs.root.stepnumber]) for rs in self])

class _Assignment:
	def __init__(self, stepnum, rs):
		rs.root.stepnumber = stepnum
		self.rs = rs
		self.root = rs.root
		self._gstepnums = []
		self._maps = []

	def __len__(self):
		return len(self._gstepnums)

	def __getitem__(self, position):
		if not type(position) is int:
			position = position.stepnumber
		return self._gstepnums[position]

	def __setitem__(self, key, value):
		self._gstepnums[key] = value

	@property
	def edges(self):
		return self.rs.edges

	@property
	def elements(self):
		return self.rs.elements

	def __contains__(self, item):
		return item in self._gstepnums

	def remove(self, stepnum):
		try:
			i = self._gstepnums.index(stepnum)
			self._gstepnums.remove(stepnum)
		except:
			raise ValueError('step num {} not in assignment of rs root {}'.format(stepnum, self.rs))
		del self._maps[i]
