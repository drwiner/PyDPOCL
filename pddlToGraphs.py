from pddl.parser import Parser
from collections import defaultdict
from Plan import Action, ElementGraph
from Graph import Edge
from Element import Argument, Operator, Literal, Element, Actor
from clockdeco import clock
import copy
from uuid import uuid4
from Flaws import FlawLib
from GlobalContainer import GC

#ARGLABELS = ['first-arg', 'sec-arg', 'third-arg', 'fourth-arg', 'fifth-arg', '6', '7', '8', '9', '10']


def makeGoal(formula):
	if formula.key == 'not':
		formula = next(iter(formula.children))
		num_children = len(formula.children)
		lit = Literal(name=formula.key, num_args=num_children, truth=False)
	else:
		num_children = len(formula.children)
		lit = Literal(name=formula.key, num_args=num_children, truth=True)
	return lit


def makeLit(formula, parent, relationship, elements, edges, bit=None, noAdd=None):
	if bit == None:
		bit = True
	if noAdd == None:
		noAdd = False
	num_children = len(formula.children)
	lit = Literal(name=formula.key, num_args=num_children, truth=bit)

	if not noAdd:
		elements.add(lit)
		edges.add(Edge(parent, lit, relationship))
	return lit, formula


def getNonEquals(formula, op_graph, elements, edges):
	# ARGLABELS
	(c1, c2) = formula.children
	arg1 = next(element for element in elements if c1.key.name == element.arg_name)
	arg2 = next(element for element in elements if c2.key.name == element.arg_name)
	edge1 = next(edge for edge in edges if edge.source.typ == 'Action' and edge.sink == arg1)
	edge2 = next(edge for edge in edges if edge.source.typ == 'Action' and edge.sink == arg2)
	i1 = GC.ARGLABELS.index(edge1.label)
	i2 = GC.ARGLABELS.index(edge2.label)
	op_graph.nonequals.add((i1, i2))


def getSubFormulaGraph(formula, op_graph, parent=None, relationship=None, elements=None, edges=None):
	if elements is None:
		elements = set()
	if edges is None:
		edges = set()

	'''make new literal representing subformula'''
	if formula.key == 'not':
		formula = next(iter(formula.children))
		if formula.key == 'intends':
			pass
			raise NameError('no intends yet')
		elif formula.key in {'equals', '=', 'equal'}:
			getNonEquals(formula, op_graph, elements, edges)
			return
		else:
			lit, formula = makeLit(formula, parent, relationship, elements, edges, False)
	elif formula.key == 'intends':
		raise NameError('no intends yet')
	elif formula.key == 'for-all' or formula.key == 'forall':
		raise NameError('no for-all yet')
	elif formula.type > 0:
		raise ValueError('not sure why formula.type > 0')
	else:
		lit, formula = makeLit(formula, parent, relationship, elements, edges, True)

	'''for each variable, find existing argument in action parameters and add Edge'''
	for i, child in enumerate(formula.children):
		arg = next(element for element in elements if child.key.name == element.arg_name)

		if relationship == 'actor-of':
			edges.add(Edge(parent, arg, 'actor-of'))
		else:
			edges.add(Edge(lit, arg, GC.ARGLABELS[i]))

	return elements, edges


def getFormulaGraph(formula, op_graph, parent=None, relationship=None, elements=None, edges=None):
	if parent is None:
		parent = Element()
	if edges is None:
		edges = set()
	if elements is None:
		elements = set()

	if formula.key == 'and':
		for child in formula.children:
			getSubFormulaGraph(child, op_graph, parent, relationship, elements, edges)
	else:
		getSubFormulaGraph(formula, op_graph, parent, relationship, elements, edges)


def getSubFormulaNoParent(formula, objects):
	elements = set()
	edges = set()
	if formula.key == 'not':
		formula = next(iter(formula.children))
		if formula.key == 'intends':
			raise NameError('no intends yet')

		else:
			lit = Literal(name=formula.key, num_args=len(formula.children), truth=False)
			elements.add(lit)
	elif formula.key == 'intends':
		raise NameError('no intends yet')
	elif formula.type > 0:
		raise ValueError('not sure why formula.type > 0')
	else:
		lit = Literal(name=formula.key, num_args=len(formula.children), truth=True)
		elements.add(lit)
	for i, child in enumerate(formula.children):
		# children are list
		arg = next(ob_element for ob_name, ob_element in objects.items() if child.key == ob_name)
		edges.add(Edge(lit, arg, GC.ARGLABELS[i]))
		elements.add(arg)
	return elements, edges


