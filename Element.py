
""" Policies: 
		element.id is unique across all data structures
		element.type refers to the type of an elementgraph with that element as the root
		element.name sometimes refers to the predicate name or operator name. otherwise None
		num_args is 0 means that num_args is in essence None. If predicate with no args, then this will cause problems
	Properties:
		Another element is consistent with self iff for each non-None parameter in self, the other's parameter is None or ==
		Another element is equivalent with self iff for each non-None parameter in self, other's parameter == and cannot be None
		Another element is identical just when their ids match and they're equivalent
	Operations:
		Merge operation takes all non-None parameters of other, and assumes co-consistency
""" 
class Element:
	"""Element is a token or label"""
	def __init__(self, id, type = None, name = None):
		self.id = id
		self.type = type
		#Optional:
		self.name = name
		
	def isConsistent(self, other):
		""" Returns True if self and other have same name or unassigned"""
		if not self.type is None and not other.type is None:
			if self.type != other.type:
				return False
		if not self.name is None and not other.name is None:
			if self.name != other.name:
				return False
		return True
		
	def isIdentical(self, other):
		if self.id == other.id:
			if self.isEqual(other):
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
		
		if not self.type is None:
			if self.type != other.type:
				return False
				
		return True
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
			
	def merge(self, other):
		"""merge returns self with non-None properties of other,
			and assumes elements are co-consistent"""
		if not self.isConsistent(other):
			return None
		if self.isEqual(other):
			return self
		if self.type is None and not other.type is None:
			self.type = other.type
		if self.name is None and not other.name is None:
			self.name = other.name
		return self
		
	def combine(self, other):
		if not self.isConsistent(other):
			return None
		if self.isEqual(other):
			return self
		if other.merge(self) is None:
			return None
		if self.merge(other) is None:
			return None
		return self
			
	def print_element(self):
		print('(',self.id, self.type, self.name,')')
		
	def __repr__(self):
		return '({} {} {})'format(self.id, self.type, self.name)
		
class InternalElement(Element):
	"""Internal Element is an Element with a possibly unimportant name, and a number of arguments
			Plus, a dictionary mapping ids of superordinate elements to 'roles'
				Only one role per id... ?
				Examples:			excavate.id : 'precondition'
									operator.id : 'effect'
									frame.id	: 'initial'
									frame.id	: 'source'
	"""
	def __init__(self, id, type, name = None, num_args = None, roles = None):
		super(InternalElement,self).__init__(id,type,name)
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
				
		# must be num_args if there is no name
		if not other.name is None:
			if self.num_args == 0:
				if self.num_args != other.num_args:
					return False
					
						
		if not self.isConsistentRoleDict(other):
			return False
				
		return True
			
	
	def isConsistent(self, other):
	
		#If other has a type, then return False if they are not the same
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
		for id, pos in other.roles.items():
			if id in self.roles:
				if other.roles[id] != self.roles[id]:
					return False
		return True
		
	def isRole(self, role_str):
		for id, role in self.roles.items():
			if role == role_str:
				return id
		return False
		
		
class Operator(InternalElement):
	""" An operator element is an internal element with an executed status and orphan status"""
	def __init__(self, id, type, name = None, num_args = None, roles = None, is_orphan = None, executed = None, instantiated = None):
		if instantiated == None:
			instantiated = False
		if is_orphan is None:
			is_orphan = True
		if num_args == None:
			num_args = 0
		if roles == None:
			roles = {}
		super(Operator,self).__init__(id,type,name, num_args, roles)
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
		print('executed: {}, orphan: {}, ({}, {}, {})'.format(self.executed, self.is_orphan, self.name, self.type, self.id))
		#print('executed:',self.executed,', orphan=',self.is_orphan,'(',self.id, self.type, self.name,')')
		for key,value in self.roles.items():
			print('\t id={}, role={}'.format(key, value))
			
	def __repr__(self):
		st = 'executed: {}, orphan: {}, ({}, {}, {})'.format(self.executed, self.is_orphan, self.name, self.type, self.id)
		for key,value in self.roles.items():
			st.append('\t id={}, role={}'.format(key,value))
		return st

		
class Literal(InternalElement):
	""" A Literal element is an internal element with a truth status
	"""
	def __init__(self, id, type, name = None, num_args = None, roles = None,truth = None):
		if num_args == None:
			num_args = 0
		if roles == None:
			roles = {}
		super(Literal,self).__init__(id,type,name, num_args, roles)
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
				
			
		return True
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		if super(Literal,self).merge(other) is None:
			return None
			
		if self.truth is None and not other.truth is None:
			self.truth = other.truth
			
		return self
			
	def print_element(self):
		print(self.truth, '(',self.id, self.type, self.name,')')
		
		
