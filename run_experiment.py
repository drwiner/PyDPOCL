
from PyDPOCL import *

if __name__ == '__main__':

	# domain_file = 'Ground_Compiler_Library//domains/travel_domain_primitive_only.pddl'
	domain_file = 'Ground_Compiler_Library//domains/travel_domain.pddl'

	# Problem files
	# 1] 1 agent, 1 car, 1 airplane, 2 locations
	problem_file_1 = 'Ground_Compiler_Library//domains/travel-to-la.pddl'
	# 2] 2 agents, 1 car, 1 airplane, 2 locations, 1 goal
	problem_file_2 = 'Ground_Compiler_Library//domains/travel-2.pddl'
	# 3] 2 agents, 1 car, 1 airplane, 2 locations, 2 goals
	problem_file_3 = 'Ground_Compiler_Library//domains/travel-3.pddl'
	# 4] 2 agents, 1 car, 1 airplane, 2 locations, 2 goals
	problem_file_4 = 'Ground_Compiler_Library//domains/travel-4.pddl'
	# 5] 2 agents, 1 car, 1 airplane, 3 locations, 1 goal
	problem_file_5 = 'Ground_Compiler_Library//domains/travel-5.pddl'
	# 6] 2 agents, 1 car, 1 airplane, 3 locations, 2 goals
	problem_file_6 = 'Ground_Compiler_Library//domains/travel-6.pddl'
	# 7] 1 agent, 2 cars, 2 airplanes, 2 locations, 1 goal
	problem_file_7 = 'Ground_Compiler_Library//domains/travel-7.pddl'
	# 8] 4 agents, 1 car, 1 airplane, 4 locations, 2 goals
	problem_file_8 = 'Ground_Compiler_Library//domains/travel-8.pddl'

	# problems = [problem_file_1, problem_file_2, problem_file_3, problem_file_4,
	#             problem_file_5, problem_file_6, problem_file_7, problem_file_8]
	problems = [problem_file_1]

	d_name = domain_file.split('/')[-1].split('.')[0]

	# for each problem, solve in 1 of 4 ways... but need way to run in different ways

	for prob in problems:
		p_name = prob.split('/')[-1].split('.')[0]
		uploadable_ground_step_library_name = 'Ground_Compiler_Library//' + d_name + '.' + p_name

		RELOAD = 0
		if RELOAD:
			print('reloading')
			ground_steps = just_compile(domain_file, prob, uploadable_ground_step_library_name)

		ground_steps = []
		i = 0
		while True:
			try:
				print(i)
				with open(uploadable_ground_step_library_name + str(i), 'rb') as ugly:
					ground_steps.append(pickle.load(ugly))
				i += 1
			except:
				break
		print('finished uploading')

		print(p_name)

		planner = GPlanner(ground_steps)
		planner.solve(k=8)