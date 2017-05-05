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
from uuid import uuid4


class Element:
	"""Element is a token or label with the following attributes"""

	def __init__(self, ID=None, typ=None, name=None, arg_name=None):
		if ID is None:
			ID = uuid4()

		# ID is a unique reference instance
		self.ID = ID
		# typ refers to the python object type of the graph whose root is this element
		self.typ = typ
		# name is op_type, or literal predicate name, etc.
		self.name = name
		# arg_name is the name designated as a variable in some operator
		self.arg_name = arg_name
		# replaced_ID is the unchanging ID designed once the element is part of an instance of a ground step
		self.replaced_ID = -1

	def isConsistent(self, other):
		""" Returns True if self and other have same name or unassigned"""
		if not self.isConsistentType(other):
			return False
		if not self.isConsistentName(other):
			return False
		return True

	def isConsistentType(self, other):
		if self.typ is not None and other.typ is not None:
			if self.typ != other.typ:
				return False
		return True

	def isConsistentName(self, other):
		if self.name is not None and other.name is not None:
			if self.name != other.name:
				return False
		return True

	def isEquivalent(self, other):

		if self.typ is not None:
			if self.typ != other.typ:
				return False
		else:
			if other.typ is not None:
				return False

		return True

	def __eq__(self, other):
		if other is None:
			return False
		return self.ID == other.ID

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.ID)

	def merge(self, other):
		"""merge returns self with non-None properties of other,
			and assumes elements are co-consistent"""
		if not self.isConsistent(other):
			return None
		if self.isEquivalent(other):
			return self
		if self.typ is None and other.typ is not None:
			self.typ = other.typ
		if self.name is None and other.name is not None:
			self.name = other.name
		return self

	def __repr__(self):
		id = str(self.ID)[19:23]
		return '({}-{}-{})'.format(id, self.typ, self.name)


class InternalElement(Element):
	"""Internal Element is an Element with a possibly unimportant name, and a number of arguments
	"""

	def __init__(self, ID=None, typ=None, name=None, arg_name=None, num_args=None):
		super(InternalElement, self).__init__(ID, typ, name, arg_name)
		if num_args == None:
			num_args = 0
		self.num_args = num_args

	def isEquivalent(self, other):
		if not super(InternalElement, self).isEquivalent(other):
			return False

		if self.name is not None:
			if self.name != other.name:
				return False
		else:
			if other.name is not None:
				return False

		if self.num_args != other.num_args:
			return False

		return True

	def isConsistent(self, other):

		# If other has a typ, then return False if they are not the same
		if not super(InternalElement, self).isConsistent(other):
			return False

		if self.num_args > 0 and other.num_args > 0:
			if self.num_args != other.num_args:
				return False

		# If other has a predicate name, then return False if they are not the same
		if self.name is not None and other.name is not None:
			if self.name != other.name:
				return False

		return True

	def merge(self, other):

		if super(InternalElement, self).merge(other) is None:
			return None

		if other.num_args > 0 and self.num_args == 0:
			self.num_args = other.num_args

		return self


class Operator(InternalElement):
	stepnumber = 0
	""" An operator element is an internal element with an executed status and orphan status"""

	def __init__(self, ID=None, typ=None, name=None, stepnumber=None, num_args=None, executed=None, arg_name=None):
		if typ is None:
			typ = 'Action'
		if num_args is None:
			num_args = 0
		if stepnumber is None:
			stepnumber = Operator.stepnumber
			Operator.stepnumber += 1
		else:
			Operator.stepnumber = stepnumber + 1

		super(Operator, self).__init__(ID, typ, name, arg_name, num_args=num_args)
		self.stepnumber = stepnumber
		self.executed = executed
		self.is_decomp = False
		self.height = 0

	def __hash__(self):
		return hash(self.ID)

	def __eq__(self, other):
		if other is None:
			# this ain't good
			raise ValueError('self {}  == other {}, other is None'.format(self, other))
		# return False
		return self.ID == other.ID

	# if self.name == other.name:
	#	if self.stepnumber == other.stepnumber:
	#			return True
	#	return False

	def isConsistent(self, other):
		if not super(Operator, self).isConsistent(other):
			return False

		if other.executed is not None and self.executed is not None:
			if self.executed != other.executed:
				return False

		return True

	def merge(self, other):
		if super(Operator, self).merge(other) is None:
			return None

		if not other.executed is None and self.executed is None:
			self.executed = other.executed

		return self

	def __repr__(self):
		if self.executed is None:
			exe = ''
		else:
			exe = self.executed
		uid = str(self.ID)[19:23]
		return '{}{}-{}-{}'.format(exe, self.name, self.stepnumber, uid)


