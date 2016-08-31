# story-elements

This is a partial-order causal-link (POCL) planner adopting a plan-space search strategy (each child
node in the search is a refinement to a flaw in the parent-node. The algorithm iteratively selects plan at frontier of
search, selects a flaw, refines flaws, identifies new flaws, and repeats.

The implementation of this planner adopts a graph-based representation such that a plan is a graph. Steps and
literals are subgraphs where directed edges connect parent elements to child elements in a hierarchy. For example, a grounded literal is a graph
whose root represents the predicate name and truth-status of the literal, and the children are elements representing
atoms/constants, and each edge from the parent to the child is labeled with the argument position. The benefit of
this graph representation is its common language of abstraction. It makes it easy for an outside program to easily
detect patterns that extend across multiple literals and steps, and to make atomic changes/additions, restrictions to
 a plan.

python Planner.py 'domain.pddl' 'problem.pddl'

Examples:

python Planner.py domains/ark-domain.pddl domains/ark-problem.pddl > console.txt

python Planner.py domains/mini-indy-domain.pddl domains/mini-indy-problem.pddl


tested in python 3.3 and 3.5


TODO: intention frames (open motivation flaws, unsatisfied intention frame flaws, orphan flaws, execution marking)

TODO: actions with duration



--David Winer drwiner@cs.utah.edu