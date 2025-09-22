"""Step representation for PyDPOCL planning system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
)
from uuid import UUID, uuid4

from pydpocl.core.literal import Literal
from pydpocl.core.types import (
    Grounded,
    Identifiable,
    ObjectName,
    OperatorName,
    StepId,
)

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Step(Identifiable, Grounded, ABC):
    """Abstract base class for planning steps.

    A step represents an action that can be executed in a plan.
    This is an immutable data structure for thread safety and efficiency.
    """

    name: OperatorName
    parameters: tuple[str, ...] = field(default_factory=tuple)
    _id: UUID | None = field(default=None, compare=False)
    height: int = 0  # 0 for primitive, >0 for hierarchical
    depth: int = 0  # depth in the plan hierarchy

    def __post_init__(self) -> None:
        """Initialize the unique identifier after creation."""
        if self._id is None:
            object.__setattr__(self, "_id", uuid4())

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this step."""
        return self._id or uuid4()

    @property
    def step_id(self) -> StepId:
        """Return the typed step identifier."""
        return StepId(self.id)

    @property
    @abstractmethod
    def preconditions(self) -> frozenset[Literal]:
        """Return the preconditions of this step."""
        ...

    @property
    @abstractmethod
    def effects(self) -> frozenset[Literal]:
        """Return the effects of this step."""
        ...

    @property
    def is_grounded(self) -> bool:
        """Return True if this step is fully grounded (no variables)."""
        return all(not param.startswith("?") for param in self.parameters)

    @property
    def is_primitive(self) -> bool:
        """Return True if this is a primitive step."""
        return self.height == 0

    @property
    def is_hierarchical(self) -> bool:
        """Return True if this is a hierarchical step."""
        return self.height > 0

    @property
    def signature(self) -> str:
        """Return a string signature for this step."""
        if self.parameters:
            params_str = ", ".join(self.parameters)
            return f"{self.name}({params_str})"
        return str(self.name)

    @abstractmethod
    def substitute(self, substitution: dict[str, str]) -> Step:
        """Apply a substitution to this step."""
        ...

    @abstractmethod
    def unify(self, other: Step) -> dict[str, str] | None:
        """Attempt to unify this step with another."""
        ...

    def conflicts_with(self, other: Step) -> bool:
        """Check if this step conflicts with another step."""
        # Two steps conflict if their effects contradict
        for effect1 in self.effects:
            for effect2 in other.effects:
                if effect1.conflicts_with(effect2):
                    return True
        return False

    def threatens(self, link_condition: Literal) -> bool:
        """Check if this step threatens a causal link condition."""
        return any(effect.conflicts_with(link_condition) for effect in self.effects)

    def supports(self, condition: Literal) -> bool:
        """Check if this step can support a given condition."""
        return any(effect == condition for effect in self.effects)

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return self.signature

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"parameters={self.parameters!r}, id={self.id}, "
            f"height={self.height}, depth={self.depth})"
        )

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Check equality based on unique identifier."""
        if not isinstance(other, Step):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other: object) -> bool:
        """Define ordering for steps."""
        if not isinstance(other, Step):
            return NotImplemented
        # Order by name, then parameters
        return (self.name, self.parameters) < (other.name, other.parameters)


@dataclass(frozen=True, slots=True)
class GroundStep(Step):
    """Concrete implementation of a ground step.

    A ground step is a fully instantiated action with specific
    preconditions and effects.
    """

    _preconditions: frozenset[Literal] = field(default_factory=frozenset)
    _effects: frozenset[Literal] = field(default_factory=frozenset)
    step_number: int = 0  # For compatibility with legacy code
    instantiable: bool = True

    @property
    def preconditions(self) -> frozenset[Literal]:
        """Return the preconditions of this step."""
        return self._preconditions

    @property
    def effects(self) -> frozenset[Literal]:
        """Return the effects of this step."""
        return self._effects

    @property
    def open_preconditions(self) -> frozenset[Literal]:
        """Return preconditions that are not yet satisfied."""
        # In a full implementation, this would track which preconditions
        # are already satisfied by causal links
        return self._preconditions

    def substitute(self, substitution: dict[str, str]) -> GroundStep:
        """Apply a substitution to this step."""
        new_parameters = tuple(
            substitution.get(param, param) for param in self.parameters
        )

        # Convert substitution to ObjectName values for Literal.substitute
        literal_substitution = {k: ObjectName(v) for k, v in substitution.items()}

        new_preconditions = frozenset(
            precond.substitute(literal_substitution) for precond in self._preconditions
        )

        new_effects = frozenset(
            effect.substitute(literal_substitution) for effect in self._effects
        )

        return GroundStep(
            name=self.name,
            parameters=new_parameters,
            _preconditions=new_preconditions,
            _effects=new_effects,
            height=self.height,
            depth=self.depth,
            step_number=self.step_number,
            instantiable=self.instantiable,
        )

    def unify(self, other: Step) -> dict[str, str] | None:
        """Attempt to unify this step with another."""
        if not isinstance(other, GroundStep):
            return None

        if self.name != other.name:
            return None

        if len(self.parameters) != len(other.parameters):
            return None

        substitution: dict[str, str] = {}

        # Unify parameters
        for param1, param2 in zip(self.parameters, other.parameters, strict=False):
            if param1.startswith("?") and param2.startswith("?"):
                if param1 in substitution:
                    if substitution[param1] != param2:
                        return None
                else:
                    substitution[param1] = param2
            elif param1.startswith("?"):
                if param1 in substitution:
                    if substitution[param1] != param2:
                        return None
                else:
                    substitution[param1] = param2
            elif param2.startswith("?"):
                if param2 in substitution:
                    if substitution[param2] != param1:
                        return None
                else:
                    substitution[param2] = param1
            else:
                if param1 != param2:
                    return None

        return substitution

    def copy_with(
        self,
        name: OperatorName | None = None,
        parameters: tuple[str, ...] | None = None,
        preconditions: frozenset[Literal] | None = None,
        effects: frozenset[Literal] | None = None,
        **kwargs,
    ) -> GroundStep:
        """Create a copy of this step with modified attributes."""
        return GroundStep(
            name=name or self.name,
            parameters=parameters or self.parameters,
            _preconditions=preconditions or self._preconditions,
            _effects=effects or self._effects,
            height=kwargs.get("height", self.height),
            depth=kwargs.get("depth", self.depth),
            step_number=kwargs.get("step_number", self.step_number),
            instantiable=kwargs.get("instantiable", self.instantiable),
            _id=kwargs.get("_id", uuid4()),  # New ID for copy
        )


@dataclass(frozen=True, slots=True)
class HierarchicalStep(Step):
    """A hierarchical step that decomposes into sub-steps."""

    _preconditions: frozenset[Literal] = field(default_factory=frozenset)
    _effects: frozenset[Literal] = field(default_factory=frozenset)
    sub_steps: tuple[Step, ...] = field(default_factory=tuple)
    sub_orderings: frozenset[tuple[StepId, StepId]] = field(default_factory=frozenset)
    sub_links: frozenset[tuple[StepId, StepId, Literal]] = field(default_factory=frozenset)

    @property
    def preconditions(self) -> frozenset[Literal]:
        """Return the preconditions of this step."""
        return self._preconditions

    @property
    def effects(self) -> frozenset[Literal]:
        """Return the effects of this step."""
        return self._effects

    def substitute(self, substitution: dict[str, str]) -> HierarchicalStep:
        """Apply a substitution to this step."""
        new_parameters = tuple(
            substitution.get(param, param) for param in self.parameters
        )

        # Convert substitution to ObjectName values for Literal.substitute
        literal_substitution = {k: ObjectName(v) for k, v in substitution.items()}

        new_preconditions = frozenset(
            precond.substitute(literal_substitution) for precond in self._preconditions
        )

        new_effects = frozenset(
            effect.substitute(literal_substitution) for effect in self._effects
        )

        new_sub_steps = tuple(
            sub_step.substitute(substitution) for sub_step in self.sub_steps
        )

        return HierarchicalStep(
            name=self.name,
            parameters=new_parameters,
            _preconditions=new_preconditions,
            _effects=new_effects,
            sub_steps=new_sub_steps,
            sub_orderings=self.sub_orderings,
            sub_links=self.sub_links,
            height=self.height,
            depth=self.depth,
        )

    def unify(self, other: Step) -> dict[str, str] | None:
        """Attempt to unify this step with another."""
        if not isinstance(other, HierarchicalStep):
            return None

        if self.name != other.name:
            return None

        if len(self.parameters) != len(other.parameters):
            return None

        substitution: dict[str, str] = {}

        # Unify parameters (same logic as GroundStep)
        for param1, param2 in zip(self.parameters, other.parameters, strict=False):
            if param1.startswith("?") and param2.startswith("?"):
                if param1 in substitution:
                    if substitution[param1] != param2:
                        return None
                else:
                    substitution[param1] = param2
            elif param1.startswith("?"):
                if param1 in substitution:
                    if substitution[param1] != param2:
                        return None
                else:
                    substitution[param1] = param2
            elif param2.startswith("?"):
                if param2 in substitution:
                    if substitution[param2] != param1:
                        return None
                else:
                    substitution[param2] = param1
            else:
                if param1 != param2:
                    return None

        return substitution


# Special step types for planning
def create_initial_step(initial_state: set[Literal]) -> GroundStep:
    """Create the initial step with the given initial state."""
    return GroundStep(
        name=OperatorName("__INITIAL__"),
        parameters=(),
        _preconditions=frozenset(),
        _effects=frozenset(initial_state),
        height=0,
        depth=0,
        step_number=-1,
        instantiable=False,
    )


def create_goal_step(goal_state: set[Literal]) -> GroundStep:
    """Create the goal step with the given goal conditions."""
    return GroundStep(
        name=OperatorName("__GOAL__"),
        parameters=(),
        _preconditions=frozenset(goal_state),
        _effects=frozenset(),
        height=0,
        depth=0,
        step_number=-2,
        instantiable=False,
    )


def create_dummy_step(name: str) -> GroundStep:
    """Create a dummy step for hierarchical decomposition."""
    return GroundStep(
        name=OperatorName(f"__DUMMY_{name}__"),
        parameters=(),
        _preconditions=frozenset(),
        _effects=frozenset(),
        height=0,
        depth=0,
        instantiable=False,
    )
