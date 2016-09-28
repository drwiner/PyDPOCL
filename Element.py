
""" Policies: 
		element.ID is unique across all data structures
		element.typ refers to the typ of an elementgraph with that element as the root
		element.name sometimes refers to the predicate name or operator name. otherwise None
		num_args is 0 means that num_args is in essence None. If predicate with no args, then this may cause problems
	Properties:
		Another element is consistent with self iff for each non-None parameter in self, the other's parameter is None or ==
		Another element is equivalent with self iff for each non-None parameter in self, other's parameter == and cannot be None
		Another element is identical just when their ids match and they're equivalent
	Operations:
		Merge operation takes all non-None parameters of other, and assumes co-consistency
""" 

import copy

class Element:

	"""Element is a token or label with the following attributes"""
	def __init__(self, ID, typ = None, name = None, arg_name = None):
		self.ID = ID
		self.typ = typ
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
	"""

	def __init__(self, ID, typ, name = None, arg_name = None, num_args = None):
		super(InternalElement,self).__init__(ID,typ,name, arg_name)
		if num_args == None:
			num_args = 0
		self.num_args = num_args
	
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
				
		return True
		
	def merge(self,other):
		"""Element merge assumes co-consistent 
			and places None properties of self with non-None propeties of other"""
			
		if super(InternalElement,self).merge(other) is None:
			return None
			
		if other.num_args > 0 and self.num_args == 0:
			self.num_args = other.num_args
			
		return self
		

		
class Operator(InternalElement):
	stepnumber = 0
	""" An operator element is an internal element with an executed status and orphan status"""
	def __init__(self, ID, typ, name = None, stepnumber = None, num_args = None, executed = None, arg_name = None):

		if num_args == None:
			num_args = 0
		if stepnumber == None:
			stepnumber = Operator.stepnumber
			Operator.stepnumber+=1
		else:
			Operator.stepnumber = stepnumber + 1
		
		super(Operator,self).__init__(ID, typ, name, arg_name, num_args = num_args)
		self.stepnumber = stepnumber
		self.executed = executed
		
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
			
	def __repr__(self):
		if self.executed is None:
			exe = 'ex'
		else:
			exe = self.executed
		id = str(self.ID)[19:23]
		return 'operator({}-{}-{}-{})'.format(exe, self.name, self.stepnumber, id)

		
class Literal(InternalElement):
	""" A Literal element is an internal element with a truth status
	"""
	def __init__(self, ID, typ, name = None, arg_name = None, num_args = None,truth = None):
		if num_args == None:
			num_args = 0

		super(Literal,self).__init__(ID,typ,name, arg_name, num_args)
		self.truth = truth

	def isConsistent(self, other):
		if not super(Literal,self).isConsistent(other):
			return False
				
		if not self.truth is None and not other.truth is None:
			if self.truth != other.truth:
				return False
	
		return True

	def isOpposite(self, other):
		opp = copy.deepcopy(self)
		if self.truth == True:
			opp.truth = False
		else:
			opp.truth = True
		return opp.isConsistent(other)
		
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
		return '|Arg: {} {} {} {}|'.format(id, self.typ, self.name, self.arg_name)
	

class Actor(Argument):
	""" An actor is an argument
	"""
	def __init__(self, ID, typ, name= None, arg_name = None):
		super(Actor,self).__init__(ID,typ,name,arg_name)
		
	def merge(self, other):
		if super(Actor,self).merge(other) is None:
			return None
		
		return self
		
	def __repr__(self):
		id = str(self.ID)[19:23]
		return '|Actor: {} {} {} {}|'.format(id, self.typ, self.name, self.arg_name)

class PlanElement(Element):

	def __init__(self,ID,typ=None, name=None, arg_name = None):
		if typ == None:
			typ = 'PlanElementGraph'
			
		super(PlanElement,self).__init__(ID,typ,name, arg_name)