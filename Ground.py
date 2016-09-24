
import itertools
import copy
from collections import namedtuple, defaultdict

#GStep = namedtuple('GStep', 'action pre_dict pre_link')
Antestep = namedtuple('Antestep', 'action eff_link')

class GStep:
	""" Container class for a ground action"""

	def __init__(self, action):
		self._action = action
		self.pre_dict = defaultdict(set)
		self.link = None

	def subgraph(self, elm):
		return self._action.subgraph(elm)

	def RemoveSubgraph(self, elm):
		self.link = self._action.RemoveSubgraph(elm)

	def getPreconditionsOrEffects(self, label):
		return self._action.getPreconditionsOrEffects(label)

	def replaceInternals(self):
		self._action.replaceInternals()

	def deepcopy(self):
		return copy.deepcopy(self._action)

	@property
	def name(self):
		return self._action.name

	def __repr__(self):
		return self._action.__repr__()

def groundStepList(operators, objects, obtypes):
	gsteps = []
	for op in operators:
		op.updateArgs()
		cndts = [[obj for obj in objects if arg.typ == obj.typ or arg.typ in obtypes[obj.typ]] for arg in op.Args]
		tuples = itertools.product(*cndts)
		for t in tuples:
			legaltuple = True
			for (u,v) in op.nonequals:
				if t[u] == t[v]:
					legaltuple = False
					break
			if not legaltuple:
				continue
			gstep = copy.deepcopy(op)
			gstep.replaceInternals()
			gstep.replaceArgs(t)
			gsteps.append(GStep(gstep))
	return gsteps



def loadAnteSteps(_gsteps, _step, _pre):
	"""

	@param _gsteps: list of gsteps
	@param _step: a particular step
	@param _pre: a particular precondition element of _step
	@return: a list of antesteps, gsteps with effect_links
	"""

	Precondition = _step.subgraph(_pre)

	for gstep in _gsteps:

		#Defense pattern
		for _eff in gstep.getPreconditionsOrEffects('effect-of'):

			#Defense 1
			if not _eff.isConsistent(_pre):
				continue

			#Defense 2
			Effect = gstep.subgraph(_eff)
			if Effect.Args != Precondition.Args:
				continue
		#	if not Effect.isConsistentSubgraph(Precondition):
			#	continue

			#Create antestep
			antestep = gstep.deepcopy()
			eff_link = antestep.RemoveSubgraph(_eff)
			antestep.replaceInternals()

			#Add antestep to _step.pre_dict
			_step.pre_dict[_pre].add(Antestep(antestep, eff_link))

class GLib:
	def __init__(self, operators, objects, obtypes):
		self._gsteps = groundStepList(operators,objects, obtypes)

	def loadAll(self):
		for _step in self._gsteps:
			print('\npreprocessing step {}....'.format(_step))
			pre_tokens = _step.getPreconditionsOrEffects('precond-of')
			for _pre in pre_tokens:
				print('\npreprocessing precondition {} of step {}....\n'.format(_pre, _step))
				loadAnteSteps(self._gsteps, _step, _pre)
				for antestep in _step.pre_dict[_pre]:
					print(antestep.action)

	def get

	def __len__(self):
		return len(self._gsteps)

	def __getitem__(self, position):
		return self._gsteps[position]

	def __contains__(self, item):
		return item in self._gsteps

	def __repr__(self):
		st= ' \n'
		return st.join(self._gsteps)




from pddlToGraphs import parseDomainAndProblemToGraphs
from Flaws import FlawLib
from Planner import preprocessDomain, obTypesDict, PlanSpacePlanner

if __name__ ==  '__main__':
	domain_file = 'domains/ark-domain.pddl'
	problem_file = 'domains/ark-problem.pddl'

	operators, objects, object_types, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)

	FlawLib.non_static_preds = preprocessDomain(operators)
	obtypes = obTypesDict(object_types)

	print("creating ground actions......\n")
	GL = GLib(operators, objects, obtypes)
	print("preprocessing ground actions.... \n")
	GL.loadAll()
	print('\n')

	for gstep in GL:
		print(gstep)
		pre_tokens = gstep.getPreconditionsOrEffects('precond-of')
		print('antes:')
		for pre in pre_tokens:
			print('pre: {} of step {}....\n'.format(pre, gstep))
			for ante in gstep.pre_dict[pre]:
				print(ante.action)
			print('\n')
		print('\n')

	#print(GL)

	print('ok')