def getGoalSet(goal_formula, objects):
	""" Returns set of goal literals """
	goal_elements = set()
	goal_edges = set()
	if goal_formula.key == 'and':
		for child in goal_formula.children:
			elements, edges = getSubFormulaNoParent(child, objects)
			goal_elements.update(elements)
			goal_edges.update(edges)
	else:
		elements, edges = getSubFormulaNoParent(goal_formula, objects)
		goal_elements.update(elements)
		goal_edges.update(edges)

	return goal_elements, goal_edges


def decorateElm(child, DG):
	if child.key == 'name':
		elm = whichElm(child.children[0].key.name, DG)
		elm.name = child.children[1].key
	elif child.key == 'nth-step-arg' or child.key == 'nth-lit-arg':
		args = child.children
		label = GC.ARGLABELS[int(args[0].key)]
		parent_elm = whichElm(args[1].key.name, DG)
		child_elm = whichElm(args[2].key.name, DG)
		DG.edges.add(Edge(parent_elm, child_elm, label))
	elif child.key == 'includes':
		arg1, arg2 = child.children
		DG.edges.add(Edge(whichElm(arg1.key.name, DG), whichElm(arg2.key.name, DG), 'arg-of'))
	elif child.key == 'truth':
		lit, value = child.children
		lit = whichElm(lit.key.name, DG)
		if value.key in {'t', '1', 'true', 'yes', 'y'}:
			lit.truth = True
		else:
			lit.truth = False
	elif child.key == 'effect' or child.key == 'precond':
		label = child.key + '-of'
		arg1, arg2 = child.children
		if len(arg2.children) > 0:
			child_elm = litFromArg(arg2, DG)
		else:
			child_elm = whichElm(arg2.key.name, DG)
		DG.edges.add(Edge(whichElm(arg1.key.name, DG), child_elm, label))
	elif child.key == 'linked':
		arg1, arg2 = child.children
		dep = Literal(arg_name='link-condition' + str(uuid4())[19:23])
		Src = whichElm(arg1.key.name, DG)
		Snk = whichElm(arg2.key.name, DG)
		DG.CausalLinkGraph.addEdge(Src, Snk, dep)
		DG.edges.add(Edge(Snk, dep, 'precond-of'))
		DG.edges.add(Edge(Src, dep, 'effect-of'))
	elif child.key == '<':
		arg1, arg2 = child.children
		DG.OrderingGraph.addEdge(whichElm(arg1.key.name, DG), whichElm(arg2.key.name, DG))
	elif child.key == 'linked-by':
		src, snk, by = child.children
		try:
			dep = whichElm(by.key.name, DG)
		except:
			dep = litFromArg(by, DG)
		Src = whichElm(src.key.name, DG)
		Snk = whichElm(snk.key.name, DG)
		DG.CausalLinkGraph.addEdge(Src, Snk, dep)
		DG.edges.add(Edge(Snk, dep, 'precond-of'))
		DG.edges.add(Edge(Src, dep, 'effect-of'))
	elif child.key == 'consents':
		arg1, arg2, by = child.children
		DG.edges.add(Edge(whichElm(arg1.key.name, arg2.key.name, 'actor-of')))
	elif child.key == 'occurs':
		# then, first argument is step element name and second argument is an operator with children args
		stepFromArg(child, DG)
	elif child.key == 'is-state':
		litFromArg(child, DG)
	else:

		raise NameError('No definition implemented for decomp predicate {}'.format(child.key))


def stepFromArg(arg, DG):
	step_elm = whichElm(arg.children[0].key, DG)
	args = [whichElm(child.key.name, DG) for child in arg.children[0].children]
	for i, arg in enumerate(args):
		DG.edges.add(Edge(step_elm, arg, GC.ARGLABELS[i]))


def litFromArg(arg, DG):
	neg = True
	if arg.key == 'not':
		neg = False
		arg = arg.children[0]
	# arg 2 is written out
	lit_name = arg.key
	lit_elm = Literal(name=lit_name, arg_name=lit_name + str(uuid4())[19:23], num_args=len(arg.children), truth=neg)
	for i, ch in enumerate(arg.children):
		e_i = whichElm(ch.key.name, DG)
		DG.edges.add(Edge(lit_elm, e_i, GC.ARGLABELS[i]))
	return lit_elm


def whichElm(name, dg):
	return next(element for element in dg.elements if name == element.arg_name)


def getDecompGraph(formula, decomp_graph, params):
	for param in params:
		createElementByType(param, decomp_graph)

	if formula.key == 'and':
		for child in formula.children:
			decorateElm(child, decomp_graph)
	else:
		decorateElm(formula, decomp_graph)


