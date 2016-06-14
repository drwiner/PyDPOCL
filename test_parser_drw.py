from pddl.parser import Parser
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
		print(formula.key.name)
		return 
		
	print(formula.key, end= " ")
	for child in formula.children:
		rGetFormulaElements(child)
		
	
domain_file = 'domain.pddl'
#problem = parse('domain.pddl','task02.pddl')
""" Problem attributes"""
		# self.name = name
		# self.domain = domain
		# self.objects = objects
		# self.initial_state = init
		# self.goal = goal
		
""" Domain attributes"""
		# self.name = name
		# self.types = types
		# self.predicates = predicates
		# self.actions = actions
		# self.constants = constants
		
""" Predicate attributes"""
		# self.name = name
		# self.signature = signature
		
""" Action attributes"""
		#self._visitorName = 'visit_action_stmt'
		# self.name = name
		# self.parameters = parameters  # a list of parameters
		# self.precond = precond
		# self.effect  = effect
		


print('\n')	
domain = parseDomain(domain_file)
print(type(domain))
print(domain.name)
print('\ndomain action effect types:\n')
for action in domain.actions:
	#print(type(action))
	print('[[[[[{}]]]]]'.format(action.name))
	
	print('\n ------- preconditions \n')
	rGetFormulaElements(action.precond.formula)
	
	print('\n +++++++ effects \n')
	rGetFormulaElements(action.effect.formula)
	
	print('\n &&&&&&& prerequisite \n')
	rGetFormulaElements(action.prereq.formula)
	
	print('\n\n parameters \n')
	for p in action.parameters:
		print(p.name, end=" ")
	#print(action.parameters)
	print('\n\n\n')
		
