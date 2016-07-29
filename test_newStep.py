
	
from pddlToGraphs import *
from Planner import *
domain_file = 'domains/mini-indy-domain.pddl'
problem_file = 'domains/mini-indy-problem.pddl'

# parser = Parser(domain_file, problem_file)
# domain, dom = parser.parse_domain_drw()
# problem, v = parser.parse_problem_drw(dom)
# op_graphs = domainToOperatorGraphs(domain)


operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
graph = planner[0]
flaw = graph.flaws[0]

''' test
results = planner.newStep(graph, flaw)
'''



