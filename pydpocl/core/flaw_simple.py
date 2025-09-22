"""Simplified flaw representation without dataclass inheritance issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydpocl.core.literal import Literal
from pydpocl.core.types import (
    FlawId,
    FlawType,
    Identifiable,
)

if TYPE_CHECKING:
    from pydpocl.core.plan import Plan
    from pydpocl.core.step import Step


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
class OpenConditionFlaw(Identifiable):
    """A flaw representing an unsatisfied precondition."""

    step: Step
    condition: Literal
    priority: float = field(default=0.0, compare=False)
    level: int = field(default=0, compare=False)
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
    def flaw_type(self) -> FlawType:
        """Return the type of this flaw."""
        return FlawType.OPEN_CONDITION

    @property
    def description(self) -> str:
        """Return a human-readable description of this flaw."""
        return f"Step {self.step.signature} needs {self.condition.signature}"

    def compute_priority(self, plan: "Plan") -> float:
        """Compute the priority of this flaw in the given plan context."""
        base_priority = 1.0
        if self.condition.is_static:
            base_priority *= 0.1
        predicate_complexity = len(self.condition.predicate) + self.condition.arity
        base_priority += predicate_complexity * 0.1
        if self.level > 0:
            base_priority *= (1.0 + self.level * 0.2)
        return base_priority

    def can_be_resolved_by(self, step: Step) -> bool:
        """Check if the given step can resolve this flaw."""
        return step.supports(self.condition)

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Check equality based on unique identifier."""
        if not isinstance(other, OpenConditionFlaw):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other: object) -> bool:
        """Define ordering for flaws (higher priority first)."""
        if not isinstance(other, OpenConditionFlaw):
            return NotImplemented
        return self.priority > other.priority

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.flaw_type.name}: {self.description}"


# Simplified factory function
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

    # Set priority based on computation
    priority = flaw.compute_priority(None)
    object.__setattr__(flaw, "priority", priority)

    return flaw
