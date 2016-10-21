
import itertools
import copy
import pickle
from collections import namedtuple, defaultdict
from PlanElementGraph import Condition, Action
from clockdeco import clock
from Plannify import Plannify
from Element import Argument, Actor, Operator, Literal
from pddlToGraphs import parseDomAndProb
from Graph import Edge
from Flaws import FlawLib
from GlobalContainer import GC
import hashlib

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

def groundDecompStepList(doperators, GL, stepnum=0):
	gsteps = []
	for op in doperators:
		#Subplans = Plannify(op.subplan, GL)
		for sp in Plannify(op.subplan, GL):

			GDO = copy.deepcopy(op)

			for elm in sp.elements:
				assignElmToContainer(GDO, sp, elm, list(op.elements))

			GDO.ground_subplan = sp
			GDO.root.stepnumber = stepnum
			GDO._replaceInternals()
			gsteps.append(GDO)
			stepnum += 1

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

import re
@clock
def upload(GL, name):
	n = re.sub('[^A-Za-z0-9]+', '', name)
	afile = open(n, "wb")
	pickle.dump(GL, afile)
	afile.close()

@clock
def reload(name):
	n = re.sub('[^A-Za-z0-9]+', '', name)
	afile = open(n, "rb")
	GL = pickle.load(afile)
	FlawLib.non_static_preds = GL.non_static_preds
	GC.object_types = GL.object_types
	afile.close()
	return GL

class GLib:

	def __init__(self, domain, problem):
		operators, dops, objects, obtypes, init_action, goal_action = parseDomAndProb(domain, problem)
		self.non_static_preds = FlawLib.non_static_preds
		self.object_types = GC.object_types
		self.objects = objects
		self._gsteps = groundStoryList(operators, self.objects, obtypes)

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
		self.pre_dict = defaultdict(set)
		self.ante_dict = defaultdict(set)
		self.id_dict = defaultdict(set)
		self.eff_dict = defaultdict(set)
		self.threat_dict = defaultdict(set)
		self.loadAll()

		D = groundDecompStepList(dops, self, stepnum=len(self._gsteps))
		self.loadPartition(D)
		self._gsteps[-2:] = D

		# init at [-2] second time
		self._gsteps.append(init_action)
		# goal at [-1] second time
		self._gsteps.append(goal_action)

		print('{} ground steps created'.format(len(self)))
		print('uploading')
		upload(self, domain + problem)

	def insert(self, _pre, antestep, eff):
		self.pre_dict[_pre.replaced_ID].add(antestep)
		self.id_dict[_pre.replaced_ID].add(antestep.stepnumber)
		self.eff_dict[_pre.replaced_ID].add(eff.replaced_ID)

	def loadAll(self):
		self.load(self._gsteps, self._gsteps)

	def loadPartition(self, doperators):
		#print('... for each decompositional operator ')
		self.load(doperators, self._gsteps)
		self.load(self._gsteps, doperators)

	def load(self, antecedents, consequents):
		for ante in antecedents:
			for pre in ante.Preconditions:
				self._loadAntecedentPerConsequent(consequents, ante, pre)

	def _loadAntecedentPerConsequent(self, antecedents, _step, _pre):
		for gstep in antecedents:
			if self._parseEffects(gstep, _step, _pre) > 0:
				self.ante_dict[_step.stepnumber].add(gstep.stepnumber)

	def _parseEffects(self, gstep, _step, _pre):
		count = 0
		for Eff in gstep.Effects:
			if Eff.Args != _pre.Args or Eff.name != _pre.name:
				continue
			if Eff.truth != _pre.truth:
				self.threat_dict[_step.stepnumber].add(gstep.stepnumber)
			else:
				self.insert(_pre, gstep.deepcopy(replace_internals=True), Eff)
				count += 1
		return count

	def getPotentialLinkConditions(self, src, snk):
		cndts = []
		for pre in self[snk.stepnumber].preconditions:
			if src.stepnumber not in self.id_dict[pre.replaced_ID]:
				continue
			cndts.append(Edge(src,snk, copy.deepcopy(pre)))
		return cndts

	def getPotentialEffectLinkConditions(self, src, snk):
		cndts = []
		for eff in self[src.stepnumber].effects:
			for pre in self[snk.stepnumber].preconditions:
				if eff.replaced_ID not in self.id_dict[pre.replaced_ID]:
					continue
				cndts.append(Edge(src, snk, copy.deepcopy(eff)))

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
		if pre_token is None:
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