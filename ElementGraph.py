from Graph import *

class ElementGraph(Graph):
	"""An element graph is a graph with a root"""
	
	def __init__(self,id,type,name=None, Elements = set(), root_element = None, Edges = set(), Constraints = set()):
		super(ElementGraph,self).__init__(id,type,name,Elements,Edges,Constraints)
		self.root = root
	
	def getElementGraphFromElement(self, element):
		if self.root is element:
			return self
		
		return ElementGraph(element.id, type='element %s' %subgraph, name=self.name\
			self.rGetDescendants(element)\
			root=element\
			self.rGetDescendantEdges(element)\
			self.rGetDescendantConstraints(element))
			
	def rMerge(self, other, self_element = self.root, other_element = other.root, consistent_merges = {self}):
		incidentEdges = self.getIncidentEdges(self_element)
		otherEdges = other.getIncidentEdges(other_element)
		
		#Base Case
		if len(incidentEdges) == 0 and len(otherEdges) == 0:
			return consistent_merges
			
		#Induction
		consistent_edges = \
				{(edge,other) for edge in incidentEdges for other in otherEdges \
					if edge.isCoConsistent(other)\
				}
		
		#For each pair of consistent edges which are not equivalent (if they are equivalent, then ignore), 
			#edit the 'n' merge-graphs where both are separated edges, where 'n' is the number of consistent_merges
			#another 'n' merge-graph where both are merged into the first-arg,
		#Then, rMerge, but from self_element.sink and other_element.sink
		
		#Get the eelementgraph from the sink1, and the 
		for edge,other in consistent_sinks:	
			if not edge.isEqual(other):
				for consistent_merge in consistent_merges:
					consistent_merges = consistent_merge.rMerge(other,edge.sink, other.sink, consistent_merges)
					new_merge = copy.deepcopy(consistent_merge)
					edge.Merge(other)
					consistent_merges = new_merge.rMerge(other,edge.sink, other.sink, consistent_merges)
				element_graph_merge.add()
				merge = copy.deepcopy(edge).Merge(other)
				
				
				merge_graph = self.getElementGraphFromElement(sink_merge)
				sink1_graph = self.getElementGraphFromElement(sink1)
				sink2_graph = other.getElementGraphFromElement(sink2)
				
				merge_graph.rMerge(sink2_graph, consistent_merges)
				sink1_graph.rMerge(sink2_graph, consistent_merges)
	

def extractElementsubGraphFromElement(G, element, Type):
	Edges = G.rGetDescendantEdges(element)
	Elements = G.rGetDescendants(element)
	Constraints = G.rGetDescendantConstraints(element)
	return Type(element.id,type = element.type, name=element.name, Elements, Edges, Constraints)
	
def getElementGraphMerge(one,other):
	
	if not one.isCoConsistent(other):
		return set()
		
	
	possible_worlds = {element_graph for element_graph in {}}
		
	if one.root.name is None:
		if other.root.name is None:
			print('if this were a literal, needs a name')
		else:
			one.root.name = other.root.name	

	if type(one.root) == 'Literal':
		if one.root.num_args is None:
			if other.root.num_args is None:
				print('need to put num_args in literals')
				return None
			else:
				self.root.num_args = other.root.num_args
				
	if type(one.root) == 'Operator':
		preconditions = {edge for edge in }
		#For each pair of co-consistent preconditions (one.precondition, other.precondition), 
			#If they both have the same name,
				#Create new ElementGraphs EG1,EG2, where EG1 makes them the same precondition, and EG2 keeps them separated
		#Do same for each pair of effects.
			#Don't need to do this for consenting actor
	#Action, Condition, 
		""" BUT, then there will be a combinatorial explosion of different ElementGraphs for each permuation,
			especially more complex ElementGraphs.
			What if, for each element in an ElementGraph, we store a set of possible mergers?"""
				
				
		"""TODO: with literals, there are no edges with same label. With steps, there are. 
			With steps, consider the unnamed step which contains two same-named literals. (e.g. to preconditions (at x loc) and (at y loc))
			Where self has (at arg1 loc) and other has (at None loc). 
			Two options, combine the literals or let there be two preconditions in merged Condition.
			Ought we store a list of alternatives? Ought this method not be a class method?"""
