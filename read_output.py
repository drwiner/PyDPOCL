import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import math
if __name__ == '__main__':

	file_names = ['po', 'd_add', 'd_add_c_minus_d', 'd_add_subtrct_depth', 'd_add_div_depth',
				'd_insrt', 'd_insrt_c_minus_d', 'd_insrt_subtrct_depth', 'd_insrt_div_depth']#, 'd_addHt', 'd_addht_rrp']

	active = 0
	begin = 0
	
	data_dict = {}
	headings = ['time', 'expanded', 'visited', 'terminated', 'depth', 'cost', 'trace']
	
	problem_num = 0
	problem_dict = {}
	for file_name in file_names:
		with open(file_name + '.txt', 'r') as fp:
			for line in fp:
				
				split_line = line.split()
				
				if split_line[0] == 'time':
					begin = 1
					active = 1
					continue
				elif split_line[0] == 'finished':
					active = 0
					continue
					

				
				if begin:
					begin = 0
					problem_num += 1
					problem_dict[problem_num] = []

				if active:
					problem_dict[problem_num].append(split_line)

		data_dict[file_name] = problem_dict
		problem_dict = {}
		problem_num = 0
		active = 0
		begin = 0

	# prepare data for matplotlib

	print('stop here')

	avg_per_c_per_problem = {}

	plt.figure(figsize=(8,4))
	ax = plt.gca()
	colormap = plt.get_cmap('jet')
	ax.set_color_cycle([colormap(k) for k in np.linspace(0, 1, 9)])

	G = GridSpec(4, 2)
	subplots = []

	# for each experimental condition
	for i in range(1, 9):
		for condition_name, data in data_dict.items():
		# for each planning problem

			num_rows = len(data[i])
			if num_rows > 1:
				rt = [float(row[0]) for row in data[i] if row[0] != 'timedout:']
				expnd = [int(row[1]) for row in data[i] if row[0] != 'timedout:']
				dep = [int(row[4]) for row in data[i] if row[0] != 'timedout:']
				cost = [int(row[5]) for row in data[i] if row[0] != 'timedout:']
				trace = [int(row[6]) for row in data[i] if row[0] != 'timedout:']
				cost_div_depth = [int(row[5]) / (1 + math.log2(int(row[4])+1)) for row in data[i] if row[0]!= 'timedout:']
				avg_per_c_per_problem[(condition_name, i)] = \
					(num_rows, rt[0], rt[-1], expnd[0], expnd[-1], sum(dep)/num_rows, sum(cost)/num_rows, sum(trace)/num_rows)

				print('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
					condition_name, i,
					num_rows, rt[0], rt[-1],
					expnd[0], expnd[-1], sum(dep) / num_rows, sum(cost) / num_rows, sum(trace)/num_rows, max(dep)))
				# plt.subplot(4, 2, i)
				# plt.plot(rt, expnd, 'x', label=condition_name)
				if i > 4:
					R = i-5
					axes_1 = plt.subplot(G[R, 1])
				else:
					axes_1 = plt.subplot(G[i-1,0])

				if i == 1:
					plt.legend()

				axes_1.set_title(i)
				s = axes_1.plot(rt, trace, 'x', label=condition_name)
				# subplots.append(s)

				# ax = fig.add_subplot(gs[i,0])

			else:
				# if i > 4:
				# 	R = i-5
				# 	axes_1 = plt.subplot(G[R, 1])
				# else:
				# 	axes_1 = plt.subplot(G[i-1,0])
				# #
				# #
				# axes_1.set_title(i)
				# s = axes_1.plot(0, 0, 'x', label=condition_name)
				# # # subplots.append(s)

				print('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(condition_name, i,
				                       0, 'TO', 'TO', 'NA', 'NA', 'NA',
				                        'NA', 'NA', 'NA'))
		# plt.title(i)
	plt.tight_layout()
	# plt.axes()
	# plt.legend(tuple(subplots))
	# plt.legend(['a','b','c','d','e','f','g','h','i'], loc='lower center')
	plt.xlabel('Runtime')
	plt.ylabel("Nodes Expanded")

	plt.show()



	"""
	i = 1
	for each key in data_dict (condition)
		for i'th planning problem
			extract data columns (RT, expanded, cost, depth, trace)

	"""
