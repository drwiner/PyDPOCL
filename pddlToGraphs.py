from pddl.parser import Parser
#from Flaws import *

from math import floor
import collections
from PlanElementGraph import *
from clockdeco import clock


#from Flaws import *

ARGLABELS = ['first-arg', 'sec-arg','third-arg', 'fourth-arg', 'fifth-arg']
	

def parseDomain(domain_file):
	parser = Parser(domain_file)
	domain = parser.parse_domain_drw()
	return domain


def parse(domain_file, problem_file):
	# Parsing
	parser = Parser(domain_file, problem_file)
	domain = parser.parse_domain()
	problem = parser.parse_problem(domain)

	return problem
	
def makeGoal(formula, current_id):
	if formula.key == 'not':
		formula = next(iter(formula.children))
		num_children = len(formula.children)
		lit = Literal(ID = uuid.uuid1(current_id), typ = 'Condition', name = formula.key, num_args = num_children, truth = False)
	else:
		num_children = len(formula.children)
		lit = Literal(ID = uuid.uuid1(current_id), typ = 'Condition', name = formula.key, num_args = num_children, truth = True)
	return lit
	
def makeMotive(formula, current_id, parent, relationship, elements, edges, bit = None):
	if bit ==None:
		bit = True
	character = next(iter(formula.children))
	CE = next(element for element in elements if element.name == character.key.name)
	formula = next(iter(formula.children))
	""" make goal"""
	lit = makeGoal(formula, current_id)
	current_id += 1
	m = Motivation(ID = uuid.uuid1(current_id), truth = bit, intender = character, goal=lit)
	elements.update(m,lit)
	edges.update(Edge(m,lit,'goal-of'),Edge(m,CE,'intender-of'),Edge(parent,m,relationship))
	current_id+=1
	return lit, formula
	
def makeLit(formula, current_id, parent, relationship, elements, edges, bit = None, noAdd = None):

	if bit == None:
		bit=  True
	if noAdd == None:
		noAdd = False
	num_children = len(formula.children)
	lit = Literal(ID = uuid.uuid1(current_id), typ = 'Condition',  name = formula.key, num_args = num_children, truth = bit)
	#current_id += 1
	if not noAdd:
		elements.add(lit)
		edges.add(Edge(parent,lit,relationship))
	return lit, formula

def forallFormula(formula, parent, relationship, elements, edges):
	'''
		(forall ?c (not (at ?c ?l)))
		first find out what ?c is . then get all args and create precondition for each
	'''
	global args
	arg_elements = {v for v in args.values()}
	scoped_var = formula.children[0]
	typ = next(iter(elm.typ for elm in elements if elm.arg_name == scoped_var.key.name))

	#scoped_args = objects from planning problem which share a typ with scoped_var
	scoped_args = {arg for arg in arg_elements if arg.typ ==typ}
	lit = formula.children[1]

	negative = False
	num_args = 0
	if lit.key == 'not':
		Lit, formula = makeLit(next(iter(lit.children)),7,parent = parent,relationship= relationship,
							elements =elements,edges = edges,bit= False, noAdd = True)
	else:
		Lit, formula = makeLit(lit,7,parent = parent,relationship= relationship, elements =elements,edges = edges,
							bit= True, noAdd = True)

	for arg in scoped_args:
		L = copy.deepcopy(Lit)
		L.ID = uuid.uuid1(26)
		elements.add(L)
		edges.add(Edge(parent, L, relationship))
		for i, child in enumerate(formula.children):
			if child.key.name == scoped_var.key.name:
				elements.add(arg)
				edges.add(Edge(L, arg, ARGLABELS[i]))  # figure out which arg
			else:
				non_scoped = next(element for element in elements if child.key.name == element.arg_name)
				edges.add(Edge(L,non_scoped,ARGLABELS[i]))

def getNonEquals(formula, elements, edges):
	global op_graph
	#ARGLABELS
	(c1, c2) = formula.children
	arg1 = next(element for element in elements if c1.key.name == element.arg_name)
	arg2 = next(element for element in elements if c2.key.name == element.arg_name)
	edge1 = next(edge for edge in edges if edge.source.typ == 'Action' and edge.sink == arg1)
	edge2 = next(edge for edge in edges if edge.source.typ == 'Action' and edge.sink == arg2)
	i1 = ARGLABELS.index(edge1.label)
	i2 = ARGLABELS.index(edge2.label)
	op_graph.nonequals.add((i1,i2))

