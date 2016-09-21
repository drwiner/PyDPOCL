"""
	A plan element graph P
	A restriction graph R representing requirements
	A plan element graph P' is P such that R is an isomorphic subgraph of P'

	Problem Formulation: Find all possible P's

	Strategy:
		For each root of R, create root-induced subgraph of R, called Roots = {r1,..,rn}
		For each ri in Roots, assign ri to some element in P, to a domain action, or to nothing
			Assignment = {r1:nothing, r2: pi, r3:pj, r4:"excavate", etc}
			A key,value pair is valid just when the key is a consistent subgraph of value, or the value is nothing
			If all key,value pairs are valid, then the Assignment is valid.
		Reformulated Problem: Find all valid Assignments, then value.unifyWith(key)
			LITS: cannot be roots - unless they refer to a specific element already in the story
				Thus, any Lit key 'q' is assigned to itself {q:q}?
			STEPS:
				{s: t} --> t.unifyWith(s) just when s is a consistent subgraph of t
				Returns a set of steps T = {t'_1,...,t'_n} such that s is an isomorphic subgraph of t
				For each step s, {s:t'_1,...,s:t'_n, s:domain_action_1,...,s:domain_action_m}
			ORDERINGS: problems are detected just when there is a cycle in an ordering graph.
			LINKS: For each link s --e--> t, add edges s --eff--> e and t --pre--> e. Any assignments of the form
							{x1 : x1', x2 : x2',..., xn : xn'} such that x1,..,xn in X are all linked, then create
							some total ordering of X and go through reverse order and do the following:
								:create all possible assignments for X[i], and for each, carry mapping to X[i-1]

			when that condition is specified:
						if the condition is specified in the link, then there are edges:
							s --eff--> e, t --pre--> e.
						if the conditino is unspecified, then the condition e is a hollow container
			Frames:
				{f : i} --> i.unifyWith(f) just when f is consistent with i
					f is consistent with i just when:
						actors are consistent
						goals are consistent
						either f.ms is consistent subgraph of i.ms, or vice versa
						either f.sat is consistent with subgraph of i.sat or vice versa
						recursively check the following:
							s in f.subplan and s--p-->f.sat, and t in i.subplan and t--p-->i.sat:
								then t must be consistent subgraph of s
							check if antecedents of s are consistent with antecedents of t
						rCheckSubplan(s, t):
							t_antes = {(t'.condition, t') for t' in i.subplan.links if t'.isAntecedent(t)}.
							s_antes = {(s'.condition, s') for s' in f.subplan.links if s'.isAntecedent(s)}
							for (e, t') in t_antes:
								S = {(e',s') for s_ante in s_antes if e'.isConsistent(e)}
								if len(S) == 0
									continue (because, there's no required step consistency)
								if t'.isConsistentSubgraph(s_ante


For now, don't worry about intention frames, but here are somenotes that may or may not offer insight
	Let I = {i1,...,in} be the set of frames in Req.
	Let F be the set of frames in P.
	Create a dictionary IMap = {i1 : fi,...,fj,
								,...,
								im : fu,..,fv}
			where for each (i_j, f_j) pair, i_j is consistent with f_j

	NOTE: for each step "t" in a frame "i" in Req, let t.TMap = "s" be a step such that {t : s} is in TMap.
	Two frames i, f are consistent just when:
		actors are consistent, goals are consistent,
		fi.ms is either equal to or a consistent subgraph of a step "s" in fj.ms.TMap
			Construct intention frame
		if fi.ms is equal to or a consistent subgraph of with fj.ms.TMap

	For each frame 'i_j' of the form <a, g, ms, sat, Sf> in Req, remove f_j where i_j : f_j for any of the following issues:
		if t_i in T is f.ms, then remove s_i where t_i : s_i if s_i cannot include intends(a, g) as one of its effects
		if t_i in T is f.sat, then remove s_i where t_i : s_i if s_i cannot include g as one of its effects or cannot
		have the consent of 'a'
		if t_i in T is f.insubplan, then remove s_i if s_i cannot have the consent of 'a'

	For each partially specified frame 'i' of the form <a, g, ms, sat, Sf> in Req:


"""

"""

Let T = {t1,...,tn} be the set of steps in Req.
Let S be set of steps in P.
Let D be the set of domain actions.
Create a dictionary TMap = {t1 : sk,...,sw, du,..,dv,
							t2 : sq,...,sp, di,...,dj,
							,...,
							tn : ss,...,st, dw,...,dr}
		where for each (t_i, p_i) pair, t_i is a consistent subgraph of p_i

For each ordering of the form ti < tj in Req, remove s_i, s_j where t_i : s_i and t_j : s_j and s_i,s_j in S if there
is an ordering path from s_j to s_i in P.
For each link of the form ti --e--> tj in Req, remove s_i, s_j where t_i : s_i and t_j : s_j if s_i is not a valid
antecedent for s_j.
"""

#from Restrictions import Restriction
#self is Planner
def assignReqs(self, Plan, ReqSteps, ReqLinks, ReqOrderings):
	S = Plan.Steps
	D = self.op_graphs
	TMap = {t : {s for s in S if t.isIsomorphicSubgraphOf(s, consistency=True)}
			for t in ReqSteps}
	DMap = {t : {d for d in D if t.isIsomorphicSubgraphOf(d, consistency=True)}
			for t in ReqSteps}

	for (ti,tj) in ReqOrderings:
		removable = {(si,sj) for si in TMap[ti] for sj in TMap[tj] if Plan.OrderingGraph.isPath(sj,si)}
		for (si,sj) in removable:
			TMap[ti] -= si
			TMap[tj] -= sj

	TMap.update(DMap)
	for (ti,tj,te) in ReqLinks:
		removable = {(si,sj) for si in TMap[ti] for sj in TMap[tj] if Plan.OrderingGraph.isPath(sj,si)}
		for (si,sj) in removable:
			TMap[ti] -= si
			TMap[tj] -= sj

		removable = {(si,sj) for si in TMap[ti] for sj in TMap[tj] if not si.isConsistentAntecedentFor(sj,effect =te)}
		for (si,sj) in removable:
			TMap[ti] -= si
			TMap[tj] -= sj

	return TMap


