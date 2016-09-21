
""" Policies: 
		element.ID is unique across all data structures
		element.typ refers to the typ of an elementgraph with that element as the root
		element.name sometimes refers to the predicate name or operator name. otherwise None
		num_args is 0 means that num_args is in essence None. If predicate with no args, then this will cause problems
	Properties:
		Another element is consistent with self iff for each non-None parameter in self, the other's parameter is None or ==
		Another element is equivalent with self iff for each non-None parameter in self, other's parameter == and cannot be None
		Another element is identical just when their ids match and they're equivalent
	Operations:
		Merge operation takes all non-None parameters of other, and assumes co-consistency
""" 

import copy

class Element:

	"""Element is a token or label"""
	def __init__(self, ID, typ = None, name = None, arg_name = None):
		self.ID = ID
		self.typ = typ
		#Optional:
		self.name = name
		self.arg_name = arg_name
		self.replaced_ID = -1
		
	def isConsistent(self, other):
		""" Returns True if self and other have same name or unassigned"""
		if not self.typ is None and not other.typ is None:
			if self.typ != other.typ:
				return False
		if not self.name is None and not other.name is None:
			if self.name != other.name:
				return False
		return True
		
	def isIdentical(self, other):
		if self.ID == other.ID:
			return True
		return False
		
	def isEquivalent(self, other):
		"""Another element is equivalent with self iff 
				for each non-None parameter in self, 
					other's parameter == 
					and cannot be None
				and if for each None parameter in self,
					other's parameter cannot be None
		"""
		
		if not self.typ is None:
			if self.typ != other.typ:
				return False
		else:
			if not other.typ is None:
				return False
				
		return True
		
		
	def __eq__(self, other):
		if other is None:
			return False
		if self.ID == other.ID:
			return True
		return False
		
	def __ne__(self, other):
		return (not self.__eq__(other))
		
	def __hash__(self):
		return hash(self.ID)
			
	def merge(self, other):
		"""merge returns self with non-None properties of other,
			and assumes elements are co-consistent"""
		if not self.isConsistent(other):
			return None
		if self.isEquivalent(other):
			return self
		if self.typ is None and not other.typ is None:
			self.typ = other.typ
		if self.name is None and not other.name is None:
			self.name = other.name
		return self
		
	def __repr__(self):
		id = str(self.ID)[19:23]
		return '({}-{}-{})'.format(id, self.typ, self.name)
		
class InternalElement(Element):
	"""Internal Element is an Element with a possibly unimportant name, and a number of arguments
			Plus, a dictionary mapping ids of superordinate elements to 'roles'
				Only one role per ID... ?
				Examples:			excavate.ID : 'precondition'
									operator.ID : 'effect'
									frame.ID	: 'initial'
									frame.ID	: 'source'
	"""
	def __init__(self, ID, typ, name = None, arg_name = None, num_args = None, roles = None):
		super(InternalElement,self).__init__(ID,typ,name, arg_name)
		if num_args == None:
			num_args = 0
		if roles == None:
			roles = {}
		self.num_args = num_args
		self.roles = roles
	
	def isEquivalent(self, other):
		"""Another element is equivalent with self iff 
				for each non-None parameter in self, 
					other's parameter == 
					and cannot be None 
				and if for each None parameter in self,
						other's parameter must be None
		"""
		if not super(InternalElement,self).isEquivalent(other):
			return False
		

		if not self.name is None:
			if self.name != other.name:
				return False
		else:
			if not other.name is None:
				return False
				
		if self.num_args != other.num_args:
			return False
		
		
		# if not other.name is None:
			# if other.num_args > 0:
				# if self.num_args != other.num_args:
					# return False
			# if self.num_args == 0:
				# if self.num_args != other.num_args:
					# return False
					
						
		if not self.isConsistentRoleDict(other):
			return False
				
		return True
			
	
	def isConsistent(self, other):
	
		#If other has a typ, then return False if they are not the same
		if not super(InternalElement,self).isConsistent(other):
			return False
				
		if self.num_args >0 and other.num_args > 0:
			if self.num_args != other.num_args:
				return False

		#If other has a predicate name, then return False if they are not the same
		if not self.name is None and not other.name is None:
			if self.name != other.name:
				return False
				
						
		if not self.isConsistentRoleDict(other):
			return False
				
		return True
		
	def merge(self,other):
		"""Element merge assumes co-consistent 
			and places None properties of self with non-None propeties of other"""
			
		if super(InternalElement,self).merge(other) is None:
			return None
			
		if other.num_args > 0 and self.num_args == 0:
			self.num_args = other.num_args
			
		self.roles.update(other.roles)
			
		return self
		
	def isConsistentRoleDict(self, other):
		for ID, pos in other.roles.items():
			if ID in self.roles:
				if other.roles[ID] != self.roles[ID]:
					return False
		return True
		
	def isRole(self, role_str):
		for ID, role in self.roles.items():
			if role == role_str:
				return ID
		return False
		

		
