import itertools
class AssignmentLib:
	def __init__(self, required_steps, GL):
		self._assignments = [_Assignment(i, rs) for i, rs in enumerate(required_steps)]
		self.makeAssignments(GL)

	def makeAssignments(self, GL):
		for rs in self._assignments:
			for gs in GL:
				if not gs.root.isConsistent(rs.root):
					continue
				possible_map = gs.isConsistentSubgraph(rs, return_map=True)
				if possible_map is False:
					continue
				rs._gsteps.append(gs.stepnumber)
				rs._unified.append(possible_map)
			if len(rs) == 0:
				raise ValueError('no gstep compatible with rs {}'.format(rs))

	def __len__(self):
		return len(self._assignments)

	def __getitem__(self, item):
		return self._assignments[item.stepnumber]

	def remove(self, rs, gstepnum):
		self._assignments[rs.stepnumber].remove(gstepnum)

	def narrowByLink(self, link):

		pass

	@property
	def permutations(self):
		return itertools.product(*[list(self[rs.root]) for rs in self])

class _Assignment:
	def __init__(self, stepnum, rs):
		self.rs = rs
		self.root = rs.root
		self.rs.stepnumber = stepnum
		self._gstepnums = []
		self._unified = []

	def __len__(self):
		return len(self._gstepnums)

	def __getitem__(self, position):
		return self._gstepnums[position]

	def __contains__(self, item):
		return item in self._gstepnums

	def remove(self, stepnum):
		try:
			i = self._gstepnums.index(stepnum)
			self._gstepnums.remove(stepnum)
		except:
			raise ValueError('step num {} not in assignment of rs root {}'.format(stepnum, self.rs))
		del self._unified[i]