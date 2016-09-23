from PlanElementGraph import Action
import itertools
import copy

class GStep(Action):
	def __init__(self, action, uniqueInt):
		self.action = action
		self.list_num = uniqueInt
		self.pre_dict = {}
		self.pre_link = None

	@classmethod
	def makeGStep(cls, action, uniqueInt):
		return cls(action, uniqueInt)

def groundStepList(operators, objects, obtypes):
	gsteps = []
	for op in operators:
		op.updateArgs()
		cndts = [[obj for obj in objects if arg.typ == obj.typ or arg.typ in obtypes[obj.typ]] for arg in op.Args]
		tuples = itertools.product(*cndts)
		for t in tuples:
			gstep = copy.deepcopy(op)
			gstep.replaceArgs(t)
			gsteps.append(gstep)
	return gsteps

class GLib:
	def __init__(self, operators, objects, obtypes):
		self._gsteps = groundStepList(operators,objects, obtypes)

	def __len__(self):
		return len(self._gsteps)

	def __getitem__(self, position):
		return self._gsteps[position]