class Argument(Element):
	""" An Argument Element is an element with a dictionary mapping operator ids to positions 
		Bindings are stored on arguments. 
			An argument can take at most 1 position per operator id.
			A Merge makes a codesignation between two arguments.
		 
	"""
	
	def __init__(self, id, type, name= None, arg_pos_dict = None):
		if arg_pos_dict == None:
			arg_pos_dict = {}
		super(Argument,self).__init__(id,type,name)
		#arg_pos_dict is a mapping from operator.ids to positions
		self.arg_pos_dict = arg_pos_dict
		
	def isConsistent(self, other):
		""" isConsistent if for every other.id in arg_pos_dict, 
			either	A) there is no id in self
					B) the same id is there and the position is the same
		"""
		if not super(Argument,self).isConsistent(other):
			return False
		
		#Trivially, true if other has no arg_pos_dicts to speak of
		if len(other.arg_pos_dict) == 0:
			return True
			
		if not self.isConsistentArgPosDict(other):
			return False
			
		return True
	
	def isConsistentArgPosDict(self, other):
		for id, pos in other.arg_pos_dict.items():
			if id in self.arg_pos_dict:
				if other.arg_pos_dict[id] != self.arg_pos_dict[id]:
					return False
		return True
	
	def isEquivalent(self, other):
		""" isEquivalent if for all shared keys, the value is the same.
		"""
		""" equivalent if for super equivalent and 
			for every id:pos in other, id in self and id: pos
			BUT cannot be equivalent if it has no arg_pos_dict
		"""
		if not super(Argument,self).isEquivalent(other):
			return False
			
		if len(other.arg_pos_dict) == 0:
			return False
			
		if not self.isConsistentArgPosDict(other):
			return False
				
		return True
		
	def isEqual(self,other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		""" Merging arguments:
				Assume self and other arg_pos_dicts are consistent/equivalent
				Take all entries from other's arg_pos_dict
		"""
		if super(Argument,self).merge(other) is None:
			return None
		
		self.arg_pos_dict.update(other.arg_pos_dict)
		return self
		
	def print_element(self):
		print('(',self.id, self.type, self.name,')')
		for key,value in self.arg_pos_dict.items():
			print("\t op.id=", key,":","pos=",value)

class Actor(Argument):
	""" An actor is an argument such that 
			For each operator in arg_pos_dict where the argument is a consenting actor 'a',
			then that operator needs to be part of an intention frame where 'a' is the intender
			
		An orphan_dict is a dictionary whose keys are operators where the actor is a consenting actor
		and whose values are True or False depending on the actor's orphan status for that step
			Example:		{operator.id : True, another_operator.id : False}
			
		When we instantiate an Action, we identify all consenting actor arguments
				When this occurs, we add the {Operator.id : False} to the orphan_dict of that actor
		If we successfully add that Action to an intention frame, we add {Operator.id : True} 
				for the actor that matches the intention frame's intender
		When we merge 2 actors, we merge the orphan_dicts with preference for True
	"""
	def __init__(self, id, type, name= None, arg_pos_dict = None, orphan_dict = None):
		if arg_pos_dict == None:
			arg_pos_dict = {}
		if orphan_dict == None:
			orphan_dict = {}
			
		super(Actor,self).__init__(id,type,name, arg_pos_dict)
		self.orphan_dict=  orphan_dict
		
	def merge(self, other):
		if super(Actor,self).merge(other) is None:
			return None
			
		for operatorID, status in other.orphan_dict.items():
			if operatorID not in self.orphan_dict:
				self.orphan_dict[operatorID] = status
			elif status != self.orphan_dict[operatorID]:
				#One of them must be True if they are unequal
				self.orphan_dict[operatorID] = True
				
		self.arg_pos_dict.update(other.arg_pos_dict)
		
		return self

class PlanElement(Element):

	def __init__(self,id,type=None, name=None,\
				#Steps=None, \
				#Orderings=None,  \
				#CausalLinks=None, \
				#IntentionFrames=None\
				):
		if type == None:
			type = 'PlanElementGraph'
		
		# if Steps == None:
			# Steps = set()
		# if Orderings == None:
			# Orderings = set()
		# if CausalLinks == None:
			# CausalLinks = set()
		# if IntentionFrames == None:
			# IntentionFrames = set()
			
		super(PlanElement,self).__init__(id,type,name)
		
		# self.Steps = Steps
		# self.Orderings = Orderings
		# self.CausalLinks = CausalLinks
		# self.IntentionFrames = IntentionFrames
		
class IntentionFrameElement(Element):
	def __init__(self, id, type_graph=None, name= None, ms=None, motivation = None, intender = None, goal = None, sat = None, steps = None):
		if steps == None:
			steps = set()
		if type_graph == None:
			type_graph='IntentionFrame'
			
		super(IntentionFrameElement,self).__init__(id,type_graph,name)
		
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
		incident_edges = PLAN.getIncidentEdges(self.id)
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
			if incident_edge.source.id == self.id:
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
				print('the subplan of intention frame {} in plan {} will have no consistent consenting actors'.format(self.id, PLAN.id))
			if len(actors) > 1:
				pass
				#could keep them like dis: self.actors = actors
				
		""" NOTE: combine all actors """
		if not self.intender is None:
			#Can we just access all actors in plan willy nillier than this?
			for step in self.subplan:
				{self.intender.combine(nb) for nb in PLAN.getNeighborsByLabel(step, 'actor-of') if self.id in nb.arg_pos_dict}
				#WHEN adding a step to an intention frame, make sure to update actors with new arg_pos_dict for intention frame
				
			
		return self
	
				
					
		
class Motivation(Literal):
	def __init__(self, id, type=None, name=None, num_args = None, truth = None, intender=None, goal=None):
		if num_args == None:
			num_args = 1
		if name == None:
			name = 'intends'
		if type == None:
			type = 'motivation'
		if truth == None:
			truth = True
		super(Motivation,self).__init__(id=id,type=type,name=name,num_args=num_args,truth =truth)
		
			
		self.actor = intender
		self.goal = goal #Goal is a literal. THIS is a case where... a Literal has-a Literal
		