from PlanElementGraph import *

""" Represent plans as element graphs.

	An open precondition flaw is a tuple <step element, precondition element>
		where precondition element is a literal element, 
		there is a precondition edge from the step element to the precondition element,
		and there is no causal link in the graph from another step to the precondition element with label 'effect'
		
	A threatened causal link flaw is a tuple <causal link edge, threatening step element>
		where if s --p--> t is a causal link edge and s_threat is the threatening step element,
			then there is no ordering path from t to s_threat,
			no ordering path from s_threat to s,
			there is an effect edge from s_threat to a literal false-p',
			and p' is consistent with p after flipping the truth attribute
		
"""

def detectThreatenedCausalLinks(graph):
	detectedThreatenedCausalLinks = set()
	"""
		For each causal link,
			for each step element,
				if step element qualifies as threatening,
					add tuple <causal-link, step element> to set
	"""
	return detectedThreatenedCausalLinks
	

def addOpenPreconditionFlaws(graph, step):
	"""
		for each precondition edge with step as the source,
			found = false
			For each causal link with step as the sink,
				If the precondition is the condition of the causal link,
					found = true
					break
			if found,
				
	"""