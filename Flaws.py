from pddlToGraphs import *
import collections
""" 
	Flaws for element graphs
"""

class Flaw:
	def __init__(self, tuple, name):
		self.name = name
		self.flaw = tuple
		
	def __hash__(self):
		return hash((self.name, self.flaw))
		
	def __eq__(self, other):
		return hash(self) == hash(other)
		
	def __repr__(self):
		return '{}, {}'.format(self.name, self.flaw)
		
class FlawLibrary(collections.deque):
	def __init__(self):
		self._flaws = []
	
	def __getitem__(self, position):
		return self._flaws[position]
		
	def __len__(self):
		return len(self._flaws)
	
	def __setitem__(self, flaw, position):
		self._flaws[position] = flaw



"""
An open precondition flaw is a tuple <step element, precondition element>
	where precondition element is a literal element, 
	there is a precondition edge from the step element to the precondition element,
	and there is no causal link in the graph from another step to the precondition element with label 'effect'
	It's important to consider this last point 
		because with this approach, you could instantiate an element which already has some preconditions in causal links
		
		********Consider above for resolve "uninstantiated step flaw"
"""
