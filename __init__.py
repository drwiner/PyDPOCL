
import sys
import pickle
from PyDPOCL import GPlanner
import Ground_Compiler_Library.GElm

if __name__ == '__main__':
	num_args = len(sys.argv)
	if num_args >1:
		domain_file = sys.argv[1]
		if num_args > 2:
			problem_file = sys.argv[2]
	else:
		domain_file = 'domains/travel_domain.pddl'
		problem_file = 'domains/travel-to-la.pddl'


	RELOAD = 0
	if RELOAD:
		import Ground_Compiler_Library

	d_name = domain_file.split('/')[1].split('.')[0]
	p_name = problem_file.split('/')[1].split('.')[0]
	uploadable_ground_step_library_name = 'Ground_Compiler_Library//' + d_name + '.' + p_name
	ground_steps = pickle.load(open(uploadable_ground_step_library_name, 'rb'))
	planner = GPlanner(ground_steps)
	planner.solve(k=4)