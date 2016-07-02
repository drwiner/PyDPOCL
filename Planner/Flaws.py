from OrderingGraph import *

""" 
	Flaws for element graphs
"""

class Flaw:
	def __init__(self, tuple, name):
		self.name = name
		self.flaw = tuple

def detectThreatenedCausalLinks(graph):
	"""
	A threatened causal link flaw is a tuple <causal link edge, threatening step element>
		where if s --p--> t is a causal link edge and s_threat is the threatening step element,
			then there is no ordering path from t to s_threat,
			no ordering path from s_threat to s,
			there is an effect edge from s_threat to a literal false-p',
			and p' is consistent with p after flipping the truth attribute
	"""
	
	detectedThreatenedCausalLinks = set()
	for causal_link in graph.CausalLinks:
		dependency = causal_link.condition
		reverse_dependency = copy.deepcopy(dependency)
		#Reverse the truth status of the dependency
		if reverse_dependency.truth == True:
			reverse_dependency.truth = False
		else:
			reverse_dependency.truth = True
			
		for step in graph.Steps:
			#First, ignore steps which either are the source and sink of causal link, or which cannot be ordered between them
			if step.id == causal_link.source.id || step.id == causal_link.sink.id:
				break
			if graph.orderingGraph.isPath(causal_link.sink, step):
				break
			if graph.orderingGraph.isPath(step, causal_link.source):
				break
			
			#Is condition consistent?
			effects = graph.getNeighborsByLabel(step, 'effect-of')	
			problem_effects = {eff for eff in effects if eff.isConsistent(reverse_dependency)}
			detectedThreatenedCausalLinks.update({Flaw((step,pe),'tclf') for pe in problem_effects})

	return detectedThreatenedCausalLinks
	

def addOpenPreconditionFlaws(graph, step):
	"""
	An open precondition flaw is a tuple <step element, precondition element>
		where precondition element is a literal element, 
		there is a precondition edge from the step element to the precondition element,
		and there is no causal link in the graph from another step to the precondition element with label 'effect'
		It's important to consider this last point 
			because with this approach, you could instantiate an element which already has some preconditions in causal links
	"""
	new_flaws = set()
	preconditions = graph.getNeighborsByLabel(step, 'precond-of')
	new_flaws.update({Flaw((step,precondition),'opf') for precondition in preconditions})
	return new_flaws