def getSubFormulaGraph(formula, current_id = None, parent = None, relationship = None, elements = None, edges = None):
	if elements ==None:
		elements = set()
	if edges == None:
		edges = set()
	
	'''make new literal representing subformula'''
	if formula.key == 'not':
		formula = next(iter(formula.children))
		if formula.key == 'intends':
			lit, formula = makeMotive(formula, current_id, parent, relationship, elements, edges, False)
		elif formula.key == 'equals' or formula.key == '=' or formula.key == 'equal':
			getNonEquals(formula, elements, edges)
			return elements, edges
		else:
			lit, formula = makeLit(formula, current_id, parent, relationship, elements, edges, False)
	elif formula.key == 'intends':
		lit, formula = makeMotive(formula, current_id, parent, relationship, elements, edges, True)
	elif formula.key == 'for-all' or formula.key == 'forall':
		#formula = next(iter(formula.children))
		forallFormula(formula, parent, relationship, elements, edges)
		return elements, edges
	elif formula.type >0:
		pass
	else:
		lit, formula = makeLit(formula, current_id, parent, relationship, elements, edges, True)
	
	'''for each variable, find existing argument in action parameters and add Edge'''
	for i, child in enumerate(formula.children):
		#children are list
		#print(child.key.name)
		arg = next(element for element in elements if child.key.name == element.arg_name)
		
		if relationship == 'actor-of':
			edges.add(Edge(parent, arg, 'actor-of'))

		#elif lit.name == '=' or lit.name == 'equals' or lit.name == 'equal':
			# TODO: test if ever receiving 'equals'
			#edges.add(Edge(lit, arg, 'arg-of'))
		else:
			edges.add(Edge(lit, arg, ARGLABELS[i]))
			
	return elements, edges
	
""" Get a precondition, effect, or set of prerequisites from pddl operator to element graph"""

def getFormulaGraph(formula, current_id = None, parent = None, relationship = None, elements = None, edges = None):
	if current_id == None:
		current_id = 1
	if parent == None:
		parent = Element(ID = uuid.uuid1(current_id), typ = None)
		current_id += 1
	if edges == None:
		edges = set()
	if elements == None:
		elements = set() #why is this list?
	
		
	if formula.key == 'and':
		for child in formula.children:
			getSubFormulaGraph(child, current_id, parent, relationship, elements, edges)
	else:
		getSubFormulaGraph(formula, current_id, parent, relationship, elements, edges)
		
	return elements, edges
	
def getSubFormulaNoParent(formula, objects):
	lit = None
	elements = set()
	edges = set()
	if formula.key == 'not':
		formula = next(iter(formula.children))
		if formula.key == 'intends':
			pass
		else:
			lit = Literal(ID = uuid.uuid1(12), typ = 'Condition',  name = formula.key, num_args = len(formula.children), truth = False)
			elements.add(lit)
	elif formula.key == 'intends':
		pass
	elif formula.type >0:
		pass
	else:
		lit = Literal(ID = uuid.uuid1(13), typ = 'Condition',  name = formula.key, num_args = len(formula.children), truth = True)
		elements.add(lit)
	for i, child in enumerate(formula.children):
		#children are list
		arg = next(ob_element for ob_name, ob_element in objects.items() if child.key == ob_name)
		edges.add(Edge(lit, arg, ARGLABELS[i]))
	return (elements, edges)
	
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
				
	return (goal_elements, goal_edges)