def rPrintFormulaElements(formula):
	# BASE CASE
	if formula.type == 1 or formula.type == 2:
		print(formula.key.name, end=" ")
		return

	# INDUCTION
	if not formula.key == 'and':
		print('{}'.format(formula.key), end=" ")

	for child in formula.children:
		rPrintFormulaElements(child)

	print('\n')


def createElementByType(parameter, decomp):
	paramtypes = GC.object_types[next(iter(parameter.types))]

	if 'character' in parameter.types or 'actor' in parameter.types:
		elm = Actor(arg_name=parameter.name)
	elif 'arg' in paramtypes or 'item' in paramtypes or 'place' in paramtypes:
		arg_type = next(iter(parameter.types))
		elm = Argument(typ=arg_type, arg_name=parameter.name)
	elif 'step' in parameter.types:
		elm = Operator(arg_name=parameter.name)
	elif 'literal' in parameter.types or 'lit' in parameter.types:
		elm = Literal(arg_name=parameter.name)
	else:
		raise ValueError('parameter {} not story element'.format(parameter.name))

	decomp.elements.add(elm)
	return


def evalActionParams(params, op_graph):
	for i, parameter in enumerate(params):
		# parameters are list
		if 'character' in parameter.types or 'actor' in parameter.types:
			arg = Actor(arg_name=parameter.name)
			op_graph.elements.add(arg)
		# elif 'literal' in parameter.types or 'lit' in parameter.types:
		# 	lit = Literal(arg_name=parameter.name, typ='Condition')
		# 	op_graph.elements.add(lit)
		else:
			arg_type = next(iter(parameter.types))
			if arg_type in {'lit', 'literal'}:
				arg_type = 'Condition'
			arg = Argument(typ=arg_type, arg_name=parameter.name)
			op_graph.elements.add(arg)
		op_graph.edges.add(Edge(op_graph.root, arg, GC.ARGLABELS[i]))


""" Convert pddl file to set of operator graphs"""


@clock
def domainToOperatorGraphs(domain):
	opGraphs = set()
	dopGraphs = set()
	for action in domain.actions:
		op = Operator(name=action.name, num_args=len(action.parameters))
		op_graph = Action(name=action.name, root_element=op)
		evalActionParams(action.parameters, op_graph)

		if action.precond is not None:
			getFormulaGraph(action.precond.formula, op_graph, parent=op, relationship='precond-of',
							elements=op_graph.elements, edges=op_graph.edges)
		if action.effect is not None:
			getFormulaGraph(action.effect.formula, op_graph, parent=op, relationship='effect-of',
							elements=op_graph.elements,
							edges=op_graph.edges)
		if hasattr(action, 'decomp') and action.decomp is not None:
			decomp_graph = ElementGraph(name=action.name)
			getDecompGraph(action.decomp.formula, decomp_graph, action.parameters)
			op_graph.subplan = decomp_graph
			opelms = list(op_graph.elements)
			dpelms = list(decomp_graph.elements)
			for step_elm in opelms:
				for d_elm in dpelms:
					if not isinstance(d_elm, Argument):
						continue
					if d_elm.arg_name == step_elm.arg_name:
						op_graph.assign(step_elm, d_elm)
			dopGraphs.add(op_graph)
		else:
			opGraphs.add(op_graph)
	return opGraphs, dopGraphs


""" Convert pddl problem file to usable structures"""


@clock
def problemToGraphs(problem):
	"""
		Returns a dictionary:
		Keys: 'arg', 'init', 'goal'
		Values: arg dictionary, (elements, edges), (elements, edges)
	"""

	Args = {object.name: Argument(name=object.name, typ=object.typeName) for object in problem.objects if
			not object.typeName.lower() in {'character', 'actor'}}
	Args.update({object.name: Actor(name=object.name) for object in problem.objects if
				 object.typeName.lower() in {'character', 'actor'}})
	goal_elements, goal_edges = getGoalSet(problem.goal.formula, Args)
	goal_op = Operator(name='dummy_goal', stepnumber=1, num_args=0)
	goal_graph = Action(name='dummy_goal', root_element=goal_op)
	goal_graph.elements.update(goal_elements)
	goal_graph.edges.update(goal_edges)
	goal_graph.edges.update({Edge(goal_op, goal_lit, 'precond-of')
							 for goal_lit in goal_elements if type(goal_lit) is Literal})

	init_op = Operator(name='dummy_init', stepnumber=0, num_args=0)
	init_graph = Action(name='dummy_init', root_element=init_op)
	for condition in problem.init.predicates:
		lit = Literal(name=condition.name, num_args=len(condition.parameters), truth=True)
		init_graph.elements.add(lit)
		init_graph.edges.add(Edge(init_op, lit, 'effect-of'))
		for i, p in enumerate(condition.parameters):
			init_graph.edges.add(Edge(lit, Args[p], GC.ARGLABELS[i]))

	return Args, init_graph, goal_graph


