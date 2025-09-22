"""Plan representation for PyDPOCL planning system."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
)
from uuid import UUID, uuid4

import networkx as nx

from pydpocl.core.flaw_simple import (
    CausalLink,
    OpenConditionFlaw,
    create_open_condition_flaw,
)
from pydpocl.core.literal import Literal
from pydpocl.core.step import Step, create_goal_step, create_initial_step
from pydpocl.core.types import (
    Identifiable,
    PlanId,
    SearchStatus,
    StepId,
)

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Plan(Identifiable):
    """Immutable representation of a partial plan.

    A plan consists of steps, ordering constraints, causal links,
    and flaws that need to be resolved. This implementation uses
    immutable data structures for efficiency and thread safety.
    """

    steps: frozenset[Step] = field(default_factory=frozenset)
    orderings: frozenset[tuple[StepId, StepId]] = field(default_factory=frozenset)
    causal_links: frozenset[CausalLink] = field(default_factory=frozenset)
    flaws: frozenset[OpenConditionFlaw] = field(default_factory=frozenset)

    # Plan metadata
    _id: UUID | None = field(default=None, compare=False)
    cost: float = field(default=0.0, compare=False)
    depth: int = field(default=0, compare=False)
    name: str = field(default="", compare=False)
    status: SearchStatus = field(default=SearchStatus.PENDING, compare=False)

    # Cached graphs for efficiency
    _ordering_graph: nx.DiGraph | None = field(default=None, init=False, compare=False)
    _step_lookup: dict[StepId, Step] | None = field(default=None, init=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize computed fields after creation."""
        if self._id is None:
            object.__setattr__(self, "_id", uuid4())

        # Build step lookup dictionary
        step_lookup = {step.step_id: step for step in self.steps}
        object.__setattr__(self, "_step_lookup", step_lookup)

        # Build ordering graph
        ordering_graph = nx.DiGraph()
        ordering_graph.add_nodes_from(step.step_id for step in self.steps)
        ordering_graph.add_edges_from(self.orderings)
        object.__setattr__(self, "_ordering_graph", ordering_graph)

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this plan."""
        return self._id or uuid4()

    @property
    def plan_id(self) -> PlanId:
        """Return the typed plan identifier."""
        return PlanId(self.id)

    @property
    def ordering_graph(self) -> nx.DiGraph:
        """Return the ordering constraint graph."""
        if self._ordering_graph is None:
            # This shouldn't happen due to __post_init__, but just in case
            ordering_graph = nx.DiGraph()
            ordering_graph.add_nodes_from(step.step_id for step in self.steps)
            ordering_graph.add_edges_from(self.orderings)
            return ordering_graph
        return self._ordering_graph

    @property
    def step_lookup(self) -> dict[StepId, Step]:
        """Return the step lookup dictionary."""
        if self._step_lookup is None:
            # This shouldn't happen due to __post_init__, but just in case
            return {step.step_id: step for step in self.steps}
        return self._step_lookup

    @property
    def is_complete(self) -> bool:
        """Return True if this plan has no flaws."""
        return len(self.flaws) == 0

    @property
    def is_consistent(self) -> bool:
        """Return True if this plan is internally consistent."""
        # Check for cycles in ordering constraints
        if not nx.is_directed_acyclic_graph(self.ordering_graph):
            return False

        # Check for conflicting causal links
        # (Implementation would check for threats that aren't resolved)
        return True

    @property
    def initial_step(self) -> Step | None:
        """Return the initial step if present."""
        for step in self.steps:
            if step.name == "__INITIAL__":
                return step
        return None

    @property
    def goal_step(self) -> Step | None:
        """Return the goal step if present."""
        for step in self.steps:
            if step.name == "__GOAL__":
                return step
        return None

    def get_step(self, step_id: StepId) -> Step | None:
        """Get a step by its ID."""
        return self.step_lookup.get(step_id)

    def has_ordering(self, before: StepId, after: StepId) -> bool:
        """Check if there's an ordering constraint between two steps."""
        return (before, after) in self.orderings

    def has_path(self, source: StepId, target: StepId) -> bool:
        """Check if there's a path from source to target in the ordering graph."""
        try:
            return nx.has_path(self.ordering_graph, source, target)
        except nx.NodeNotFound:
            return False

    def topological_order(self) -> list[Step]:
        """Return steps in topological order based on ordering constraints."""
        try:
            ordered_ids = list(nx.topological_sort(self.ordering_graph))
            return [self.step_lookup[step_id] for step_id in ordered_ids]
        except nx.NetworkXError:
            # Graph has cycles, return arbitrary order
            return list(self.steps)

    def add_step(
        self,
        step: Step,
        orderings: list[tuple[StepId, StepId]] | None = None,
    ) -> Plan:
        """Add a step to the plan with optional ordering constraints."""
        new_steps = self.steps | {step}
        new_orderings = self.orderings

        if orderings:
            new_orderings = new_orderings | set(orderings)

        # Add flaws for any open preconditions
        new_flaws = set(self.flaws)
        for precond in step.preconditions:
            if not self._is_condition_satisfied(precond):
                flaw = create_open_condition_flaw(step, precond)
                new_flaws.add(flaw)

        return self._copy_with(
            steps=frozenset(new_steps),
            orderings=frozenset(new_orderings),
            flaws=frozenset(new_flaws),
            cost=self.cost + 1.0,  # Simple cost increment
        )

    def add_ordering(self, before: StepId, after: StepId) -> Plan:
        """Add an ordering constraint to the plan."""
        if (before, after) in self.orderings:
            return self  # Already exists

        new_orderings = self.orderings | {(before, after)}
        return self._copy_with(orderings=new_orderings)

    def add_causal_link(
        self,
        source: Step,
        target: Step,
        condition: Literal,
    ) -> Plan:
        """Add a causal link to the plan."""
        link = CausalLink(source=source, target=target, condition=condition)
        new_links = self.causal_links | {link}

        # Remove the open condition flaw that this link satisfies
        new_flaws = set(self.flaws)
        for flaw in self.flaws:
            if (
                isinstance(flaw, OpenConditionFlaw)
                and flaw.step.id == target.id
                and flaw.condition == condition
            ):
                new_flaws.discard(flaw)
                break

        # Add ordering constraint: source must come before target
        new_orderings = self.orderings | {(source.step_id, target.step_id)}

        return self._copy_with(
            causal_links=frozenset(new_links),
            flaws=frozenset(new_flaws),
            orderings=frozenset(new_orderings),
        )

    def remove_flaw(self, flaw: OpenConditionFlaw) -> Plan:
        """Remove a flaw from the plan."""
        if flaw not in self.flaws:
            return self

        new_flaws = self.flaws - {flaw}
        return self._copy_with(flaws=frozenset(new_flaws))

    def add_flaws(self, flaws: set[OpenConditionFlaw]) -> Plan:
        """Add multiple flaws to the plan."""
        if not flaws:
            return self

        new_flaws = self.flaws | flaws
        return self._copy_with(flaws=frozenset(new_flaws))

    def select_flaw(self) -> OpenConditionFlaw | None:
        """Select the next flaw to resolve based on priority."""
        if not self.flaws:
            return None

        # Return the flaw with highest priority
        return max(self.flaws, key=lambda f: f.priority)

    def _is_condition_satisfied(self, condition: Literal) -> bool:
        """Check if a condition is satisfied by existing causal links."""
        for link in self.causal_links:
            if link.condition == condition:
                return True
        return False

    def _copy_with(self, **kwargs) -> Plan:
        """Create a copy of this plan with modified attributes."""
        current_values = {
            "steps": self.steps,
            "orderings": self.orderings,
            "causal_links": self.causal_links,
            "flaws": self.flaws,
            "cost": self.cost,
            "depth": self.depth,
            "name": self.name,
            "status": self.status,
        }

        current_values.update(kwargs)
        current_values["_id"] = uuid4()  # New ID for the copy

        return Plan(**current_values)

    def copy_with_name(self, name_suffix: str) -> Plan:
        """Create a copy with an extended name."""
        new_name = f"{self.name}{name_suffix}" if self.name else name_suffix
        return self._copy_with(name=new_name)

    def to_execution_sequence(self) -> list[Step]:
        """Convert the plan to a sequence of steps for execution."""
        return [
            step
            for step in self.topological_order()
            if not step.name.startswith("__")  # Exclude dummy steps
        ]

    def validate(self) -> list[str]:
        """Validate the plan and return a list of issues."""
        issues = []

        # Check for consistency
        if not self.is_consistent:
            issues.append("Plan contains cycles in ordering constraints")

        # Check for unresolved flaws
        if self.flaws:
            issues.append(f"Plan has {len(self.flaws)} unresolved flaws")

        # Check for orphaned steps
        initial = self.initial_step
        goal = self.goal_step
        if initial and goal:
            reachable_from_initial = set(nx.descendants(self.ordering_graph, initial.step_id))
            reachable_from_initial.add(initial.step_id)
            can_reach_goal = set(nx.ancestors(self.ordering_graph, goal.step_id))
            can_reach_goal.add(goal.step_id)

            connected_steps = reachable_from_initial & can_reach_goal
            all_step_ids = {step.step_id for step in self.steps}
            orphaned = all_step_ids - connected_steps

            if orphaned:
                issues.append(f"Plan has {len(orphaned)} orphaned steps")

        return issues

    def __len__(self) -> int:
        """Return the number of steps in the plan."""
        return len(self.steps)

    def __contains__(self, step: Step) -> bool:
        """Check if a step is in the plan."""
        return step in self.steps

    def __iter__(self) -> Iterator[Step]:
        """Iterate over steps in the plan."""
        return iter(self.steps)

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Check equality based on unique identifier."""
        if not isinstance(other, Plan):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other: object) -> bool:
        """Define ordering for plans (for use in priority queues)."""
        if not isinstance(other, Plan):
            return NotImplemented

        # Primary: cost + heuristic (f-value)
        # Secondary: cost (g-value)
        # Tertiary: number of flaws
        f_value_self = self.cost  # + heuristic would be added here
        f_value_other = other.cost  # + heuristic would be added here

        if f_value_self != f_value_other:
            return f_value_self < f_value_other
        elif self.cost != other.cost:
            return self.cost < other.cost
        elif len(self.flaws) != len(other.flaws):
            return len(self.flaws) < len(other.flaws)
        else:
            return self.id < other.id

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.name:
            return f"Plan[{self.name}]({len(self.steps)} steps, {len(self.flaws)} flaws)"
        return f"Plan({len(self.steps)} steps, {len(self.flaws)} flaws)"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"Plan(id={self.id}, steps={len(self.steps)}, "
            f"flaws={len(self.flaws)}, cost={self.cost}, "
            f"name={self.name!r}, status={self.status})"
        )


def create_initial_plan(
    initial_state: set[Literal],
    goal_state: set[Literal],
    name: str = "root",
) -> Plan:
    """Create an initial plan with only initial and goal steps."""
    initial_step = create_initial_step(initial_state)
    goal_step = create_goal_step(goal_state)

    steps = frozenset([initial_step, goal_step])

    # Add ordering: initial before goal
    orderings = frozenset([(initial_step.step_id, goal_step.step_id)])

    # Create flaws for all goal conditions
    flaws = set()
    for goal_condition in goal_state:
        flaw = create_open_condition_flaw(goal_step, goal_condition)
        flaws.add(flaw)

    return Plan(
        steps=steps,
        orderings=orderings,
        causal_links=frozenset(),
        flaws=frozenset(flaws),
        name=name,
        cost=0.0,
        depth=0,
        status=SearchStatus.PENDING,
    )


def create_empty_plan(name: str = "") -> Plan:
    """Create an empty plan with no steps."""
    return Plan(
        steps=frozenset(),
        orderings=frozenset(),
        causal_links=frozenset(),
        flaws=frozenset(),
        name=name,
        cost=0.0,
        depth=0,
        status=SearchStatus.PENDING,
    )
