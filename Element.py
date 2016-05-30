
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
		self.name = name
		
	def isConsistent(self, other):
		#""" Returns True if self and other have same name or unassigned"""
		if not other.type is None:
			if self.type != other.type:
				return False
		return True
		
	def isCoConsistent(self, other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return false
		
	def isIdentical(self, other):
		if self.id == other.id:
			if self.isEquivalent(other):
				return True
		return False
		
	def isEquivalent(self, other):
		if self.type == other.type:
			return True
		return False
		
	def isEqual(self, other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
			
	def merge(self, other):
		"""merge returns self with non-None properties of other,
			and assumes elements are co-consistent"""
		if not self.isCoConsistent(other):
			return None
		if self.isEqual(other):
			return self
		if self.type is None and not other.type is None:
			self.type = other.type
		if self.name is none and not other.name is None:
			self.name = other.name
		return self
		
class InternalElement(Element):
	"""Internal Element is an Element with a possibly unimportant name, and a number of arguments"""
	def __init__(self, id, type, name = None, num_args = 0):
		super(InternalElement,self).__init__(id,type,name)
		self.num_args = num_args
	
	def isEquivalent(self, other):
		# for each incident edge of other, there is a unique equivalent edge of self
		# and for each constraint of other, there is no uniqe equivalent edge of self
		if not (super(InternalElement,self).isEquivalent(other) \
			and self.name == other.name \
			and self.num_args == other.num_args):
			return False
		return True
			
	
	def isConsistent(self, other):
	
		#If other has a type, then return False if they are not the same
		if not super(InternalElement,self).isConsistent(other):
			return False
				
		#If other has an argument number, then return False if they are not the same
		if other.num_args > 0:
			if self.num_args != other.num_args:
				return False
	
		#If other has a predicate name, then return False if they are not the same
		if not other.name is None:
			if self.name != other.name:
				return False
				
		return True

	def isCoConsistent(self,other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
		
	def merge(self,other):
		"""Element merge assumes co-consistent 
			and places None properties of self with non-None propeties of other"""
			
		if super(InternalElement,self).merge(other) is None:
			return None
			
		if other.num_args > 0 and self.num_args == 0:
			self.num_args = other.num_args
			
		return self
		
class Operator(InternalElement):
	""" An operator element is an internal element with an executed status"""
	def __init__(self, id, type, name = None, num_args = 0, executed = None):
		super(Operator,self).__init__(id,type,name, num_args)
		self.executed = executed
		
	def isConsistent(self,other):
		if not super(Operator,self).isConsistent(other):
			return False
		
		if not other.executed is None and self.executed != other.executed:
			return False
		
		return True
				
	def isCoConsistent(self,other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
		
	def merge(self, other):
		if super(Operator,self).merge(other) is None:
			return None

		if not other.executed is None and self.executed is None:
			self.executed = other.executed

		return self
		
class Literal(InternalElement):
	""" A Literal element is an internal element with a truth status"""
	def __init__(self, id, type, name = None, num_args = 0, truth = None):
		super(Literal,self).__init__(id,type,name, num_args)
		self.truth = truth

	def isConsistent(self, other):
		if not super(Literal,self).isConsistent(other):
			return False
				
		if not other.truth is None:
			if self.truth != other.truth:
				return False
				
		return True

	def isCoConsistent(self, other):
		if self.isConsistent(other) and other.isConsistent(self):
			return True
		return False
		
	def isEquivalent(self,other):
		if self.name != other.name:
			return False
		if self.type != other.type:
			return False
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
		
class Argument(Element):
	""" An Argument Element is an element with a dictionary mapping operator ids to positions 
		Bindings are stored on arguments. 
			An argument can take at most 1 position per operator id.
			A Merge makes a codesignation between two arguments.
			Noncodesignation is 
	"""
	
	def __init__(self, id, type, name= None, arg_pos_dict = {}):
		super(Argument,self).__init__(id,type,name)
		self.arg_pos_dict = arg_pos_dict
		
	def isConsistent(self, other):
		if not super(Argument,self).isConsistent(other):
			return False
		if other.id in other.arg_pos_dict:
			if other.arg_pos_dict[other.id] != self.arg_pos_dict[self.id]:
				return False
		return True
	
	def isEquivalent(self, other):###Equivalent if for every shared key, share the same value?
		if super(Argument,self).isEquivalent(other) and self.isConsistent(other):
			return True
		return False
		
	def isEqual(self,other):
		if self.isEquivalent(other) and other.isEquivalent(self):
			return True
		return False
		
	def merge(self, other):
		if super(Argument,self).merge(other) is None:
			return None
		
		self.arg_pos_dict.update(other.arg_pos_dict)
		return self

class PlanElement(Element):

	def __init__(self,id,type, name=None,\
				Steps=set(), \
				Bindings = set(),\
				Orderings=set(),  \
				CausalLinks=set(), \
				IntentionFrames=set()\
				):
		
		super(PlanElement,self).__init__(id,type,name)
		
		self.Steps = Steps
		self.Bindings = Bindings
		self.Orderings = Orderings
		self.CausalLinks = CausalLinks
		self.IntentionFrames = IntentionFrames
		
class IntentionFrameElement(Element):
	def __init__(self, id, type, name= None, ms=None, motivation = None, intender = None, goal = None, sat = None, steps = set()):
		super(IntentionFrameElement,self).__init__(id,type,name)
		
		self.ms = ms
		self.motivation = motivation
		self.intender = intender
		self.goal = goal
		self.sat = sat
		self.subplan = subplan
		
class Motivation(Literal):
	def __init__(self, id, type='motivation', name='intends', num_args = 1, truth = True, intender=None, goal=None):
		super(Motivation,self).__init__(id,type,name,num_args,truth)
		self.actor = intender
		self.goal = goal #Goal is a literal. THIS is a case where... a Literal has-a Literal
		