def decorateElm(child, DG):
	if child.key == 'name':
		elm = whichElm(child.children[0].key.name, DG)
		elm.name = child.children[1].key
	elif child.key == 'nth-step-arg' or child.key == 'nth-lit-arg':
		args = child.children
		label = ARGLABELS[int(args[0].key)]
		parent_elm = whichElm(args[1].key.name,DG)
		child_elm = whichElm(args[2].key.name, DG)
		DG.edges.add(Edge(parent_elm, child_elm, label))
	elif child.key == 'includes':
		arg1, arg2 = child.children
		DG.edges.add(Edge(whichElm(arg1.key.name,DG),whichElm(arg2.key.name,DG),'arg-of'))
	elif child.key == 'effect' or child.key == 'precond':
		label = child.key + '-of'
		arg1, arg2 = child.children
		if len(arg2.children) > 0:
			child_elm = litFromArg(arg2,DG)
		else:
			child_elm = whichElm(arg2.key.name,DG)
		DG.edges.add(Edge(whichElm(arg1.key.name,DG), child_elm, label))
	elif child.key == 'linked':
		arg1, arg2 = child.children
		DG.CausalLinkGraph.addEdge(whichElm(arg1.key.name, DG), whichElm(arg2.key.name, DG), Literal(ID = -20,
																									 typ='Condition',
																									 truth=True))
	elif child.key == '<':
		arg1, arg2 = child.children
		DG.OrderingGraph.addEdge(whichElm(arg1.key.name, DG), whichElm(arg2.key.name, DG))
	elif child.key == 'linked-by':
		arg1, arg2, by = child.children
		try:
			dep = whichElm(by.key.name, DG)
		except:
			dep = litFromArg(arg2,DG)
		DG.CausalLinkGraph.addEdge(whichElm(arg1.key.name, DG), whichElm(arg2.key.name, DG), dep)
	elif child.key == 'consents':
		arg1, arg2, by = child.children
		DG.edges.add(Edge(whichElm(arg1.key.name, arg2.key.name, 'actor-of')))
	elif child.key == 'occurs':
		#then, first argument is step element name and second argument is an operator with children args
		stepFromArg(child,DG)
	elif child.key == 'is-state':
		litFromArg(child,DG)
	else:

		raise NameError('No definition implemented for decomp predicate {}'.format(child.key))

def stepFromArg(arg, DG):
	step_elm = whichElm(arg.children[0].key, DG)
	args = [whichElm(child.key.name, DG) for child in arg.children[0].children]
	for i,arg in enumerate(args):
		DG.edges.add(Edge(step_elm,arg,ARGLABELS[i]))

def litFromArg(arg,DG):
	neg = True
	if arg.key == 'not':
		neg = False
		arg = arg.children[0]
	# arg 2 is written out
	lit_name = arg.key
	lit_elm = Literal(ID=uuid.uuid1(256), typ = 'Condition', name=lit_name, num_args=len(arg.children), truth=neg)
	for i, ch in enumerate(arg.children):
		e_i = whichElm(ch.key.name, DG)
		DG.edges.add(Edge(lit_elm, e_i, ARGLABELS[i]))
	return lit_elm

def whichElm(name, dg):
	return next(element for element in dg.elements if name == element.arg_name)


def getDecomp(formula, decomp_graph):
	if formula.key == 'not':
		pass
		print('not doing this yet')
		R = Restriction()
		decomp_graph.Restrictions.add(R)
		return


	for child in formula.children:
		if len(child.children) > 0:
			#elm = whichElm(child.key.name,decomp_graph)
			decorateElm(child,decomp_graph)

def getDecompGraph(formula, decomp_graph, params):

	for i,param in enumerate(params):
		createElementByType(i,param,decomp_graph)

	if formula.key == 'and':
		for child in formula.children:
			decorateElm(child, decomp_graph)
			#getDecomp(child, decomp_graph)
	else:
		decorateElm(formula, decomp_graph)
		#getDecomp(formula, decomp_graph)
		
def rPrintFormulaElements(formula):
		
	#BASE CASE
	if formula.type == 1 or formula.type == 2:
		print(formula.key.name, end= " ")
		return
	
	#INDUCTION
	if not formula.key == 'and':
		print('{}'.format(formula.key), end= " ")
	
	for child in formula.children:
		rPrintFormulaElements(child)


	print('\n')

def createElementByType(i, parameter, decomp):
	if 'character' in parameter.types or 'actor' in parameter.types:
		elm = Actor(ID=uuid.uuid1(i), typ='character', arg_name=parameter.name)
	elif 'arg' in parameter.types:
		arg_type = next(iter(parameter.types))
		elm = Argument(ID=uuid.uuid1(i), typ=arg_type, arg_name=parameter.name)
	elif 'step' in parameter.types:
		elm = Operator(ID=uuid.uuid1(i), typ='Action', arg_name = parameter.name)
	elif 'literal' in parameter.types or 'lit' in parameter.types:
		elm = Literal(ID = uuid.uuid1(i), typ='Condition', arg_name = parameter.name)
	else:
		raise ValueError('parameter {} not story element'.format(parameter.name))

	decomp.elements.add(elm)
	return



