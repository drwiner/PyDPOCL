from pddl.parser import Parser
from math import floor
import random
import uuid
import collections
from PlanElementGraph import *
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
		lit = Literal(id = uuid.uuid1(current_id), type = 'Condition',  name = formula.key, num_args = num_children, truth = False)
	else:
		num_children = len(formula.children)
		lit = Literal(id = uuid.uuid1(current_id), type = 'Condition',  name = formula.key, num_args = num_children, truth = True)
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
	m = Motivation(id = uuid.uuid1(current_id), truth = bit, intender = character, goal=lit)
	elements.update(m,lit)
	edges.update(Edge(m,lit,'goal-of'),Edge(m,CE,'intender-of'),Edge(parent,m,relationship))
	current_id+=1
	return lit, formula
	
def makeLit(formula, current_id, parent, relationship, elements, edges, bit = None):
	if bit == None:
		bit=  True
	num_children = len(formula.children)
	lit = Literal(id = uuid.uuid1(current_id), type = 'Condition',  name = formula.key, num_args = num_children, truth = bit)
	current_id += 1
	elements.add(lit)
	edges.add(Edge(parent,lit,relationship))
	return lit, formula

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
		else:
			lit, formula = makeLit(formula, current_id, parent, relationship, elements, edges, False)
	elif formula.key == 'intends':
		lit, formula = makeMotive(formula, current_id, parent, relationship, elements, edges, True)
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
		elif lit.name == '=':
			edges.add(Edge(lit, arg, 'arg-of'))
		else:
			edges.add(Edge(lit, arg, ARGLABELS[i]))
			
	return elements, edges
	
""" Get a precondition, effect, or set of prerequisites from pddl operator to element graph"""
def getFormulaGraph(formula, current_id = None, parent = None, relationship = None, elements = None, edges = None):
	if current_id == None:
		current_id = 1
	if parent == None:
		parent = Element(id = uuid.uuid1(current_id), type = None)
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
			lit = Literal(id = uuid.uuid1(12), type = 'Condition',  name = formula.key, num_args = len(formula.children), truth = False)
			elements.add(lit)
	elif formula.key == 'intends':
		pass
	elif formula.type >0:
		pass
	else:
		lit = Literal(id = uuid.uuid1(13), type = 'Condition',  name = formula.key, num_args = len(formula.children), truth = True)
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
		
""" Convert pddl file to set of operator graphs"""
def domainToOperatorGraphs(domain):
	start_id = floor(random.random()*100)
	opGraphs = set()
	for action in domain.actions:
		start_id += 1
		op_id = uuid.uuid1(start_id)
		#Element types correspond to their type of graph
		op = Operator(id = op_id, type = 'Action', name = action.name, num_args = len(action.parameters), instantiated = True)
		
		op_graph =			Action(	id = uuid.uuid1(start_id),\
							type_graph = 'Action', \
							name = action.name,\
							root_element = op)
		
		
		start_id += 1
		#args = {}
		'''First, create elements for all action parameters (variables)'''
		for i, parameter in enumerate(action.parameters):
			#parameters are list
			if 'character' in parameter.types:
				op_graph.elements.add(Actor(id = uuid.uuid1(start_id), type = 'character', arg_name = parameter.name, arg_pos_dict={op_id : i}))
			elif 'actor' in parameter.types:
				op_graph.elements.add(Actor(id = uuid.uuid1(start_id), type = 'actor', arg_name = parameter.name, arg_pos_dict={op_id : i}))
			else:
				arg_type = next(iter(parameter.types))
				op_graph.elements.add(Argument(id = uuid.uuid1(start_id), 	type=arg_type, arg_name=parameter.name, arg_pos_dict=	{op_id :  i}))
			start_id += 1
		
		getFormulaGraph(action.precond.formula, start_id, parent = op, relationship = 'precond-of',elements= op_graph.elements, edges=op_graph.edges)
		getFormulaGraph(action.effect.formula, start_id, parent = op, relationship = 'effect-of', elements = op_graph.elements,edges= op_graph.edges)
		##getFormulaGraph(action.agents.formula, start_id, parent = op, relationship = 'actor-of', elements = op_graph.elements,edges= op_graph.edges)
		opGraphs.add(op_graph)
	return opGraphs
	
""" Convert pddl problem file to usable structures"""
def problemToGraphs(problem):
	"""
		Returns a dictionary:
		Keys: 'arg', 'init', 'goal'
		Values: arg dictionary, (elements, edges), (elements, edges)
	"""
	Args = {object.name: Argument(id = uuid.uuid1(1), name = object.name, type = object.typeName) for object in problem.objects if not object.typeName.lower() in {'character', 'actor'}}
	Args.update({object.name: Actor(id = uuid.uuid1(1), name = object.name, type = object.typeName) for object in problem.objects if object.typeName.lower() in {'character', 'actor'}})

	#Initial state
	#for condition in problem_initial_state:
	init_elements = set()
	init_edges = set()
	init_op = Operator(id = uuid.uuid1(4), type = 'Action', name = 'dummy_init', num_args = 0, instantiated = True)
	init_graph =			Action(	id = uuid.uuid1(5),\
							type_graph = 'Action', \
							name = 'dummy_init',\
							root_element = init_op)
	for condition in problem.init.predicates:
		condition_id = uuid.uuid1(2)
		lit = Literal(id = condition_id, type = 'Condition', name = condition.name, num_args = len(condition.parameters), truth = True)
		init_graph.elements.add(lit)
		init_graph.edges.add(Edge(init_op, lit, 'effect-of'))
		for i,p in enumerate(condition.parameters):
			init_graph.edges.add(Edge(lit, Args[p],ARGLABELS[i]))
	
	goal_elements, goal_edges = getGoalSet(problem.goal.formula, Args)
	goal_op = Operator(id = uuid.uuid1(4), type = 'Action', name = 'dummy_goal', num_args = 0, instantiated = True)
	goal_graph =			Action(	id = uuid.uuid1(5),\
							type_graph = 'Action', \
							name = 'dummy_goal',\
							root_element = goal_op)
	goal_graph.elements.update(goal_elements)
	goal_graph.edges.update(goal_edges)
	goal_graph.edges.update({Edge(goal_op, goal_lit, 'precond-of') for goal_lit in goal_elements})
	
	return (Args, init_graph, goal_graph)
	
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
	op_graphs = domainToOperatorGraphs(domain)
	args, init, goal = problemToGraphs(problem)
	return (op_graphs, set(args.values()), init, goal)
	
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