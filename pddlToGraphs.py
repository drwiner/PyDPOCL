from pddl.parser import Parser
from math import floor
import random
import uuid
import collections
from PlanElementGraph import *

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
	return lit , formula

def getSubFormulaGraph(formula, current_id = None, parent = None, relationship = None, elements = None, edges = None):
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
	
def getFormulaGraph(formula, current_id = None, parent = None, relationship = None, elements = None, edges = None):

	if parent == None:
		parent = Element(id = uuid.uuid1(current_id), type = None)
		current_id += 1
	if edges == None:
		edges = set()
	if elements == None:
		elements = []
	if current_id == None:
		current_id = 1
		
	if formula.key == 'and':
		for child in formula.children:
			getSubFormulaGraph(child, current_id, parent, relationship, elements, edges)
	else:
		getSubFormulaGraph(formula, current_id, parent, relationship, elements, edges)
		
	return elements, edges
	
		
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
		
def domainToOperatorGraphs(domain_file):
	domain = parseDomain(domain_file)
	start_id = floor(random.random()*100)
	opGraphs = set()
	for action in domain.actions:
		start_id += 1
		op_id = uuid.uuid1(start_id)
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
		
		
	
#domain_file = 'domain.pddl'
#problem = parse('domain.pddl','task02.pddl')
domain_file = 'ark-domain_syntactic_sugar.pddl'
#domain_file = 'domain_elevators.pddl'	
#domain_file = 'ark-domain.pddl'

print('\n')	
# domain = parseDomain(domain_file)
# print(type(domain))
# print(domain.name)
# print('\ndomain action effect types:\n')

# for action in domain.actions:
	# #print(type(action))
	# print('\t\t\t[[[[[{}]]]]]'.format(action.name))
	
	# print('\n parameters \n')
	# for p in action.parameters:
		# print(p.name, end=" -")
		# for t in p.types:
			# print(t, end = " ")
	# print('\n')
	
	# print('\n ------- preconditions -------\n')
	# #collected = 
	# rPrintFormulaElements(action.precond.formula)
	# #print('test\n')
	# #print(len(collected))
	
	# print('\n \t+++++++ effects +++++++\n')
	# rPrintFormulaElements(action.effect.formula)
	
	# print('\n &&&&&&& prerequisite &&&&&&&\n')
	# if not action.prereq is None:
		# rPrintFormulaElements(action.prereq.formula)
		
	# print('\n ^^^^^^^ agents ^^^^^^^\n')
	# if not action.agents is None:
		# rPrintFormulaElements(action.agents.formula)
	
	
	# #print(action.parameters)
	# print('\n\n\n')
		
opGraphs = domainToOperatorGraphs(domain_file)
print(len(opGraphs))
for opgraph in opGraphs:
	opgraph.print_graph_names()
	print('\n')