class Operator(InternalElement):
	stepnumber = 0
	""" An operator element is an internal element with an executed status and orphan status"""
	def __init__(self, ID, typ, name = None, arg_name = None, num_args = None, roles = None, is_orphan = None, executed = None, instantiated = None):
		if instantiated == None:
			instantiated = False
		if is_orphan is None:
			is_orphan = True
		if num_args == None:
			num_args = 0
		if roles == None:
			roles = {}
		if arg_name == None:
			arg_name = Operator.stepnumber
			Operator.stepnumber+=1
		else:
			Operator.stepnumber = arg_name + 1
		
		super(Operator,self).__init__(ID,typ,name, arg_name, num_args, roles)
		self.executed = executed
		self.is_orphan = is_orphan
		self.instantiated = instantiated
		
	def isConsistent(self,other):
		if not super(Operator,self).isConsistent(other):
			return False
		
		if not other.executed is None and not self.executed is None:
			if self.executed != other.executed:
				return False
		
		return True
		
	def merge(self, other):
		if super(Operator,self).merge(other) is None:
			return None

		if not other.executed is None and self.executed is None:
			self.executed = other.executed
			
		if other.instantiated:
			self.instantiated = True
			
		return self
		
	def print_element(self):
		print('executed: {}, orphan: {}, ({}, {}, {})'.format(self.executed, self.is_orphan, self.name, self.typ, self.ID))
		for key,value in self.roles.items():
			print('\t ID={}, role={}'.format(key, value))
			
	def __repr__(self):
		if self.executed is None:
			exe = 'ex'
		else:
			exe = self.executed
		id = str(self.ID)[19:23]
		return 'operator({}-{}-{}-{})'.format(exe, self.name, self.arg_name, id)

		
class Literal(InternalElement):
	""" A Literal element is an internal element with a truth status
	"""
	def __init__(self, ID, typ, name = None, arg_name = None, num_args = None, roles = None,truth = None):
		if num_args == None:
			num_args = 0
		if roles == None:
			roles = {}
		super(Literal,self).__init__(ID,typ,name, arg_name, num_args, roles)
		self.truth = truth

	def isConsistent(self, other):
		if not super(Literal,self).isConsistent(other):
			return False
				
		if not self.truth is None and not other.truth is None:
			if self.truth != other.truth:
				return False
	
		return True
		
	def isEquivalent(self,other):
		if not super(Literal, self).isEquivalent(other):
			return False
			
		if not self.truth is None:
			if self.truth != other.truth:
				return False
		else:
			if not other.truth is None:
				return False
				
			
		return True
		
	def merge(self, other):
		if super(Literal,self).merge(other) is None:
			return None
			
		if self.truth is None and not other.truth is None:
			self.truth = other.truth
			
		return self
		
	def __repr__(self):
		id = str(self.ID)[19:23]
		return '{}-{}-{}-{}'.format(self.typ, self.truth, self.name,id)

		
		
class Argument(Element):
	object_types = None
	def __init__(self, ID, typ, name= None, arg_name = None):
		super(Argument,self).__init__(ID,typ,name, arg_name)		
	
	def isEquivalent(self, other):
		""" 
			'equivalent' arguments are consistent and have been assigned the same name
			
		"""
		if not super(Argument,self).isEquivalent(other):
			if not self.typ in self.object_types[other.typ] and not other.typ in self.object_types[self.typ]:
				return False
		
		if not self.name is None:
			if other.name != self.name:
				return False
		else:
			if not other.name is None:
				return False		
		return True

	def isConsistent(self, other):
		if not super(Argument, self).isConsistent(other):
			if not self.typ in self.object_types[other.typ] and not other.typ in self.object_types[self.typ]:
				return False
		return True

	def merge(self, other):
		if super(Argument, self).merge(other) is None:
			return None
		if self.typ in self.object_types[other.typ]:
			self.typ = other.typ
		return self
		
	def __repr__(self):
		id = str(self.ID)[19:23]
		return '(Arg {}-{}-{})'.format(id, self.typ, self.name)
	

class Actor(Argument):
	""" An actor is an argument such that 
			For each operator in arg_pos_dict where the argument is a consenting actor 'a',
			then that operator needs to be part of an intention frame where 'a' is the intender
			
		An orphan_dict is a dictionary whose keys are operators where the actor is a consenting actor
		and whose values are True or False depending on the actor's orphan status for that step
			Example:		{operator.ID : True, another_operator.ID : False}
			
		When we instantiate an Action, we identify all consenting actor arguments
				When this occurs, we add the {Operator.ID : False} to the orphan_dict of that actor
		If we successfully add that Action to an intention frame, we add {Operator.ID : True} 
				for the actor that matches the intention frame's intender
		When we merge 2 actors, we merge the orphan_dicts with preference for True
	"""
	def __init__(self, ID, typ, name= None, arg_name = None, orphan_dict = None):
		if orphan_dict == None:
			orphan_dict = {}
			
		super(Actor,self).__init__(ID,typ,name,arg_name)
		self.orphan_dict=  orphan_dict
		
		
	def merge(self, other):
		if super(Actor,self).merge(other) is None:
			return None
			
		if type(other) == Actor:
			for operatorID, status in other.orphan_dict.items():
				if operatorID not in self.orphan_dict:
					self.orphan_dict[operatorID] = status
				elif status != self.orphan_dict[operatorID]:
					#One of them must be True if they are unequal
					self.orphan_dict[operatorID] = True
		
		return self
		
	def __repr__(self):
		id = str(self.ID)[19:23]
		return '(Actor {}-{}-{})'.format(id, self.typ, self.name)

