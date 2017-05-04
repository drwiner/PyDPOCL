import sys
from Planner import PlanSpacePlanner
from Planner import topoSort
from PlanElementGraph import Action
from Ground import GLib, upload
from GElm import GLiteral, GStep



def deelementize_ground_library(GL):
	g_steps = []
	for step in GL._gsteps:
		preconds = [GLiteral(p.name, p.Args, p.truth, p.replaced_ID, p not in GL.non_static_preds) for p in step.Preconditions]
		gstep = GStep(step.name, step.Args, preconds, step.stepnumber, step.height)
		gstep.setup(GL.ante_dict, GL.id_dict, GL.threat_dict)
		g_steps.append(gstep)
	return g_steps

if __name__ == '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		domain_file = 'domains/travel_domain.pddl'
		problem_file = 'domains/travel-to-la.pddl'

	GL = GLib(domain_file, problem_file)
	ground_step_list = deelementize_ground_library(GL)
	upload(ground_step_list, GL.name)


	# planner = PlanSpacePlanner(GL)
	#
	# results = planner.POCL(1)
	#
	# for result in results:
	# 	totOrdering = topoSort(result)
	# 	print('\n\n\n')
	# 	for step in topoSort(result):
	# 		print(Action.subgraph(result, step))
	# 	#print(result)