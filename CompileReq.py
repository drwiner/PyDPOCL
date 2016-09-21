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
			ORDERINGS and LINKS: are edges between steps, and problems are detected just when there is a cycle in an
									ordering graph. when there is a causal link, consider first cases when that
									condition is specified:
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




"""