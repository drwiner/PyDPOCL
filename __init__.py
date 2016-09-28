import sys
from pddlToGraphs import parseDomainAndProblemToGraphs
from Planner import preprocessDomain
from Flaws import FlawLib
from Planner import obTypesDict
from Element import Argument
from Planner import PlanSpacePlanner
from Planner import topoSort
from PlanElementGraph import Action


if __name__ ==  '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		#domain_file = 'domains/mini-indy-domain.pddl'
		#problem_file = 'domains/mini-indy-problem.pddl'
		domain_file = 'domains/ark-domain.pddl'
		problem_file = 'domains/ark-problem.pddl'

	#f = open('workfile', 'w')
	operators, objects, object_types, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
	#non_static_preds = preprocessDomain(operators)
	FlawLib.non_static_preds = preprocessDomain(operators)
	obtypes = obTypesDict(object_types)

	Argument.object_types = obtypes
	planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
	#planner.GL = GLib(operators, objects, obtypes, initAction, goalAction)

	results = planner.POCL(1)

	for result in results:
		totOrdering = topoSort(result)
		print('\n\n\n')
		for step in topoSort(result):
			print(Action.subgraph(result, step))
		#print(result)