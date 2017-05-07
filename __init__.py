
import sys
import pickle
from PyDPOCL import GPlanner
import Ground_Compiler_Library

if __name__ == '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		domain_file = 'Ground_Compiler_Library//domains/travel_domain.pddl'
		problem_file = 'Ground_Compiler_Library//domains/travel-to-la.pddl'
	d_name = domain_file.split('/')[-1].split('.')[0]
	p_name = problem_file.split('/')[-1].split('.')[0]
	uploadable_ground_step_library_name = 'Ground_Compiler_Library//' + d_name + '.' + p_name


	RELOAD = 0
	if RELOAD:
		GL = Ground_Compiler_Library.Ground.GLib(domain_file, problem_file)
		with open('ground_steps.txt', 'w') as gs:
			for step in GL:
				gs.write(str(step))
				gs.write('\n')
		ground_step_list = Ground_Compiler_Library.deelementize_ground_library(GL)
		with open('ground_steps.txt', 'a') as gs:
			gs.write('\n\n')
			for step in ground_step_list:
				gs.write(str(step))
				gs.write('\n')
		Ground_Compiler_Library.Ground.upload(ground_step_list, uploadable_ground_step_library_name)

	ground_steps = pickle.load(open(uploadable_ground_step_library_name, 'rb'))
	planner = GPlanner(ground_steps)
	planner.solve(k=1)