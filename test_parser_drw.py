from pddl.parser import Parser

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
		
	print(formula.key)
	for child in formula.children:
		rGetFormulaElements(child)
		
	
domain_file = 'domain.pddl'
problem = parse('domain.pddl','task02.pddl')
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
		# self.name = name
		# self.signature = signature
		# self.precondition = precondition
		# self.effect = effect
		
print('\ndomain predicates:\n')
for p in problem.domain.predicates:
	print(p)
print('\ndomain types:\n')
for t in problem.domain.types:
	print(t)

print('\n')	
domain = parseDomain(domain_file)
print(type(domain))
print(domain.name)
print('\ndomain action effect types:\n')
for action in domain.actions:
	#print(type(action))
	print('\n effects \n')
	rGetFormulaElements(action.effect.formula)
	print('\n preconditions \n')
	rGetFormulaElements(action.precond.formula)
		

		