import itertools


def addNegativeInitStates(predicates, initAction, objects):
	init_tups = defaultdict(set)
	effects = initAction.getNeighbors(initAction.root)
	for eff in effects:
		nontup = sorted([(edge.sink, GC.ARGLABELS.index(edge.label)) for edge in initAction.getIncidentEdges(eff)],
						key=lambda x: x[1])
		init_tups[eff.name].add(tuple(nontup[i][0] for i in range(len(nontup))))

	objs_by_type_dict = defaultdict(set)
	for obj in objects:
		objs_by_type_dict[obj.typ].add(obj)

	for p in predicates:

		param_object_pairs = [[obj for obj in objs_by_type_dict[param.types[0]]] for param in p.parameters if not
		p.parameters[0].types is None]
		param_tuples = {i for i in itertools.product(*param_object_pairs)}

		pred = Literal(name=p.name, arg_name='init_effect', num_args=len(
			p.parameters), truth=False)

		for pt in param_tuples:
			if pt in init_tups[p.name]:
				continue
			pc = copy.deepcopy(pred)
			pc.ID = uuid4()

			for i, arg in enumerate(pt):
				initAction.edges.add(Edge(pc, arg, GC.ARGLABELS[i]))

			if len(pt) > 0:
				initAction.elements.add(pc)
				initAction.edges.add(Edge(initAction.root, pc, 'effect-of'))


def domainAxiomsToGraphs(domain):
	if len(domain.axioms) > 0:
		from pddlToGraphs import ActionStmt
	for ax in domain.axioms:
		domain.actions.append(ActionStmt(name=ax.name, parameters=ax.vars_, precond=ax.context,
										 effect=ax.implies))


def parseDomAndProb(domain_file, problem_file):

	parser = Parser(domain_file, problem_file)
	domain, dom = parser.parse_domain_drw()
	problem, v = parser.parse_problem_drw(dom)


	GC.object_types.update(obTypesDict(domain.types))
	GC.prim_predtypes, GC.abs_predtypes = predTypesDict(list(dom.predicates.items()))
	#GC.predicate_types.update(predTypesDict(list(dom.predicates.items())))
	#GC.abs_predicate_types.update(predTypesDict(list(dom.predicates.items())))

	args, init, goal = problemToGraphs(problem)
	objects = set(args.values())

	addNegativeInitStates(domain.predicates.predicates, init, objects)

	domainAxiomsToGraphs(domain)
	Operators, DOperators = domainToOperatorGraphs(domain)

	addStatics(Operators)
	addStatics(DOperators)

	return Operators, DOperators, objects, GC.object_types, init, goal

def addStatics(operators):
	for op in operators:
		for eff in op.effects:
			FlawLib.non_static_preds.add((eff.name, eff.truth))

def obTypesDict(object_types):
	obtypes = defaultdict(set)
	for t in object_types:
		obtypes[t.name].add(t.parent)
		accumulated = set()
		rFollowHierarchy(object_types, t.parent, accumulated)
		obtypes[t.name].update(accumulated)
	return obtypes

def predTypesDict(pred_types):
	prim_predtypes = defaultdict(set)
	abs_predtypes = defaultdict(set)
	for name, predicate in pred_types:
		arg_types = {tup[0].name for _, tup in predicate.signature}
		if 'step' in arg_types or 'literal' in arg_types:
			abs_predtypes[name] = arg_types
		else:
			prim_predtypes[name] = arg_types
	return prim_predtypes, abs_predtypes

def rFollowHierarchy(object_types, child_name, accumulated=set()):
	for ob in object_types:
		if ob.name not in accumulated:
			if ob.name == child_name:
				accumulated.add(ob.parent)
				rFollowHierarchy(object_types, ob.parent, accumulated)


import sys

if __name__ == '__main__':
	num_args = len(sys.argv)
	if num_args > 1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		domain_file = 'domains/mini-indy-domain.pddl'
		problem_file = 'domains/mini-indy-problem.pddl'

	parser = Parser(domain_file, problem_file)
	domain, dom = parser.parse_domain_drw()
	problem, v = parser.parse_problem_drw(dom)
	op_graphs, dops = domainToOperatorGraphs(domain)
	for opgraph in op_graphs:
		opgraph.print_graph_names()
		print('\n')

	strucDict = problemToGraphs(problem)
	print('\nargs \n')
	Args = strucDict['args']
	for argElement in Args.values():
		print(argElement)
	print('\ninit\n')
	strucDict['init'].print_graph_names()
	print('\ngoal\n')
	strucDict['goal'].print_graph_names()
	print('\n')
