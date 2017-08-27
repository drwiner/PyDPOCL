from Ground_Compiler_Library.GElm import GLiteral, GStep
from uuid import uuid4
from Flaws import FlawLib, OPF, TCLF
from Ground_Compiler_Library.OrderingGraph import OrderingGraph, CausalLinkGraph
import copy
from collections import namedtuple, defaultdict
import math
dummyTuple = namedtuple('dummyTuple', ['init', 'final'])
# class dummyTuple:
# 	def __init__(self, init, final):
# 		self.init = init
# 		self.final = final

class GPlan:

	def __init__(self, dummy_init_constructor, dummy_goal_constructor):
		self.ID = uuid4()
		self.OrderingGraph = OrderingGraph()
		self.CausalLinkGraph = CausalLinkGraph()
		# self.HierarchyGraph = HierarchyGraph()
		self.flaws = FlawLib()
		self.solved = False
		self.dummy = dummyTuple(dummy_init_constructor.instantiate(), dummy_goal_constructor.instantiate())

		self.init = self.dummy.init.preconds
		self.goal = self.dummy.final.preconds
		self.steps = [self.dummy.init, self.dummy.final]

		# check if any existing steps are choices (instances of cndts of open conditions)
		self.dummy.final.update_choices(self)

		self.cndt_map = None
		self.threat_map = None
		# self.gstep_lib = ground_step_list

		# self.h_step_dict = dict()

		self.heuristic = float('inf')
		self.name = ''
		self.cost = 0
		self.depth = 0

	def __len__(self):
		return len(self.steps)

	def __getitem__(self, pos):
		return self.steps[pos]

	def __setitem__(self, item, pos):
		self.steps[pos] = item

	def index(self, step):
		for i, s in enumerate(self.steps):
			if s.ID == step.ID:
				return i
		print('{} {} {}'.format(self.name, step, step.ID))
		for i, s in enumerate(self.steps):
			print('{} {} {}'.format(i, s, s.ID))
		raise ValueError('{} with ID={} not found in plan {}'.format(step, step.ID, self.name))

	def instantiate(self, add_to_name):
		new_self = copy.deepcopy(self)
		new_self.ID = uuid4()
		new_self.name += add_to_name
		# refresh attributes
		return new_self

	# @property
	# def cost(self):
	# 	return len(self.steps) - 2

	def isInternallyConsistent(self):
		return self.OrderingGraph.isInternallyConsistent() and self.CausalLinkGraph.isInternallyConsistent()

	# Insert Methods #

	def insert(self, step):
		# baseline condition:
		# self.cost += 1
		# self.cost += (2 * 2 + 1) - (step.height * step.height)
		if step.height > 0:
			self.insert_decomp(step)
		else:
			self.insert_primitive(step)


	def insert_primitive(self, new_step):
		self.steps.append(new_step)

		# global orderings
		self.OrderingGraph.addEdge(self.dummy.init, new_step)
		self.OrderingGraph.addEdge(new_step, self.dummy.final)

		# add open conditions for new step
		for pre in new_step.open_preconds:
			self.flaws.insert(self, OPF(new_step, pre))

		# check for causal link threats
		for edge in self.CausalLinkGraph.edges:
			# source, sink, condition = edge
			if edge.source.ID == new_step.ID:
				continue
			if edge.sink.ID == new_step.ID:
				continue
			if self.OrderingGraph.isPath(new_step, edge.source):
				continue
			if self.OrderingGraph.isPath(edge.sink, new_step):
				continue
			if new_step.stepnum in edge.sink.threat_map[edge.label.ID]:
				self.flaws.insert(self, TCLF(new_step, edge))

	def insert_decomp(self, new_step):
		# magic happens here
		swap_dict = dict()

		# sub dummy init
		d_i = new_step.dummy.init.instantiate()
		d_i.depth = new_step.depth
		swap_dict[new_step.dummy.init.ID] = d_i
		self.steps.append(d_i)
		# add flaws for each new_step precondition, but make s_need d_i and update cndt_map/ threat_map
		d_i.swap_setup(new_step.cndts, new_step.cndt_map, new_step.threats, new_step.threat_map)
		for pre in new_step.open_preconds:
			self.flaws.insert(self, OPF(d_i, pre, new_step.height))
		preconds = list(new_step.open_preconds)
		d_i.preconds = preconds
		d_i.open_preconds = preconds

		self.OrderingGraph.addEdge(self.dummy.init, d_i)
		self.OrderingGraph.addEdge(d_i, self.dummy.final)


		# sub dummy final
		d_f = new_step.dummy.final.instantiate(default_None_is_to_refresh_open_preconds=False)
		d_f.depth = new_step.depth
		swap_dict[new_step.dummy.final.ID] = d_f
		# d_f will be primitive, to allow any heighted applicable steps
		self.insert(d_f)

		# added this 2017-08-09
		self.OrderingGraph.addEdge(d_i, d_f)
		self.OrderingGraph.addEdge(d_f, self.dummy.final)
		self.OrderingGraph.addEdge(self.dummy.init, d_f)

		# decomposition links
		# self.HierarchyGraph.addOrdering(new_step, d_i)
		# self.HierarchyGraph.addOrdering(new_step, d_f)
		# for sb_step in new_step.sub_steps:
		# 	self.HierarchyGraph.addOrdering(new_step, sb_step)

		# log who your family is
		new_step.dummy = dummyTuple(d_i, d_f)
		d_i.sibling = d_f
		d_f.sibling = d_i

		# sub steps
		for substep in new_step.sub_steps:
			new_substep = substep.instantiate(default_None_is_to_refresh_open_preconds=False)
			swap_dict[substep.ID] = new_substep

			# INCREMENT DEPTH
			new_substep.depth = new_step.depth + 1
			if new_substep.depth > self.depth:
				self.depth = new_substep.depth

			self.insert(new_substep)

			# if your substeps have children, make those children fit between your init and
			if new_substep.height > 0:
				self.OrderingGraph.addEdge(new_substep.dummy.final, d_f)
				self.OrderingGraph.addEdge(d_i, new_substep.dummy.init)

		# sub orderings
		for edge in new_step.sub_orderings.edges:
			source, sink = swap_dict[edge.source.ID], swap_dict[edge.sink.ID]
			if source.height > 0:
				source = source.dummy.final
			if sink.height > 0:
				sink = sink.dummy.init
			self.OrderingGraph.addEdge(source, sink)

		# sub links
		for edge in new_step.sub_links.edges:
			# instantiating a GLiteral does not give it new ID (just returns deep copy)
			source, sink, label = swap_dict[edge.source.ID], swap_dict[edge.sink.ID], edge.label.instantiate()
			if source.height > 0:
				source = source.dummy.final
			if sink.height > 0:
				sink = sink.dummy.init

			clink = self.CausalLinkGraph.addEdge(source, sink, label)

			# check if this link is threatened
			for substep in new_step.sub_steps:
				new_substep = swap_dict[substep.ID]
				if new_substep.ID in {clink.source.ID, clink.sink.ID}:
					continue
				if new_substep.stepnum not in clink.sink.threat_map[clink.label.ID]:
					continue
				if new_substep.height > 0:
					# decomp step compared to its dummy init and dummy final steps
					if self.OrderingGraph.isPath(new_substep.dummy.final, clink.source):
						continue
					if self.OrderingGraph.isPath(clink.sink, new_substep.dummy.init):
						continue
					self.flaws.insert(self, TCLF(new_substep.dummy.final, clink))
				else:
					# primitive step gets the primitive treatment
					if self.OrderingGraph.isPath(new_substep, clink.source):
						continue
					if self.OrderingGraph.isPath(clink.sink, new_substep):
							continue
					self.flaws.insert(self, TCLF(new_substep, clink))

	# Resolve Methods #

	def resolve(self, new_step, s_need, p):
		if new_step.height > 0:
			self.resolve_with_decomp(new_step, s_need, p)
		else:
			self.resolve_with_primitive(new_step, s_need, p)

	def resolve_with_primitive(self, new_step, mutable_s_need, mutable_p):

		# operate on cloned plan
		mutable_s_need.fulfill(mutable_p)

		# add orderings
		self.OrderingGraph.addEdge(new_step, mutable_s_need)
		# add causal link
		c_link = self.CausalLinkGraph.addEdge(new_step, mutable_s_need, mutable_p)

		mutable_s_need.update_choices(self)

		# check if this link is threatened
		ignore_these = {mutable_s_need.ID, new_step.ID}
		# ignore_these = {mutable_s_need.stepnum, new_step.stepnum}
		for step in self.steps:
			if step.ID in ignore_these:
				continue
			if step.stepnum not in mutable_s_need.threat_map[mutable_p.ID]:
				continue
			if self.OrderingGraph.isPath(mutable_s_need, step):
				continue
			# only for reuse case, otherwise this check is superfluous
			if self.OrderingGraph.isPath(step, new_step):
				continue
			self.flaws.insert(self, TCLF(step, c_link))

		# # check if adding this step threatens other causal links
		# for cl in self.CausalLinkGraph.edges:
		# 	if cl == c_link:
		# 		continue
		# 	if new_step.stepnum not in cl.sink.threat_map[cl.label.ID]:
		# 		continue
		# 	if self.OrderingGraph.isPath(new_step, cl.source):
		# 		continue
		# 	if self.OrderingGraph.isPath(cl.sink, new_step):
		# 		continue
		# 	self.flaws.insert(self, TCLF(new_step, cl))

	def resolve_with_decomp(self, new_step, mutable_s_need, mutable_p):
		d_i, d_f = new_step.dummy

		# operate on cloned plan
		# mutable_s_need = self[s_index]
		# mutable_p = mutable_s_need.preconds[p_index]
		mutable_s_need.fulfill(mutable_p)

		# add ordering
		self.OrderingGraph.addEdge(d_f, mutable_s_need)

		# add causal link
		c_link = self.CausalLinkGraph.addEdge(d_f, mutable_s_need, mutable_p)

		mutable_s_need.update_choices(self)

		# check if df -> s_need is threatened
		ignore_these = {mutable_s_need.ID, d_f.ID, d_i.ID}
		for step in self.steps:
			# reminder: existing steps are primitive

			if step.ID in ignore_these:
				continue

			### NOT SUFFICIENT: needs to not be a threat to any sub-step added... ###
			if step.stepnum not in mutable_s_need.threat_map[mutable_p.ID]:
				continue
			# check only for d_f, in case this step occurs between d_i and d_f
			if self.OrderingGraph.isPath(step, d_f):
				continue
			if self.OrderingGraph.isPath(mutable_s_need, step):
				continue
			self.flaws.insert(self, TCLF(step, c_link))

		# # check if adding this step threatens other causal links
		# for cl in self.CausalLinkGraph.edges:
		# 	# all causal links are between primitive steps
		# 	if cl == c_link:
		# 		continue
		# 	if new_step.stepnum not in cl.sink.threat_map[cl.label.ID]:
		# 		continue
		# 	if self.OrderingGraph.isPath(d_f, cl.source):
		# 		continue
		# 	if self.OrderingGraph.isPath(cl.sink, d_f):  # LOOK HERE TODO: DECIDE
		# 		continue
		# 	self.flaws.insert(self, TCLF(d_f, cl))

	def __lt__(self, other):
		# if self.cost / (1 + math.log2(self.depth+1)) + self.heuristic != other.cost / (1 + math.log2(other.depth+1)) + other.heuristic:
		# 	return self.cost / (1 + math.log2(self.depth+1)) + self.heuristic < other.cost / (1 + math.log2(other.depth+1)) + other.heuristic
		# if self.cost - math.log2(self.depth+1) + self.heuristic != other.cost - math.log2(other.depth+1) + other.heuristic:
		# 	return self.cost - math.log2(self.depth+1) + self.heuristic < other.cost - math.log2(other.depth+1) + other.heuristic
		# if self.cost - self.depth + self.heuristic != other.cost - other.depth + other.heuristic:
		# 	return self.cost - self.depth + self.heuristic < other.cost - other.depth + other.heuristic
		if self.cost + self.heuristic != other.cost + other.heuristic:
			return (self.cost + self.heuristic) < (other.cost + other.heuristic)
		elif self.cost != other.cost:
			return self.cost < other.cost
		elif self.heuristic != other.heuristic:
			return self.heuristic < other.heuristic
		elif len(self.flaws) != len(other.flaws):
			return len(self.flaws) < len(other.flaws)
		elif len(self.CausalLinkGraph.edges) != len(other.CausalLinkGraph.edges):
			return len(self.CausalLinkGraph.edges) > len(other.CausalLinkGraph.edges)
		elif len(self.OrderingGraph.edges) != len(other.OrderingGraph.edges):
			return len(self.OrderingGraph.edges) > len(other.OrderingGraph.edges)
		elif sum([step.stepnum for step in self]) != sum([step.stepnum for step in other]):
			return sum([step.stepnum for step in self]) < sum([step.stepnum for step in other])
		else:
			return self.OrderingGraph < other.OrderingGraph

	def __str__(self):
		return self.name
		# return 'GPlan{} c={} h={}\t'.format(self.ID[-4:], self.cost, self.heuristic) + \
		# 		str(self.steps) + '\n' + str(self.OrderingGraph) + '\n' + str(self.CausalLinkGraph)

	def __repr__(self):
		return self.__str__()


def topoSort(ordering_graph):
	L =[]
	# ogr = copy.deepcopy(ordering_graph)
	ogr = OrderingGraph()
	init_dummy = GStep(name='init_dummy')
	ogr.elements.add(init_dummy)
	for elm in list(ordering_graph.elements):
		ogr.addOrdering(init_dummy, elm)
	S = {init_dummy}

	#L = list(graph.Steps)
	while len(S) > 0:
		n = S.pop()
		if n not in L:
			L.append(n)
		for m_edge in ogr.getIncidentEdges(n):
			ogr.edges.remove(m_edge)
			#if the sink has no other ordering sources, add it to the visited
			if len({edge for edge in ogr.getParents(m_edge.sink)}) == 0:
				S.add(m_edge.sink)
	return L

if __name__ == '__main__':
	pass