class PlanElement(Element):

	def __init__(self,ID,typ=None, name=None, arg_name = None):
		if typ == None:
			typ = 'PlanElementGraph'
			
		super(PlanElement,self).__init__(ID,typ,name, arg_name)
		
class IntentionFrameElement(Element):
	def __init__(self, ID, type_graph=None, name= None, arg_name = None, ms=None, motivation = None, intender = None,
				 goal = None, sat = None, steps = None):
		if steps == None:
			steps = set()
		if type_graph == None:
			type_graph='IntentionFrame'
			
		super(IntentionFrameElement,self).__init__(ID,type_graph,name, arg_name)
		
		self.ms = ms
		self.motivation = motivation
		self.intender = intender
		self.goal = goal
		self.sat = sat
		self.subplan = steps
		
	def external_update(self, PLAN):
		"""updates frame slots, edges, and constraints"""
		
		if not self.sat is None:
			if not self.sat in self.subplan:
				self.subplan.add(self.sat)
		
		""" If the slot is filled but the edge isn't' there, fill it in"""
		incident_edges = PLAN.getIncidentEdges(self.ID)
		labels = {ie.label for ie in incident_edges}
		if not self.goal is None:
			if 'goal-of' not in labels:
				PLAN.edges.add(Edge(self, self.goal, 'goal-of'))
		if not self.ms is None:
			if 'motivating-step-of' not in labels:
				PLAN.edges.add(Edge(self, self.ms, 'motivating-step-of'))
		if not self.sat is None:
			if 'sat-step-of' not in labels:
				PLAN.edges.add(Edge(self, self.sat,'sat-step-of'))
		if not self.intender is None:
			if 'actor-of' not in labels:
				PLAN.edges.add(Edge(self, self.intender, 'actor-of'))
		if len(self.subplan) == 0:
			neighbs = {ie.sink for ie in incident_edges if ie.label == 'in-subplan-of'}
			for step in self.subplan:
				if step not in neighbs:
					PLAN.edges.add(Edge(self, step, 'in-subplan-of'))
				
			
		""" If there's an edge but slot is None, fill it in"""
		for incident_edge in PLAN.edges:
			if incident_edge.source.ID == self.ID:
				if self.goal is None:
					if incident_edge.label == 'goal-of':
						self.goal = incident_edge.sink
				if self.ms is None:
					if incident_edge.label == 'motive-of':
						self.ms = incident_edge.sink
				if self.intender is None:
					if incident_edge.label == 'actor-of':
						self.intender = incident_edge.sink
				if self.sat is None:
					if incident_edge.label == 'sat-of':
						self.sat = incident_edge.sink
						if not self.sat in self.subplan:
							self.subplan.add(self.sat)
				if incident_edge.label == 'in-subplan-of':
					if incident_edge.sink not in self.subplan:
						self.subplan.add(incident_edge.sink)
		
		""" Add ordering constraints if not there """
		if len(self.subplan) > 0:
			for step in self.subplan:
				if not self.ms is None:
					# self.ms < step
					pass
				if not self.sat is None:
					if not self.sat is step:
						#step < self.sat
						pass

		""" consenting Actors """
		if self.intender is None:
			actors = PLAN.getConsentingActors(self.subplan)
			if len(actors) == 1:
				self.intender = actors.pop()
			if len(actors) == 0:
				print('the subplan of intention frame {} in plan {} will have no consistent consenting actors'.format(self.ID, PLAN.ID))
			if len(actors) > 1:
				pass
				#could keep them like dis: self.actors = actors
				
		""" NOTE: combine all actors """
		if not self.intender is None:
			#Can we just access all actors in plan willy nillier than this?
			pass
			
			#for step in self.subplan:
			#	{self.intender.combine(nb) for nb in PLAN.getNeighborsByLabel(step, 'actor-of') if self.ID in nb.arg_pos_dict}
				#WHEN adding a step to an intention frame, make sure to update actors with new arg_pos_dict for intention frame
				
			
		return self
	
				
					
		
class Motivation(Literal):
	def __init__(self, ID, typ=None, name=None, arg_name = None, num_args = None, truth = None, intender=None, goal=None):
		if num_args == None:
			num_args = 1
		if name == None:
			name = 'intends'
		if typ == None:
			typ = 'motivation'
		if truth == None:
			truth = True
		super(Motivation,self).__init__(ID=ID,typ=typ,name=name,arg_name = arg_name, num_args=num_args,truth =truth)
		
			
		self.actor = intender
		self.goal = goal #Goal is a literal. THIS is a case where... a Literal has-a Literal
		