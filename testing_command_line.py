s_need, pre = flaw.flaw
Precondition = graph.getElementGraphFromElementID(pre.ID,Condition)
steps = list((step for step in graph.Steps if step != s_need))
step = steps[1]
graph.OrderingGraph.isPath(s_need, step)
effs = [eff for eff in graph.getNeighborsByLabel(step, 'effect-of')]
eff = effs[4]
Effect = graph.getElementGraphFromElementID(eff.ID, Condition)
Effect
Effect.canAbsolve(Precondition)
Effect_absorbtions = Effect.getInstantiations(Precondition)
eff_abs = Effect_absorbtions.pop()
graph_copy = copy.deepcopy(graph)
graph_copy.mergeGraph(eff_abs)
replace_ids = {element.ID for element in eff_abs.elements}
incoming = {edge for edge in graph_copy.edges if hasattr(edge.sink, 'replaced_ID')}
incoming = {edge for edge in incoming if edge.sink.replaced_ID in replace_ids}
rmv = {edge for edge in incoming if hasattr(edge.source, 'replaced_ID')}
rmv = {edge for edge in rmv if edge.source.replaced_ID in replace_ids}
incoming -= rmv
uniqueSinks = {edge.sink for edge in incoming}
for snk in uniqueSinks:
	new_sink = eff_abs.getElementByReplacedId(snk.ID)
	graph_copy.replaceWith(snk,new_sink)
							
self.addStep(graph_copy, step, s_need, eff_abs.root, new = False)



from pddlToGraphs import *
from Planner import *
domain_file = 'domains/mini-indy-domain.pddl'
problem_file = 'domains/mini-indy-problem.pddl'



operators, objects, initAction, goalAction = parseDomainAndProblemToGraphs(domain_file, problem_file)
planner = PlanSpacePlanner(operators, objects, initAction, goalAction)
graph = planner[0]
result = planner.rPOCL(graph)
self = planner



print(graph)
print('num flaws: {} '.format(len(graph.flaws)))

if not graph.isInternallyConsistent():
	print('wakeup')
	
if len(graph.flaws) == 0:
	print('wakeup')
	
#INDUCTION\
graph.isInternallyConsistent()
graph = results.pop()
graph.isInternallyConsistent()
flaw = graph.flaws.pop() 



if flaw.name == 'opf':
	print('opf')
	s_need, pre = flaw.flaw
	print(graph.getElementGraphFromElement(s_need,Action))
	print(graph.getElementGraphFromElement(pre,Condition))
	results = self.reuse(graph, flaw)
	print('reuse results: {} '.format(len(results)))
	results.update(self.newStep(graph, flaw))
	print('newStep results: {} '.format(len(results)))
	if len(results) == 0:
		print('could not resolve opf')

	
if flaw.name == 'tclf':
	results = self.resolveThreatenedCausalLinkFlaw(graph,flaw)
	
for result in results:
	new_flaws = detectThreatenedCausalLinks(result)
	result.flaws += new_flaws
	print('detected tclfs: {} '.format(len(new_flaws)))

if len(results) == 1:
	graph = results.pop()
else:
	print('wake up')

	
	
#replace this with choosing highest ranked graph
for g in results:
	print('rPOCLing')
	#result = self._frontier.pop()
	result = self.rPOCL(g) 
	if not result is None:
		return result