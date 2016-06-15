from pddl.parser import Parser
from math import floor
import random
import uuid
from PlanElementGraph import *

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
	
def rGetFormulaElements(formula, current_element = None, collected = None):
	if collected == None:
		collected = set()
	if current_element == None:
		current_element = []
		
	#BASE CASE
	if formula.type == 1 or formula.type == 2:
		print('prim: {}'.format(formula.key.name), end= " ")
		current_element.append(formula.key.name)
		#print(formula.key)
		return current_element
	
	#INDUCTION
	if not formula.key == 'and':
		print('non-primitive: {}'.format(formula.key), end= " ")
		current_element.append(formula.key)
	if formula.key == 'not':
		formula = next(iter(formula.children))
		print('name: {}'.format(formula.key), end= " ")
		current_element.append(formula.key)
		
	# if formula.key == 'not':
		# current_element.append(formula.key)
	# if formula.key == 'intends':
		# current_element.append(formula.key)
	
	#for child in formula.children:
	current_element.append(child.key.name for child in formula.children)
		#current_element = rGetFormulaElements(child,current_element, collected)
		
	if len(current_element) > 0:
		collected.add(tuple(current_element))
		current_element = None
		print('\n')
	return collected
	
		
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
	opGraphs = {}
	for action in domain.actions:
		op_graph =			Action(	id = uuid.uuid1(start_id),\
							type_graph = 'Action', \
							name = action.name)
		start_id += 1
		op_id = uuid.uuid1(start_id)
		op = Operator(id = uuid.uuid1(op_id), type = 'Action', name = action.name, num_args = len(action.parameters), instantiated = True)
		start_id += 1
		#args = {}
		for i, parameter in enumerate(action.parameters):
			if 'character' in parameter.types:
				op_graph.elements.add(Actor(id = uuid.uuid1(start_id), type = 'actor', name = parameter.name, arg_pos_dict={op_id : i}))
			else:
				arg_type = parameter.types.pop()
				op_graph.elements.add(Argument(id = uuid.uuid1(start_id), 	type=arg_type, name=parameter.name, arg_pos_dict=	{op_id :  i}))
			start_id += 1
		
		#if not action.agents is None:
			#rGetFormulaElements(action.agents.formula)
	
#domain_file = 'domain.pddl'
#problem = parse('domain.pddl','task02.pddl')
domain_file = 'ark-domain_syntactic_sugar.pddl'
#domain_file = 'domain_elevators.pddl'	
#domain_file = 'ark-domain.pddl'

print('\n')	
domain = parseDomain(domain_file)
print(type(domain))
print(domain.name)
print('\ndomain action effect types:\n')
for action in domain.actions:
	#print(type(action))
	print('\t\t\t[[[[[{}]]]]]'.format(action.name))
	
	print('\n parameters \n')
	for p in action.parameters:
		print(p.name, end=" -")
		for t in p.types:
			print(t, end = " ")
	print('\n')
	
	print('\n ------- preconditions -------\n')
	#collected = 
	rGetFormulaElements(action.precond.formula)
	#print('test\n')
	#print(len(collected))
	
	print('\n \t+++++++ effects +++++++\n')
	rPrintFormulaElements(action.effect.formula)
	
	print('\n &&&&&&& prerequisite &&&&&&&\n')
	if not action.prereq is None:
		rPrintFormulaElements(action.prereq.formula)
		
	print('\n ^^^^^^^ agents ^^^^^^^\n')
	if not action.agents is None:
		rPrintFormulaElements(action.agents.formula)
	
	
	#print(action.parameters)
	print('\n\n\n')
		
