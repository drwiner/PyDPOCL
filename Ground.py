
import itertools
import copy
import pickle
from collections import namedtuple, defaultdict
from PlanElementGraph import Condition, Action
from clockdeco import clock
from Plannify import Plannify
from Element import Argument, Actor, Operator, Literal
from pddlToGraphs import parseDomAndProb

#GStep = namedtuple('GStep', 'action pre_dict pre_link')
Antestep = namedtuple('Antestep', 'action eff_link')

def groundStoryList(operators, objects, obtypes):
	stepnum = 0
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
			gstep._replaceInternals()
			gstep.root.stepnumber = stepnum
			gstep.root.arg_name = stepnum
			stepnum += 1
			gstep.replaceArgs(t)
			gsteps.append(gstep)
	return gsteps

def groundDecompStepList(operators, GL, stepnum=0):

	#For each ground subplan in Subplans, make a copy of DO s.t. each
	gsteps = []
	for op in operators:
		Subplans = Plannify(next(iter(op.subgraphs)), GL)
		for sp in Subplans:
			GDO = copy.deepcopy(op)
			for elm in sp.elements:
				ex_elms = list(op.elements)
				assignElmToContainer(GDO, sp, elm, ex_elms)
			GDO.ground_subplan = sp
			GDO.root.stepnumber = stepnum
			GDO._replaceInternals()
			stepnum += 1
			gsteps.append(GDO)

	return gsteps

def assignElmToContainer(GDO, SP, elm, ex_elms):
	for ex_elm in ex_elms:
		if ex_elm.arg_name is None:
			continue
		if elm.arg_name != ex_elm.arg_name:
			if isinstance(elm, Argument):
				if elm.name != ex_elm.name:
					continue
			else:
				continue

		EG = elm
		if elm.typ in {'Action', 'Condition'}:
			EG = eval(elm.typ).subgraph(SP, elm)

		GDO.assign(ex_elm, EG)

@clock
def upload(GL, name):
	afile = open(name,"wb")
	pickle.dump(GL, afile)
	afile.close()

@clock
def reload(name):
	afile = open(name,"rb")
	GL = pickle.load(afile)
	afile.close()
	return GL

