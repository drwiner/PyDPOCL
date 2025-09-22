"""Flaw representation for PyDPOCL planning system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydpocl.core.literal import Literal
from pydpocl.core.types import (
    FlawId,
    FlawType,
    Identifiable,
    LinkId,
)

if TYPE_CHECKING:
    from pydpocl.core.step import Step


@dataclass(frozen=True, slots=True)
class Flaw(Identifiable, ABC):
    """Abstract base class for planning flaws.

    A flaw represents something wrong with a partial plan that needs
    to be resolved to make progress toward a complete solution.
    """

    priority: float = field(default=0.0, compare=False)
    level: int = field(default=0, compare=False)  # For hierarchical planning
    _id: UUID | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Initialize the unique identifier after creation."""
        if self._id is None:
            object.__setattr__(self, "_id", uuid4())

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this flaw."""
        return self._id or uuid4()

    @property
    def flaw_id(self) -> FlawId:
        """Return the typed flaw identifier."""
        return FlawId(self.id)

    @property
    @abstractmethod
    def flaw_type(self) -> FlawType:
        """Return the type of this flaw."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of this flaw."""
        ...

    @abstractmethod
    def compute_priority(self, plan: Plan) -> float:
        """Compute the priority of this flaw in the given plan context."""
        ...

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Check equality based on unique identifier."""
        if not isinstance(other, Flaw):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other: object) -> bool:
        """Define ordering for flaws (higher priority first)."""
        if not isinstance(other, Flaw):
            return NotImplemented
        # Higher priority flaws are "smaller" (come first in sorted order)
        return self.priority > other.priority

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.flaw_type.name}: {self.description}"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"priority={self.priority}, level={self.level})"
        )


@dataclass(frozen=True, slots=True)
class OpenConditionFlaw(Flaw):
    """A flaw representing an unsatisfied precondition.

    This occurs when a step has a precondition that is not yet
    satisfied by any causal link in the plan.
    """

    step: Step
    condition: Literal
    priority: float = field(default=0.0, compare=False)
    level: int = field(default=0, compare=False)
    _id: UUID | None = field(default=None, compare=False)

    @property
    def flaw_type(self) -> FlawType:
        """Return the type of this flaw."""
        return FlawType.OPEN_CONDITION

    @property
    def description(self) -> str:
        """Return a human-readable description of this flaw."""
        return f"Step {self.step.signature} needs {self.condition.signature}"

    def compute_priority(self, plan: Plan) -> float:
        """Compute the priority based on various factors."""
        # Base priority calculation
        base_priority = 1.0

        # Static conditions have lower priority
        if self.condition.is_static:
            base_priority *= 0.1

        # Consider the number of possible resolvers
        # (This would be computed based on available steps)
        # For now, use a simple heuristic based on predicate complexity
        predicate_complexity = len(self.condition.predicate) + self.condition.arity
        base_priority += predicate_complexity * 0.1

        # Hierarchical planning: higher level flaws have higher priority
        if self.level > 0:
            base_priority *= (1.0 + self.level * 0.2)

        return base_priority

    def can_be_resolved_by(self, step: Step) -> bool:
        """Check if the given step can resolve this flaw."""
        return step.supports(self.condition)


@dataclass(frozen=True, slots=True)
class CausalLink:
    """Represents a causal link between two steps."""

    source: Step
    target: Step
    condition: Literal
    _id: UUID | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Initialize the unique identifier after creation."""
        if self._id is None:
            object.__setattr__(self, "_id", uuid4())

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this link."""
        return self._id or uuid4()

    @property
    def link_id(self) -> LinkId:
        """Return the typed link identifier."""
        return LinkId(self.id)

    def is_threatened_by(self, step: Step) -> bool:
        """Check if this causal link is threatened by the given step."""
        return step.threatens(self.condition)

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash((self.source.id, self.target.id, self.condition))

    def __eq__(self, other: object) -> bool:
        """Check equality based on source, target, and condition."""
        if not isinstance(other, CausalLink):
            return NotImplemented
        return (
            self.source.id == other.source.id
            and self.target.id == other.target.id
            and self.condition == other.condition
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return (
            f"{self.source.signature} --[{self.condition.signature}]--> "
            f"{self.target.signature}"
        )


@dataclass(frozen=True, slots=True)
class ThreatenedLinkFlaw(Flaw):
    """A flaw representing a threatened causal link.

    This occurs when a step could potentially interfere with
    a causal link by producing a conflicting effect.
    """

    threatening_step: Step
    threatened_link: CausalLink
    priority: float = field(default=0.0, compare=False)
    level: int = field(default=0, compare=False)
    _id: UUID | None = field(default=None, compare=False)

    @property
    def flaw_type(self) -> FlawType:
        """Return the type of this flaw."""
        return FlawType.THREATENED_LINK

    @property
    def description(self) -> str:
        """Return a human-readable description of this flaw."""
        return (
            f"Step {self.threatening_step.signature} threatens "
            f"link {self.threatened_link}"
        )

    def compute_priority(self, plan: Plan) -> float:
        """Compute the priority based on threat severity."""
        # Base priority for threatened links
        base_priority = 2.0  # Generally higher than open conditions

        # Consider the importance of the threatened condition
        if self.threatened_link.condition.is_static:
            base_priority *= 0.5  # Static conditions are less critical

        # Consider the number of alternatives for resolution
        # (promotion vs demotion)
        base_priority += 0.5  # Base for having options

        return base_priority


@dataclass(frozen=True, slots=True)
class DecompositionFlaw(Flaw):
    """A flaw representing a hierarchical step that needs decomposition."""

    hierarchical_step: Step
    priority: float = field(default=0.0, compare=False)
    level: int = field(default=0, compare=False)
    _id: UUID | None = field(default=None, compare=False)

    @property
    def flaw_type(self) -> FlawType:
        """Return the type of this flaw."""
        return FlawType.DECOMPOSITION

    @property
    def description(self) -> str:
        """Return a human-readable description of this flaw."""
        return f"Step {self.hierarchical_step.signature} needs decomposition"

    def compute_priority(self, plan: Plan) -> float:
        """Compute the priority based on decomposition urgency."""
        # Decomposition flaws typically have high priority
        base_priority = 3.0

        # Higher-level abstractions get higher priority
        base_priority += self.hierarchical_step.height * 0.5

        return base_priority


# Utility functions for flaw management

def create_open_condition_flaw(
    step: Step,
    condition: Literal,
    level: int = 0,
) -> OpenConditionFlaw:
    """Create an open condition flaw with computed priority."""

    flaw = OpenConditionFlaw(
        step=step,
        condition=condition,
        level=level,
    )

    # Set priority based on a dummy plan context
    # In practice, this would be computed when the flaw is added to a plan
    object.__setattr__(flaw, "priority", flaw.compute_priority(None))

    return flaw


def create_threatened_link_flaw(
    threatening_step: Step,
    threatened_link: CausalLink,
    level: int = 0,
) -> ThreatenedLinkFlaw:
    """Create a threatened link flaw with computed priority."""

    flaw = ThreatenedLinkFlaw(
        threatening_step=threatening_step,
        threatened_link=threatened_link,
        level=level,
    )

    # Set priority based on a dummy plan context
    object.__setattr__(flaw, "priority", flaw.compute_priority(None))

    return flaw


def create_decomposition_flaw(
    hierarchical_step: Step,
    level: int = 0,
) -> DecompositionFlaw:
    """Create a decomposition flaw with computed priority."""

    flaw = DecompositionFlaw(
        hierarchical_step=hierarchical_step,
        level=level,
    )

    # Set priority based on a dummy plan context
    object.__setattr__(flaw, "priority", flaw.compute_priority(None))

    return flaw
