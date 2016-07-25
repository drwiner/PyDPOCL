from pddl.parser import Parser
from math import floor
import random
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
	
def rGetFormulaElements(formula):
	#BASE CASE
	if formula.type == 1 or formula.type == 2:
		print(formula.key.name, end= " ")
		return 
	
	#INDUCTION
	if not formula.key == 'and':
		print(formula.key, end= " ")
	
	for child in formula.children:
		rGetFormulaElements(child)
	print('\n')
	
def domainToOperatorGraphs(domain_file):
	domain = parseDomain(domain_file)
	start_id = floor(random.random()*10000)
	for action in domain.actions:
		op = Operator(id = start_id, type = 'Action', name = action.name, num_args = len(action.parameters), instantiated = True)
		
	
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
	
	print(' parameters ')
	for p in action.parameters:
		print(p.name, end=" ")
	print('')
	
	print(' ------- preconditions -------')
	rGetFormulaElements(action.precond.formula)
	
	print(' \t+++++++ effects +++++++')
	rGetFormulaElements(action.effect.formula)
	
	print(' &&&&&&& prerequisite &&&&&&&')
	if not action.prereq is None:
		rGetFormulaElements(action.prereq.formula)
		
	print(' ^^^^^^^ agents ^^^^^^^')
	if not action.agents is None:
		rGetFormulaElements(action.agents.formula)
	
	
	#print(action.parameters)
	print('\n\n\n')
		
