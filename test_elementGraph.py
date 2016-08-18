from unittest import TestCase
from PlanElementGraph import Condition
from ElementGraph import ElementGraph
from Element import Literal
import copy
import uuid

class TestElementGraph(TestCase):
	def test_makeElementGraph(self):
		root = Literal(ID = uuid.uuid1(1), typ='Condition', name='JoeRoot', arg_name= 'first', truth=True)
		roo2 = copy.deepcopy(root)
		eg = Condition(id = uuid.uuid1(1), type_graph='Condition', name = 'Joe',  root_element=root, Elements= {
			root})
		JoeSubgraph = eg.subgraph(eg.root)
		Joe2 = eg.subgraph(roo2)
		assert(JoeSubgraph == Joe2)



