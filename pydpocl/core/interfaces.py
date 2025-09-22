"""Core interfaces and protocols for PyDPOCL planning system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, Sequence
from typing import Generic, Protocol, TypeVar

# Forward declarations for type hints
Plan = TypeVar("Plan")
Step = TypeVar("Step")
Flaw = TypeVar("Flaw")
Literal = TypeVar("Literal")
Solution = TypeVar("Solution")

class PlanningProblem(Protocol):
    """Interface for planning problems."""

    @property
    def initial_state(self) -> set[Literal]:
        """Return the initial state literals."""
        ...

    @property
    def goal_state(self) -> set[Literal]:
        """Return the goal state literals."""
        ...

    @property
    def operators(self) -> Sequence[Step]:
        """Return available operators."""
        ...

    def is_goal_satisfied(self, state: set[Literal]) -> bool:
        """Check if the goal is satisfied in the given state."""
        ...

class SearchStrategy(Protocol, Generic[Plan]):
    """Interface for search strategies."""

    def select_plan(self, frontier: Collection[Plan]) -> Plan | None:
        """Select the next plan to expand from the frontier."""
        ...

    def add_plans(self, plans: Sequence[Plan]) -> None:
        """Add new plans to the search frontier."""
        ...

    @property
    def is_empty(self) -> bool:
        """Return True if the frontier is empty."""
        ...

class Heuristic(Protocol, Generic[Plan]):
    """Interface for planning heuristics."""

    def estimate_cost(self, plan: Plan) -> float:
        """Estimate the cost to complete the given plan."""
        ...

    def compare_plans(self, plan1: Plan, plan2: Plan) -> int:
        """Compare two plans (-1 if plan1 < plan2, 0 if equal, 1 if plan1 > plan2)."""
        ...

class FlawResolver(Protocol, Generic[Plan, Flaw]):
    """Interface for flaw resolution strategies."""

    def can_resolve(self, flaw: Flaw) -> bool:
        """Check if this resolver can handle the given flaw type."""
        ...

    def resolve(self, plan: Plan, flaw: Flaw) -> Iterator[Plan]:
        """Generate all possible ways to resolve the flaw in the plan."""
        ...

class PlanValidator(Protocol, Generic[Plan]):
    """Interface for plan validation."""

    def is_valid(self, plan: Plan) -> bool:
        """Check if the plan is valid (consistent and complete)."""
        ...

    def find_violations(self, plan: Plan) -> Iterator[str]:
        """Find and yield all validation violations in the plan."""
        ...

class PlanExecutor(Protocol, Generic[Plan]):
    """Interface for plan execution."""

    def execute(self, plan: Plan) -> Iterator[Step]:
        """Execute the plan and yield steps in execution order."""
        ...

    def can_execute(self, plan: Plan) -> bool:
        """Check if the plan can be executed."""
        ...

# Abstract base classes for core components

class BasePlanner(ABC, Generic[Plan, Solution]):
    """Abstract base class for planners."""

    @abstractmethod
    def solve(
        self,
        problem: PlanningProblem,
        max_solutions: int = 1,
        timeout: float | None = None,
    ) -> Iterator[Solution]:
        """Solve the planning problem and yield solutions."""
        ...

    @abstractmethod
    def get_statistics(self) -> dict:
        """Return planning statistics."""
        ...

class BaseSearchNode(ABC, Generic[Plan]):
    """Abstract base class for search nodes."""

    @property
    @abstractmethod
    def plan(self) -> Plan:
        """Return the plan associated with this node."""
        ...

    @property
    @abstractmethod
    def cost(self) -> float:
        """Return the cost of this node."""
        ...

    @property
    @abstractmethod
    def heuristic_value(self) -> float:
        """Return the heuristic value for this node."""
        ...

    @property
    def f_value(self) -> float:
        """Return the f-value (cost + heuristic) for this node."""
        return self.cost + self.heuristic_value

    @abstractmethod
    def expand(self) -> Iterator[BaseSearchNode[Plan]]:
        """Expand this node and yield child nodes."""
        ...

class BaseFlawSelector(ABC, Generic[Flaw]):
    """Abstract base class for flaw selection strategies."""

    @abstractmethod
    def select_flaw(self, flaws: Collection[Flaw]) -> Flaw | None:
        """Select the next flaw to resolve."""
        ...

    @abstractmethod
    def priority(self, flaw: Flaw) -> float:
        """Return the priority of the given flaw."""
        ...

# Event system interfaces

class PlanningEvent(Protocol):
    """Interface for planning events."""

    @property
    def event_type(self) -> str:
        """Return the type of this event."""
        ...

    @property
    def timestamp(self) -> float:
        """Return when this event occurred."""
        ...

class EventListener(Protocol):
    """Interface for planning event listeners."""

    def handle_event(self, event: PlanningEvent) -> None:
        """Handle a planning event."""
        ...

class EventEmitter(Protocol):
    """Interface for objects that emit planning events."""

    def add_listener(self, listener: EventListener) -> None:
        """Add an event listener."""
        ...

    def remove_listener(self, listener: EventListener) -> None:
        """Remove an event listener."""
        ...

    def emit_event(self, event: PlanningEvent) -> None:
        """Emit an event to all listeners."""
        ...
