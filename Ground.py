
import itertools
import copy
import pickle
from collections import namedtuple, defaultdict
from PlanElementGraph import GStep, Cond
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

def groundLiteralList(objects):
	glits = []
	litnum = 0
	ignorable = {'=', 'equals', 'equal'}
	for p_name, arg_generator in GC.predicate_types.items():
		if p_name in ignorable:
			continue
		cndts = [[obj for obj in objects if arg == obj.typ or arg in GC.object_types[obj.typ]] for arg in arg_generator]
		tuples = itertools.product(*cndts)
		for t in tuples:
			glits.append(Cond(p_name, t, litnum, True))
			glits.append(Cond(p_name, t, litnum+1, False))
			litnum += 2
	return glits


def groundStoryList(operators, glits, objects, obtypes):
	stepnum = 0
	gsteps = []
	print('...Creating Ground Steps')
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
			gstep.replaceArgs(t)
			gstep.replaceInternals()
			effects = [E.deepclone() for E in glits for effect in gstep.Effects if E == effect]
			preconditions = [P.deepclone() for P in glits for pre in gstep.Preconditions if P == pre]
			g = GStep(gstep.root, gstep.Args, preconditions, effects, stepnum)
			g.root.stepnumber = stepnum
			gsteps.append(g)
			g.height = 0
			g.root.height = 0

			print('Creating ground step {}'.format(g))
			stepnum += 1
	return gsteps

def groundDecompStepList(doperators, GL, stepnum=0, height=0):
	gsteps = []
	print('...Creating Ground Decomp Steps')
	for op in doperators:
		#Subplans = Plannify(op.subplan, GL)
		print('processing operator: {}'.format(op))
		for sp in Plannify(op.subplan, GL, height):

			GDO = copy.deepcopy(op)
			GDO.is_decomp = True

			if not rewriteElms(GDO, sp, op):
				continue
		#	for elm in sp.elements:
		#		assignElmToContainer(GDO, sp, elm, list(op.elements))

			GDO.root.is_decomp = True

			GDO.ground_subplan = sp
			GDO.root.stepnumber = stepnum
			GDO._replaceInternals()
			GDO.replaceInternals()
			gsteps.append(GDO)
			sp.root = GDO.root
			stepnum += 1
			GDO.height = height + 1
			GDO.root.height = height + 1

	return gsteps

def rewriteElms(GDO, sp, op):

	for elm in sp.elements:
		assignElmToContainer(GDO, sp, elm, list(op.elements))
	GDO.updateArgs()
	for (u,v) in op.nonequals:
		if GDO.Args[u] == GDO.Args[v]:
			return False
	for arg in GDO.Args:
		if isinstance(arg, Argument):
			if arg.name is None:
				return False
	return True

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
	afile.close()
	FlawLib.non_static_preds = GL.non_static_preds
	GC.object_types = GL.object_types

	return GL

class GLib:

	def __init__(self, domain, problem):
		operators, dops, objects, obtypes, init_action, goal_action = parseDomAndProb(domain, problem)
		self.non_static_preds = FlawLib.non_static_preds
		self.object_types = GC.object_types
		self.objects = objects

		self._glits = groundLiteralList(objects)
		self._gsteps = groundStoryList(operators, self._glits, self.objects, obtypes)

		#dictionaries
		self.ante_dict = defaultdict(set)
		self.cndt_dict = defaultdict(set)
		self.threat_dict = defaultdict(set)
		print('...Creating PlanGraph base level')
		self.loadAll()

		for i in range(3):
			print('...Creating PlanGraph decompositional level {}'.format(i+1))
			try:
				D = groundDecompStepList(dops, self, stepnum=len(self._gsteps), height=i)
			except:
				break
			if not D or len(D) == 0:
				break
			self.loadPartition(D)

		#self._gsteps.extend(D)
		#Preconditions = [Action.subgraph(init_action, pre) for pre in init_action.edges.sink if pre.label ==
		#				 'effect-of']
		init_pre = [P.deepclone() for P in self._glits for prec in init_action.Effects if P == prec]
		initial_dummy_step = GStep(init_action.root, [], [], init_pre, len(self._gsteps))
		goal_eff = [E.deepclone() for E in self._glits for eff in goal_action.Preconditions if E == eff]
		goal_dummy_step = GStep(goal_action.root, [], goal_eff, [], len(self._gsteps)+1)
		self.loadPartition([initial_dummy_step, goal_dummy_step])

		#	init_action._replaceInternals()
			#init_action.replaceInternals()
		#self._gsteps.append(init_action)
		# goal at [-1]
	#	goal_action.root.stepnumber = len(self._gsteps) + 1
	#	goal_action._replaceInternals()
	#	goal_action.replaceInternals()
	#	self._gsteps.append(goal_action)

	#	self.loadPartition([init_action, goal_action])
		#self.load({init_action}, self._gsteps)
	#	self.load(self._gsteps, {goal_action})
	#	self.load({init_action}, {goal_action})
		#self._gsteps.append(init_action)
		#self._gsteps.append(goal_action)

		print('{} ground steps created'.format(len(self)))
		print('uploading')
		upload(self, domain + problem)

	def insert(self, prelitnum, antestepnum, efflitnum):
		self.id_dict[prelitnum].add(antestepnum)
		#self.eff_dict[prelitnum].add(efflitnum)

	def loadAll(self):
		self.load(self._gsteps, self._gsteps)

	def loadPartition(self, particles):
		#print('... for each decompositional operator ')
		self.load(particles, self._gsteps)
		self.load(self._gsteps, particles)
		self.load(particles, particles)
		self._gsteps.extend(particles)

	def load(self, group1, group2):
		for t in group1:

			print('... Processing cndts of step {}'.format(t))
			self.ante_dict[t.stepnumber].update({s.stepnumber for s in group2 if set(t.Preconditions).intersection(
				s.Effects)})

			for pre in t.Preconditions:

				print('... Processing cndts for {} of step {}'.format(pre, t))
				self.cndt_dict[pre.litnumber].update({gstep.stepnumber for gstep in group2 if pre in gstep.Effects})

				print('... Processing threats to {} of step {}'.format(pre, t))
				opp = self._glits[pre.getOppLitNum()]
				self.threat_dict[pre.litnumber].update({gstep.stepnumber for gstep in group2 if opp in gstep.Effects})

	def __len__(self):
		return len(self._gsteps)

	def __getitem__(self, position):
		return self._gsteps[position]

	def __contains__(self, item):
		return item in self._gsteps

	def __repr__(self):
		steps = [str(step) + '\n' for step in self]
		return 'Grounded Step Library: \n' + ''.join(['{}'.format(step) for step in steps])

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