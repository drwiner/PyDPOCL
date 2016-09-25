
import itertools
import copy
from collections import namedtuple, defaultdict
from PlanElementGraph import Condition

#GStep = namedtuple('GStep', 'action pre_dict pre_link')
Antestep = namedtuple('Antestep', 'action eff_link')

class GStep:
	""" Container class for a ground action"""

	def __init__(self, action):
		self._action = action
		#self.pre_dict = defaultdict(set)
		#self.id_dict = defaultdict(set)
		#self.eff_dict = defaultdict(set)
		self.link = None

	def subgraph(self, elm):
		return Condition.subgraph(self._action,elm)

	def RemoveSubgraph(self, elm):
		self.link = self._action.RemoveSubgraph(elm)

	def getPreconditionsOrEffects(self, label):
		return self._action.getPreconditionsOrEffects(label)

	def replaceInternals(self):
		self._action.replaceInternals()

	def deepcopy(self):
		return copy.deepcopy(self._action)

	#def __getitem__(self, item):
	#	return self.pre_dict[item]
	def __getattr__(self, name):
		if name == 'num_risks':
			risks = 0
			for pre in self.preconditions:
				risks += len(GL.id_dict[pre.replaced_ID])
			self.num_risks = risks
			return self.num_risks
		elif name == 'preconditions':
			self.preconditions = self.getPreconditionsOrEffects('precond-of')
			return self.preconditions
		elif name == 'effects':
			self.effects = self.getPreconditionsOrEffects('effect-of')
			return self.effects
		else:
			raise AttributeError('no attribute {}'.format(name))
	#
	# @property
	# def preconditions(self):
	# 	return self.getPreconditionsOrEffects('precond-of')
	#
	# @property
	# def effects(self):
	# 	return self.getPreconditionsOrEffects('effect-of')

	@property
	def name(self):
		return self._action.name

	@property
	def elements(self):
		return self._action.elements

	@property
	def edges(self):
		return self._action.edges

	@property
	def root(self):
		return self._action.root

	@property
	def typ(self):
		return self._action.typ

	@property
	def ID(self):
		return self._action.ID

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

class GLib:
	def __init__(self, operators, objects, obtypes, init_action, goal_action):
		self._gsteps = groundStepList(operators.union({init_action, goal_action}),objects, obtypes)
		self.pre_dict = defaultdict(set)
		self.id_dict = defaultdict(set)
		self.eff_dict = defaultdict(set)
		self.loadAll()

	def loadAll(self):
		for _step in self._gsteps:
			print('preprocessing step {}....'.format(_step))
			pre_tokens = _step.preconditions
			for _pre in pre_tokens:
				print('preprocessing precondition {} of step {}....'.format(_pre, _step))
				self.loadAnteSteps(_step, _pre)

	def loadAnteSteps(self, _step, _pre):
		Precondition = _step.subgraph(_pre)
		for gstep in self._gsteps:
			# Defense pattern

			#Defense 1
			if gstep.name == 'dummy_init':
				continue

			for _eff in gstep.effects:
				# Defense 2
				if not _eff.isConsistent(_pre):
					continue


				# Defense 3
				Effect = gstep.subgraph(_eff)
				if Effect.Args != Precondition.Args:
					continue

				# Create antestep
				antestep = gstep.deepcopy()
				eff_link = antestep.RemoveSubgraph(_eff)
				#eff_link.sink is not an antestep.element so its ID does not change
				antestep.replaceInternals()

				# Add antestep to _step.pre_dict
				self.pre_dict[_pre.ID].add(Antestep(antestep, eff_link))
				self.id_dict[_pre.ID].add(antestep.stepnumber)
				# step's precondition associated with corresponding effect of antestep
				self.eff_dict[_pre.ID].add(eff_link.sink.ID)


	# def Antesteps(self, stepnum, pre_token):
	# 	return self[stepnum].pre_dict[pre_token]
	#
	# def AntestepsByPreID(self, stepnum, pre_ID):
	# 	gstep = self[stepnum]
	# 	for elm in gstep.elements:
	# 		if elm.ID == pre_ID:
	# 			return gstep[elm]

	def __len__(self):
		return len(self._gsteps)

	def __getitem__(self, position):
		return self._gsteps[position]

	def __contains__(self, item):
		return item in self._gsteps

	def __repr__(self):
		return 'Grounded Step Library: \n' +  str([step.__repr__() for step in self._gsteps])



from pddlToGraphs import parseDomainAndProblemToGraphs
from Flaws import FlawLib


if __name__ ==  '__main__':
	domain_file = 'domains/ark-domain.pddl'
	problem_file = 'domains/ark-problem.pddl'

	operators, objects, object_types, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)

	from Planner import preprocessDomain, obTypesDict
	FlawLib.non_static_preds = preprocessDomain(operators)
	obtypes = obTypesDict(object_types)

	print("creating ground actions......\n")
	GL = GLib(operators, objects, obtypes, initAction, goalAction)

	print('\n')
	print(GL)

	# for gstep in GL:
	# 	print(gstep)
	# 	pre_tokens = gstep.getPreconditionsOrEffects('precond-of')
	# 	print('antes:')
	# 	for pre in pre_tokens:
	# 		print('pre: {} of step {}....\n'.format(pre, gstep))
	# 		for ante in gstep.pre_dict[pre]:
	# 			print(ante.action)
	# 		print('\n')
	# 	print('\n')