class GLib:

	def __init__(self, domain, problem):
		operators, dops, objects, obtypes, init_action, goal_action = parseDomAndProb(domain, problem)

		self.objects = objects
		self._gsteps = groundStoryList(operators, obtypes)

		# init at [-2]
		init_action.root.stepnumber = len(self._gsteps)
		init_action._replaceInternals()
		init_action.replaceInternals()
		self._gsteps.append(init_action)
		# goal at [-1]
		goal_action.root.stepnumber = len(self._gsteps)
		goal_action._replaceInternals()
		goal_action.replaceInternals()
		self._gsteps.append(goal_action)

		#dictionaries
		self.initDicts()
		self.loadAll()

		#The consequence of putting this here is that these decomp operators will not be preconditions to steps at
		# lower levels of hierarchy... but this is a good thing?
		D =  groundDecompStepList(dops, self, stepnum=len(self._gsteps))
		self.loadPartition(D)
		self._gsteps[-2:] = D

		# init at [-2] second time
		self._gsteps.append(init_action)
		# goal at [-1] second time
		self._gsteps.append(goal_action)

		print('{} ground steps created'.format(len(self)))
		print('uploading')

		upload(self, domain + problem)

	def initDicts(self):
		self.pre_dict = defaultdict(set)
		self.ante_dict = defaultdict(set)
		self.id_dict = defaultdict(set)
		self.eff_dict = defaultdict(set)
		self.threat_dict = defaultdict(set)

	def loadAll(self, consequents):
		self.load(consequents, consequents)

	def loadPartition(self, doperators):
		self.load(doperators, self._gsteps)
		self.load(self._gsteps, doperators)

	def load(self, antecedents, consequents):
		for ante in antecedents:
			for pre in ante.preconditions:
				self._loadAntecedentPerConsequent(consequents, ante, pre)

	def _loadAntecedantsPerConsequent(self, antecedents, _step, _pre):
		Precondition = Condition.subgraph(_step, _pre)
		# if _step.stepnumber
		for gstep in antecedents:
			# Defense pattern
			count = 0
			for _eff in gstep.effects:
				# Defense 2
				if not _eff.isConsistent(_pre):
					# Defense 2.1

					if not _eff.isOpposite(_pre):
						continue
					# Defense 2.2
					Effect = Condition.subgraph(gstep, _eff)
					if Effect.Args != Precondition.Args:
						continue

					self.threat_dict[_step.stepnumber].add(gstep.stepnumber)
					continue

				# Defense 3
				Effect = Condition.subgraph(gstep, _eff)
				if Effect.Args != Precondition.Args:
					continue

				# Create antestep
				antestep = copy.deepcopy(gstep)
				eff_link = antestep.RemoveSubgraph(_eff)
				antestep.replaceInternals()

				self.pre_dict[_pre.replaced_ID].add(Antestep(antestep, eff_link))
				self.id_dict[_pre.replaced_ID].add(antestep.stepnumber)
				self.eff_dict[_pre.replaced_ID].add(eff_link.sink.replaced_ID)
				count += 1

			if count > 0:
				self.ante_dict[_step.stepnumber].add(gstep.stepnumber)

	def getPotentialLinkConditions(self, src, snk):
		from Graph import Edge
		cndts = []
		for pre in self[snk.stepnumber].preconditions:
			if src.stepnumber not in self.id_dict[pre.replaced_ID]:
				continue

			cndts.add(Edge(src,snk,copy.deepcopy(pre)))
		return cndts

	def getPotentialEffectLinkConditions(self, src, snk):
		from Graph import Edge
		cndts = []
		for eff in self[src.stepnumber].effects:
			for pre in self[snk.stepnumber].preconditions:
				if eff.replaced_ID not in self.id_dict[pre.replaced_ID]:
					continue
				cndts.add(Edge(src, snk, copy.deepcopy(eff)))

		return cndts

	def getConsistentEffect(self, S_Old, precondition):
		effect_token = None
		for eff in S_Old.effects:
			if eff.replaced_ID in self.eff_dict[precondition.replaced_ID] or self.eff_dict[eff.replaced_ID] == \
					self.eff_dict[precondition.replaced_ID]:
				effect_token = eff
				break
		if effect_token is None:
			raise AttributeError('story_GL.eff_dict empty but id_dict has antecedent')
		return effect_token

	def hasConsistentPrecondition(self, Sink, effect):
		for pre in Sink.preconditions:
			if effect.replaced_ID in self.eff_dict[pre.replaced_ID]:
				return True
		return False

	def getConsistentPrecondition(self, Sink, effect):
		pre_token = None
		for pre in Sink.preconditions:
			if effect.replaced_ID in self.eff_dict[pre.replaced_ID]:
				pre_token = pre
				break
		if pre_token == None:
			raise AttributeError('effect {} not in story_GL.eff_Dict for Sink {}'.format(effect, Sink))
		return pre_token

	def __len__(self):
		return len(self._gsteps)

	def __getitem__(self, position):
		return self._gsteps[position]

	def __contains__(self, item):
		return item in self._gsteps

	def __repr__(self):
		return 'Grounded Step Library: \n' +  str([step.__repr__() for step in self._gsteps])


from Flaws import FlawLib


if __name__ ==  '__main__':
	domain_file = 'domains/ark-domain.pddl'
	problem_file = 'domains/ark-problem.pddl'

	operators, objects, object_types, initAction, goalAction = parseDomAndProb(domain_file, problem_file)

	from Planner import preprocessDomain, obTypesDict
	FlawLib.non_static_preds = preprocessDomain(operators)
	obtypes = obTypesDict(object_types)

	print("creating ground actions......\n")
	GL = GLib(operators, objects, obtypes, initAction, goalAction)

	print('\n')
	print(GL)

	# for gstep in story_GL:
	# 	print(gstep)
	# 	pre_tokens = gstep.getPreconditionsOrEffects('precond-of')
	# 	print('antes:')
	# 	for pre in pre_tokens:
	# 		print('pre: {} of step {}....\n'.format(pre, gstep))
	# 		for ante in gstep.pre_dict[pre]:
	# 			print(ante.action)
	# 		print('\n')
	# 	print('\n')
