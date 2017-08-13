import sys

from Ground_Compiler_Library.Ground import GLib, upload
from Ground_Compiler_Library.GElm import GLiteral, GStep



def deelementize_ground_library(GL):
	g_steps = []
	for step in GL._gsteps[0:-2]:
		preconds = [GLiteral(p.name, p.Args, p.truth, p.replaced_ID, (p.name, p.truth) not in GL.non_static_preds) for p in step.Preconditions]
		gstep = GStep(step.name, step.Args, preconds, step.stepnumber, step.height)
		gstep.setup(GL.ante_dict, GL.id_dict, GL.threat_dict, GL.flaw_threat_dict)

		# all primitive steps (except for dummies) are in _gsteps before all decomp steps, where each level is totally ordered
		if gstep.height > 0:
			gstep.swap_substeps(g_steps, step, len(GL._gsteps))
		# TODO: for each decompositional step, need to swap out sub-steps with gsteps as well (based on same step nums, OG, CLG, recursively)
		g_steps.append(gstep)

	init_preconds = [GLiteral(p.name, p.Args, p.truth, p.replaced_ID, (p.name, p.truth) not in GL.non_static_preds) for p in
	                 GL[-2].Effects]
	dummy_init = GStep(GL[-2].name, GL[-2].Args, init_preconds, GL[-2].stepnumber, GL[-2].height)
	dummy_init.instantiable = False

	goal_preconds = [GLiteral(p.name, p.Args, p.truth, p.replaced_ID, (p.name, p.truth) not in GL.non_static_preds) for p in
	                 GL[-1].Preconditions]
	dummy_goal = GStep(GL[-1].name, GL[-1].Args, goal_preconds, GL[-1].stepnumber, GL[-1].height)
	dummy_goal.setup(GL.ante_dict, GL.id_dict, GL.threat_dict, GL.flaw_threat_dict)
	dummy_goal.instantiable = False

	g_steps.append(dummy_init)
	g_steps.append(dummy_goal)

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
	with open('ground_steps.txt', 'w') as gs:
		for step in GL:
			gs.write(str(step))
			gs.write('\n')
	ground_step_list = deelementize_ground_library(GL)
	with open('ground_steps.txt', 'a') as gs:
		gs.write('\n\n')
		for step in ground_step_list:
			gs.write(str(step))
			gs.write('\n')
	upload(ground_step_list, GL.name)