""" Convert pddl file to set of operator graphs"""
@clock
def domainToOperatorGraphs(domain):
	start_id = 15
	opGraphs = set()
	for action in domain.actions:
		start_id += 1
		op_id = uuid.uuid1(start_id)
		#Element types correspond to their type of graph
		op = Operator(ID = op_id, typ = 'Action', name = action.name, num_args = len(action.parameters))
		
		op_graph =			Action(	ID = uuid.uuid1(start_id),\
							type_graph = 'Action', \
							name = action.name,\
							root_element = op)
		global op_graph
		start_id += 1
		#args = {}
		'''First, create elements for all action parameters (variables)'''
		for i, parameter in enumerate(action.parameters):
			#parameters are list
			if 'character' in parameter.types or 'actor' in parameter.types:
				arg = Actor(ID=uuid.uuid1(start_id), typ='character', arg_name=parameter.name)
				op_graph.elements.add(arg)#, #arg_pos_dict={op_id : i}))

			# elif 'actor' in parameter.types:
			# 	op_graph.elements.add(Actor(ID = uuid.uuid1(start_id), typ = 'actor', arg_name = parameter.name))#, arg_pos_dict={op_id : i}))
			else:
				arg_type = next(iter(parameter.types))
				arg = Argument(ID = uuid.uuid1(start_id), 	typ=arg_type, arg_name=parameter.name)
				op_graph.elements.add(arg)#, arg_pos_dict=	{op_id :  i}))
			op_graph.edges.add(Edge(op_graph.root, arg, ARGLABELS[i]))
			start_id += 1

		if not action.precond is None:
			getFormulaGraph(action.precond.formula, start_id, parent = op, relationship = 'precond-of',elements= op_graph.elements, edges=op_graph.edges)
		getFormulaGraph(action.effect.formula, start_id, parent = op, relationship = 'effect-of', elements = op_graph.elements,edges= op_graph.edges)
		if hasattr(action, 'decomp') and not action.decomp is None:
			decomp_graph = PlanElementGraph(ID = uuid.uuid1(1), name=action.name, type_graph = 'decomp')
			getDecompGraph(action.decomp.formula, decomp_graph, action.parameters)
			op_graph.subgraphs.add(decomp_graph)
		##getFormulaGraph(action.agents.formula, start_id, parent = op, relationship = 'actor-of', elements = op_graph.elements,edges= op_graph.edges)
		opGraphs.add(op_graph)
	return opGraphs
	
""" Convert pddl problem file to usable structures"""
@clock
def problemToGraphs(problem):
	"""
		Returns a dictionary:
		Keys: 'arg', 'init', 'goal'
		Values: arg dictionary, (elements, edges), (elements, edges)
	"""
	Args = {object.name: Argument(ID = uuid.uuid1(1), name = object.name, typ = object.typeName) for object in problem.objects if not object.typeName.lower() in {'character', 'actor'}}
	Args.update({object.name: Actor(ID = uuid.uuid1(1), name = object.name, typ = object.typeName) for object in problem.objects if object.typeName.lower() in {'character', 'actor'}})

	#Initial state
	#for condition in problem_initial_state:
	init_elements = set()
	init_edges = set()
	init_op = Operator(ID = uuid.uuid1(114), typ = 'Action', name = 'dummy_init', stepnumber= 0, num_args = 0)
	init_graph =			Action(	ID = uuid.uuid1(115),
							type_graph = 'Action',
							name = 'dummy_init',
							root_element = init_op)
	for condition in problem.init.predicates:
		condition_id = uuid.uuid1(20)
		lit = Literal(ID = condition_id, typ = 'Condition', name = condition.name, num_args = len(condition.parameters), truth = True)
		init_graph.elements.add(lit)
		init_graph.edges.add(Edge(init_op, lit, 'effect-of'))
		for i,p in enumerate(condition.parameters):
			init_graph.edges.add(Edge(lit, Args[p],ARGLABELS[i]))
	
	goal_elements, goal_edges = getGoalSet(problem.goal.formula, Args)
	goal_op = Operator(ID = uuid.uuid1(114), typ = 'Action', name = 'dummy_goal', stepnumber= 1, num_args = 0)
	goal_graph =			Action(	ID = uuid.uuid1(115),
							type_graph = 'Action',
							name = 'dummy_goal',
							root_element = goal_op)
	goal_graph.elements.update(goal_elements)
	goal_graph.edges.update(goal_edges)
	goal_graph.edges.update({Edge(goal_op, goal_lit, 'precond-of') for goal_lit in goal_elements})
	
	return (Args, init_graph, goal_graph)


