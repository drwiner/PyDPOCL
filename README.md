# story-elements

This is a partial-order causal-link planner (POCL), adopting planning as plan refinement, where each child node in the
search is a refinement to a flaw in the parent-node. Iteratively selects plan at frontier of search, selects a flaw,
refines flaws, identifies new flaws, and repeats.

The implementation of this planner adopts a graph-based representation such that elements in the plan, such as steps and literals, are themselves subgraphs where each
directed edges connect parent elements to child elements in a hierarchy. For example, a grounded literal is a graph
whose root represents the predicate name and truth-status of the literal, and the children are elements representing
atoms/constants, and each edge from the parent to the child is labeled with the argument position. The benefit of
this graph representation is to enable an outside program to make very minute/atomic changes/additions/restrictions
to a plan with a common language of abstraction.