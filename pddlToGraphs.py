from pddl.parser import Parser
from math import floor
import random
import uuid
import collections
from Planner.Flaws import *

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
	
	
	for i, child in enumerate(formula.children):
		#children are list
		arg = next(element for element in elements if child.key.name == element.name)
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
	
def getGoalSet(goal_formula, objects):
	""" Returns set of goal literals """
	goal_elements = set()
	goal_edges = set()
	if goal_formula.key == 'and':
		for child in goal_formula.children:
			if child.key == 'not':
				child = next(iter(child.children))
				if child.key == 'intends':
					pass
				else:
					goal_elements.add(Literal(id = uuid.uuid1(12), type = 'Condition',  name = child.key, num_args = len(child.children), truth = False))
			elif child.key == 'intends':
				pass
			elif child.type >0:
				pass
			else:
				goal_elements.add(Literal(id = uuid.uuid1(13), type = 'Condition',  name = child.key, num_args = len(child.children), truth = True))
				
		for i, grandchild in enumerate(child.children):
			#children are list
			arg = next(ob_element for ob_name, ob_element in objects.items() if grandchild.key.name == ob_name)
			if relationship == 'actor-of':
				goal_edges.add(Edge(child, arg, 'actor-of'))
			elif lit.name == '=':
				goal_edges.add(Edge(lit, arg, 'arg-of'))
			else:
				goal_edges.add(Edge(lit, arg, ARGLABELS[i]))
			
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
		for i, parameter in enumerate(action.parameters):
			#parameters are list
			if 'character' in parameter.types:
				op_graph.elements.add(Actor(id = uuid.uuid1(start_id), type = 'actor', name = parameter.name, arg_pos_dict={op_id : i}))
			else:
				arg_type = parameter.types.pop()
				op_graph.elements.add(Argument(id = uuid.uuid1(start_id), 	type=arg_type, name=parameter.name, arg_pos_dict=	{op_id :  i}))
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
	Args = {object.name: Argument(id = uuid.uuid1(1), name = object.name, type = object.typeName) for object in problem.objects}
	#Initial state
	#for condition in problem_initial_state:
	init_elements = set()
	init_edges = set()
	for condition in problem.init.predicates:
		condition_id = uuid.uuid1(2)
		lit = Literal(id = condition_id, type = 'Condition', name = condition.name, num_args = len(condition.parameters))
		init_elements.add(lit)
		for p in condition.parameters:
			init_edges.add(Edge(lit, Args[p],'effect-of'))
	goal_tuple = getGoalSet(problem.goal.formula, Args)
	return {'args': Args, 'init': (init_elements, init_edges), 'goal':goal_tuple}
	
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
	
	struc = problemToGraphs(problem)
	
	
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