class Literal(InternalElement):
	""" A Literal element is an internal element with a truth status
	"""

	def __init__(self, ID=None, typ=None, name=None, arg_name=None, num_args=None, truth=None):
		if num_args is None:
			num_args = 0
		if typ is None:
			typ = 'Condition'

		super(Literal, self).__init__(ID, typ, name, arg_name, num_args)
		self.truth = truth

	def __hash__(self):
		return hash(self.name) ^ hash(self.truth)

	def isConsistent(self, other):
		if not super(Literal, self).isConsistent(other):
			return False

		if self.truth is not None and other.truth is not None:
			if self.truth != other.truth:
				return False

		return True

	def isOpposite(self, other):
		opp = copy.deepcopy(self)
		if self.truth is True:
			opp.truth = False
		else:
			opp.truth = True
		return opp.isConsistent(other)

	def isEquivalent(self, other):
		if not super(Literal, self).isEquivalent(other):
			return False

		if self.truth is not None:
			if self.truth != other.truth:
				return False
		else:
			if other.truth is not None:
				return False

		return True

	def merge(self, other):
		if super(Literal, self).merge(other) is None:
			return None

		if self.truth is None and other.truth is not None:
			self.truth = other.truth

		return self

	def __repr__(self):
		shrt_id = str(self.ID)[19:23]
		return 'literal-{}-{}-{}'.format(shrt_id, self.truth, self.name)


class Argument(Element):
	def __init__(self, ID=None, typ=None, name=None, arg_name=None):
		if typ is None:
			typ = 'Arg'
		super(Argument, self).__init__(ID, typ, name, arg_name)
		self.p_types = [typ]

	def isEquivalent(self, other):
		""" 'equivalent' arguments are consistent and have been assigned the same name """

		if not super(Argument, self).isEquivalent(other):
			if self.typ not in other.p_types and other.typ not in self.p_types:
				return False

		if self.name is not None:
			if other.name != self.name:
				return False
		else:
			if other.name is not None:
				return False
		return True

	def isConsistentType(self, other):
		if not isinstance(other, Argument):
			return False
		if not self.typ == other.typ:
			return False
		if self.typ not in other.p_types and other.typ not in self.p_types:
			return False
		return True

	def isConsistent(self, other):
		if not super(Argument, self).isConsistent(other):
			return False
		return True

	def merge(self, other):
		if super(Argument, self).merge(other) is None:
			return None
		if self.typ in other.p_types:
			self.typ = other.typ
		return self

	def __repr__(self):
		shrt_id = str(self.ID)[19:23]
		if self.arg_name is None:
			arg_name = ''
		else:
			arg_name = '-' + self.arg_name
		if self.name is None:
			name = ''
		else:
			name = '-' + self.name
		return 'arg-{}-{}{}{}'.format(shrt_id, self.typ, name, arg_name)


class Actor(Argument):
	""" An actor is an argument """

	def __init__(self, ID=None, typ=None, name=None, arg_name=None):
		if typ is None:
			typ = 'character'
		super(Actor, self).__init__(ID, typ, name, arg_name)

	def merge(self, other):
		if super(Actor, self).merge(other) is None:
			return None

		return self

	def __repr__(self):
		shrt_id = str(self.ID)[19:23]
		if self.arg_name is None:
			arg_name = ''
		else:
			arg_name = '-' + self.arg_name
		if self.name is None:
			name = ''
		else:
			name = '-' + self.name
		return 'actor-{}-{}{}{}'.format(shrt_id, self.typ, name, arg_name)


class PlanElement(Element):
	def __init__(self, ID=None, typ=None, name=None, arg_name=None):
		if typ is None:
			typ = 'PlanElementGraph'

		super(PlanElement, self).__init__(ID, typ, name, arg_name)