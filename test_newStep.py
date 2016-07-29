
	
from pddlToGraphs import *
from Planner import *
domain_file = 'domains/mini-indy-domain.pddl'
problem_file = 'domains/mini-indy-problem.pddl'

parser = Parser(domain_file, problem_file)
domain, dom = parser.parse_domain_drw()
problem, v = parser.parse_problem_drw(dom)
op_graphs = domainToOperatorGraphs(domain)


operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
graph = planner[0]
flaw = graph.flaws[0]

''' test
results = planner.newStep(graph, flaw)
'''



s_need, precondition = flaw.flaw
Precondition = graph.getElementGraphFromElementId(precondition.id, Condition)
results = set()
		
op_iter = iter(operators)
op = next(op_iter) # repeat until 'move'
Effs = {eff for eff in op.getNeighborsByLabel(op.root, 'effect-of')}
Effects = {op.getElementGraphFromElementId(eff.id, Condition) for eff in Effs}
eff_iter = iter(Effects)
eff = next(eff_iter)

list(eff.edges)[0].source.truth


Available = copy.deepcopy(eff.edges)
Remaining = copy.deepcopy(Precondition.edges)

AbsolvingEffects = {Eff for Eff in Effects if Eff.canAbsolve(Precondition)}

	if Effect.canAbsolve(Precondition):
		step_op, nei = op.makeCopyFromID(start_from = 1,old_element_id = eff.id)
		
		Effect  = step_op.getElementGraphFromElementId(nei, Condition)
		Effect_absorbtions = Effect.getInstantiations(Precondition)


		for eff_abs in Effect_absorptions: 
			graph_copy = copy.deepcopy(graph)
			graph_copy.mergeGraph(eff_abs) 
			
			new_step_op = copy.deepcopy(step_op)
			graph_copy.mergeGraph(new_step_op)
			planner.addStep(graph_copy, new_step_op.root.id, s_need.id, eff_abs.id) 
			results.add(graph_copy)