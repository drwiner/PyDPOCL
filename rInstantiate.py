''' This method used for instantiating a partial step via from an uninstantiated step flaw'''
	def rInstantiate(self, remaining = None, operators = None, complete_plans = None):
		"""	Recursively instantiate a step in self with some operator
			Return set of plans with all steps instantiated
			
			plan.rInstantiate(steps_Ids, {operator_1, operator_2})
		"""
		if remaining == None:
			remaining = set()
		if operators == None:
			operators = set()
		if complete_plans == None:
			complete_plans = set()
		
		#self.updatePlan()
		#remaining = {step for step in self.Steps if not step.instantiated}
		print('rInstantiate: {},\t remaining: {}'.format(self.id, len(remaining)))
		
		#BASE CASE
		if len(remaining) == 0:
			complete_plans.add(self)
			print('\nsuccess!, adding new plan {}\n'.format(self.id))
			return complete_plans
		else:
			print('rInstantiate remainings List:')
			for r in remaining:
				print('\t\t\t {}'.format(r))
			print('\n')
			
		#INDUCTION
		step_id = remaining.pop()
		new_plans = set()
		new_ids = {step_id + n + 35 for n in range(1,len(operators)+10)}
		print('\nids:')
		for d in new_ids:
			print(d, end= " ")
		print('\n')
		
		""" instantiate with every operator"""
		for op in operators:
			new_id = new_ids.pop()
			new_self = self.copyGen()
			new_self.id = self.id + new_id
			step = new_self.getElementGraphFromElementId(step_id, Action)
			op_clone = op.makeCopyFromID(new_id,1)
			#print('\n Plan {} ___instantiating_{}__with operator clone {}\n'.format(new_self.id, step_id, op_clone.id))
			print('\n Plan {} Attempting instantiation with step {} and op clone {} formally {}\n'.format(new_self.id, step.id,op_clone.id,op.id))
			new_ps = step.instantiate(op_clone, new_self) 
			print('\n returned {} new plans originally from {}\n'.format(len(new_ps), self.id))
			for p in new_ps:
				p.print_plan()
				print('\n')
			print('end new plans')
			new_plans.update(new_ps)
			#print('{} new plans from instantiating {} from operator {}-{} in plan {}'.format(len(new_ps),step.id, op.id, op.root.name, self.id))
			
		""" If completely empty, then this branch terminates"""
		if len(new_plans) == 0:
			return set()
		
		completed_plans_before= len(complete_plans)
		
		""" For each version, continue with remaining steps, choosing any operator"""
		for plan in new_plans:
			print('\ncalling rInstantiate with new_plan {}, now with remaining:'.format(plan.id),end = " ")
			for r in remaining:
				print('\t {}'.format(r), end= ", ")
			print('\n')
			#rem = {rem_id for rem_id in remaining}
			complete_plans.update(plan.rInstantiate({rem_id for rem_id in remaining}, operators, complete_plans))
		
		""" if no path returns a plan, then this branch terminates"""
		if completed_plans_before >= len(complete_plans):
			return set()
			
		#Each return from rInstantiate is a set of unique plans with all steps instantiated
		#for plan in new_plans:
			#complete_plans = plan.rInstantiate(operators,complete_plans)
		
		return complete_plans
		
def instantiate(self, operator, PLAN):
		""" instantiates self as operator in PLAN
			RETURNS a set of plans, one for each instantiation which is internally consistent
			- To instantiate a step as an operator, 
							1) make a copy of operator with new IDs
							2) operator.absolve(step)
							3) swap operator for step in plan
		"""
		
		instances = operator.getInstantiations(self)
		plans = set()
		id = PLAN.id + 1
		for instance in instances:
			Plan = PLAN.copyGen()
			Plan.id = uuid.uuid1(id) 
			id += 1
			Plan.mergeGraph(instance)
			if Plan.isInternallyConsistent():
				Plan.updateIntentionFrameAttributes()
				print('adding plan {}'.format(Plan.id))
				plans.add(Plan)
			print('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
		return plans