import itertools
def addNegativeInitStates(predicates, initAction, objects):
	init_tups = defaultdict(set)
	effects = initAction.getNeighbors(initAction.root)
	#[sorted([(edge.sink, ARGLABELS.index(edge.label)) for edge in initAction.getIncidentEdges(eff)],
		 #  key=lambda x: x[1]) for eff in effects]
	for eff in effects:
		nontup = sorted([(edge.sink, ARGLABELS.index(edge.label)) for edge in initAction.getIncidentEdges(eff)],
					key = lambda x: x[1])
		init_tups[eff.name].add(tuple(nontup[i][0] for i in range(len(nontup))))
	#init_tuples = [[arg for arg in initAction.getNeighbors(eff)) for eff in initAction.getNeighbors(
		#initAction.root)))]

	objs_by_type_dict = defaultdict(set)
	for obj in objects:
		objs_by_type_dict[obj.typ].add(obj)


	for p in predicates:

		param_object_pairs = [[obj for obj in objs_by_type_dict[param.types[0]]] for param in p.parameters if not
		p.parameters[0].types is None]
		param_tuples = {i for i in itertools.product(*param_object_pairs)}

		pred = Literal(ID=uuid.uuid1(2), typ='Condition', name=p.name, arg_name='init_effect', num_args=len(
			p.parameters), truth=False)

		for pt in param_tuples:
			if pt in init_tups[p.name]:
				continue
			pc = copy.deepcopy(pred)
			pc.ID = uuid.uuid1(3)

			#TODO compare each effect Condition to every existing effect condition - if equivalent, then cannot add
			# elements/edges to initAction. Better yet, create tuples for each existing effect condition and subtract
			#  from param_tuples before getting here

			for i, arg in enumerate(pt):
				initAction.edges.add(Edge(pc, arg, ARGLABELS[i]))

			if len(pt) > 0:
				initAction.elements.add(pc)
				initAction.edges.add(Edge(initAction.root, pc, 'effect-of'))

def domainAxiomsToGraphs(domain):
	if len(domain.axioms) > 0:
		from pddlToGraphs import ActionStmt
	for ax in domain.axioms:
		domain.actions.append(ActionStmt(name = ax.name, parameters = ax.vars_, precond = ax.context,
										 effect = ax.implies))

@clock
def parseDomainAndProblemToGraphs(domain_file, problem_file):
	""" Returns tuple 
			1) Operator Graphs
			2) Object Elements
			3) Init dummy Action
			4) Goal dummy Action
	"""
	parser = Parser(domain_file, problem_file)
	domain, dom = parser.parse_domain_drw()
	problem, v = parser.parse_problem_drw(dom)
	global args
	args, init, goal = problemToGraphs(problem)
	objects = set(args.values())

	addNegativeInitStates(domain.predicates.predicates, init, objects)

	#parse Domain after parsing problem - so that for-all/exists statements can create edges for each legal typed object
	# treats axioms as actions, TODO: consider if this affects heuristics drastically enough to change.
	domainAxiomsToGraphs(domain)

	op_graphs = domainToOperatorGraphs(domain)

	return (op_graphs, objects, domain.types, init, goal)
	
import sys	
if __name__ ==  '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]		
	else:
		domain_file = 'domains/mini-indy-domain.pddl'
		problem_file = 'domains/mini-indy-problem.pddl'
	
	parser = Parser(domain_file, problem_file)
	domain, dom = parser.parse_domain_drw()
	problem, v = parser.parse_problem_drw(dom)
	op_graphs = domainToOperatorGraphs(domain)
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

	
#domain_file = 'domain.pddl'
#problem = parse('domain.pddl','task02.pddl')
#domain_file = 'ark-domain_syntactic_sugar.pddl'
	#domain_file = 'domains/mini-indy-domain.pddl'
	#problem_file = 'domains/mini-indy-problem.pddl'
#domain_file = 'domain_elevators.pddl'	
#domain_file = 'ark-domain.pddl'

	print('\n')	
# domain = parseDomain(domain_file)
# print(type(domain))
# print(domain.name)
# print('\ndomain action effect types:\n')




#parser = Parser(domain_file, problem_file)
#domain = parser.parse_domain()
#problem = parser.parse_problem(domain)



#opGraphs = domainToOperatorGraphs(domain_file)
#print(len(opGraphs))
#for opgraph in opGraphs:
#	opgraph.print_graph_names()
#	print('\n')

#domain_file = '
#problem_file = 'domains/mini-indy-problem.pddl'
#problem = parse(domain_file, problem_file)