
	
from pddlToGraphs import *
from Planner import *
domain_file = 'domains/mini-indy-domain.pddl'
problem_file = 'domains/mini-indy-problem.pddl'



operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
graph = planner[0]
result = planner.rPOCL(graph)

flaw = graph.flaws.pop()


results = planner.newStep(graph, flaw)
graph = results.pop()
flaw = graph.flaws.pop()
results = planner.newStep(graph,flaw)
graph = results.pop()
detectThreatenedCausalLinks(graph)

planner.newStep(graph, flaw)

results.update(planner.newStep(graph, flaw))




graph = results.pop()
copy.deepcopy(graph.edges)
flaw = graph.flaws.pop()

OG = graph.OrderingGraph
s_need, pre = flaw.flaw
s_need == graph.final_dummy_step

results.update(planner.reuse(graph,flaw))

print(graph.OrderingGraph)