"""Core type definitions for PyDPOCL."""

from __future__ import annotations

from typing import Generic, NewType, Protocol, TypeVar, runtime_checkable
from uuid import UUID

# Core identifiers
StepId = NewType("StepId", UUID)
PlanId = NewType("PlanId", UUID)
FlawId = NewType("FlawId", UUID)
LiteralId = NewType("LiteralId", UUID)
LinkId = NewType("LinkId", UUID)

# Domain types
ArgumentType = NewType("ArgumentType", str)
OperatorName = NewType("OperatorName", str)
PredicateName = NewType("PredicateName", str)
ObjectName = NewType("ObjectName", str)

# Generic type variables
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Protocols for core planning concepts
@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects with unique identifiers."""

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this object."""
        ...

@runtime_checkable
class Hashable(Protocol):
    """Protocol for hashable objects."""

    def __hash__(self) -> int:
        """Return hash value for the object."""
        ...

@runtime_checkable
class Comparable(Protocol):
    """Protocol for comparable objects."""

    def __lt__(self, other: object) -> bool:
        """Return True if self < other."""
        ...

@runtime_checkable
class Copyable(Protocol, Generic[T]):
    """Protocol for objects that can be copied."""

    def copy(self) -> T:
        """Return a copy of this object."""
        ...

# Planning-specific protocols
@runtime_checkable
class Grounded(Protocol):
    """Protocol for grounded planning objects."""

    @property
    def is_grounded(self) -> bool:
        """Return True if this object is fully grounded."""
        ...

@runtime_checkable
class Temporal(Protocol):
    """Protocol for objects with temporal properties."""

    @property
    def timestamp(self) -> float:
        """Return the timestamp for this object."""
        ...

# Constraint types
from enum import Enum, auto


class OrderingType(Enum):
    """Types of ordering constraints."""
    BEFORE = auto()
    AFTER = auto()
    SIMULTANEOUS = auto()

class FlawType(Enum):
    """Types of planning flaws."""
    OPEN_CONDITION = auto()
    THREATENED_LINK = auto()
    DECOMPOSITION = auto()

class SearchStatus(Enum):
    """Status of planning search."""
    PENDING = auto()
    EXPANDED = auto()
    SOLVED = auto()
    FAILED = auto()
    TIMEOUT = auto()
