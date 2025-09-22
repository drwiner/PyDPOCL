"""Tests for plan representation."""

import pytest
from uuid import uuid4

from pydpocl.core.plan import (
    Plan,
    create_initial_plan,
    create_empty_plan,
)
from pydpocl.core.step import GroundStep, create_initial_step, create_goal_step
from pydpocl.core.literal import create_literal
from pydpocl.core.flaw import OpenConditionFlaw, create_open_condition_flaw
from pydpocl.core.types import SearchStatus, OperatorName


class TestPlan:
    """Test cases for the Plan class."""

    def test_empty_plan_creation(self):
        """Test creating an empty plan."""
        plan = create_empty_plan("test")

        assert plan.name == "test"
        assert len(plan.steps) == 0
        assert len(plan.orderings) == 0
        assert len(plan.causal_links) == 0
        assert len(plan.flaws) == 0
        assert plan.cost == 0.0
        assert plan.status == SearchStatus.PENDING

    def test_initial_plan_creation(self):
        """Test creating an initial plan."""
        initial_state = {
            create_literal("at", "robot", "room1"),
            create_literal("adjacent", "room1", "room2"),
        }
        goal_state = {
            create_literal("at", "robot", "room2"),
        }

        plan = create_initial_plan(initial_state, goal_state, "initial")

        assert plan.name == "initial"
        assert len(plan.steps) == 2  # Initial and goal steps
        assert len(plan.orderings) == 1  # Initial before goal
        assert len(plan.flaws) == len(goal_state)  # One flaw per goal condition

        # Check that we have initial and goal steps
        initial_step = plan.initial_step
        goal_step = plan.goal_step

        assert initial_step is not None
        assert goal_step is not None
        assert initial_step.name == "__INITIAL__"
        assert goal_step.name == "__GOAL__"

    def test_plan_properties(self):
        """Test plan properties."""
        plan = create_empty_plan()

        assert plan.is_complete is True  # No flaws
        assert plan.is_consistent is True  # No cycles

        # Add some flaws
        step = GroundStep(name=OperatorName("test"))
        flaw = create_open_condition_flaw(step, create_literal("test"))
        plan_with_flaws = plan.add_flaws({flaw})

        assert plan_with_flaws.is_complete is False

    def test_add_step(self):
        """Test adding steps to a plan."""
        plan = create_empty_plan()

        step = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
            _preconditions=frozenset([create_literal("at", "robot", "room1")]),
            _effects=frozenset([create_literal("at", "robot", "room2")]),
        )

        new_plan = plan.add_step(step)

        assert len(new_plan.steps) == 1
        assert step in new_plan.steps
        assert new_plan.cost == plan.cost + 1.0
        assert len(new_plan.flaws) == 1  # Flaw for unsatisfied precondition

    def test_add_ordering(self):
        """Test adding ordering constraints."""
        step1 = GroundStep(name=OperatorName("step1"))
        step2 = GroundStep(name=OperatorName("step2"))

        plan = Plan(steps=frozenset([step1, step2]))

        new_plan = plan.add_ordering(step1.step_id, step2.step_id)

        assert (step1.step_id, step2.step_id) in new_plan.orderings
        assert new_plan.has_ordering(step1.step_id, step2.step_id) is True

    def test_causal_links(self):
        """Test adding causal links."""
        source = GroundStep(
            name=OperatorName("pickup"),
            _effects=frozenset([create_literal("holding", "robot", "block")]),
        )
        target = GroundStep(
            name=OperatorName("move"),
            _preconditions=frozenset([create_literal("holding", "robot", "block")]),
        )

        # Create plan with a flaw for the target's precondition
        condition = create_literal("holding", "robot", "block")
        flaw = create_open_condition_flaw(target, condition)
        plan = Plan(
            steps=frozenset([source, target]),
            flaws=frozenset([flaw]),
        )

        new_plan = plan.add_causal_link(source, target, condition)

        assert len(new_plan.causal_links) == 1
        assert len(new_plan.flaws) == 0  # Flaw should be resolved
        assert new_plan.has_ordering(source.step_id, target.step_id) is True

    def test_topological_order(self):
        """Test topological ordering of steps."""
        step1 = GroundStep(name=OperatorName("step1"))
        step2 = GroundStep(name=OperatorName("step2"))
        step3 = GroundStep(name=OperatorName("step3"))

        plan = Plan(
            steps=frozenset([step1, step2, step3]),
            orderings=frozenset([
                (step1.step_id, step2.step_id),
                (step2.step_id, step3.step_id),
            ]),
        )

        ordered_steps = plan.topological_order()

        # Should be in dependency order
        step1_index = ordered_steps.index(step1)
        step2_index = ordered_steps.index(step2)
        step3_index = ordered_steps.index(step3)

        assert step1_index < step2_index < step3_index

    def test_flaw_selection(self):
        """Test flaw selection by priority."""
        step = GroundStep(name=OperatorName("test"))

        high_priority_flaw = create_open_condition_flaw(
            step, create_literal("important")
        )
        high_priority_flaw = high_priority_flaw.__class__(
            step=high_priority_flaw.step,
            condition=high_priority_flaw.condition,
            priority=10.0,
        )

        low_priority_flaw = create_open_condition_flaw(
            step, create_literal("less_important")
        )
        low_priority_flaw = low_priority_flaw.__class__(
            step=low_priority_flaw.step,
            condition=low_priority_flaw.condition,
            priority=1.0,
        )

        plan = Plan(flaws=frozenset([low_priority_flaw, high_priority_flaw]))

        selected_flaw = plan.select_flaw()
        assert selected_flaw == high_priority_flaw

    def test_plan_validation(self):
        """Test plan validation."""
        # Valid plan
        plan = create_empty_plan()
        issues = plan.validate()
        assert len(issues) == 0

        # Plan with flaws
        step = GroundStep(name=OperatorName("test"))
        flaw = create_open_condition_flaw(step, create_literal("test"))
        plan_with_flaws = plan.add_flaws({flaw})

        issues = plan_with_flaws.validate()
        assert any("flaws" in issue for issue in issues)

    def test_execution_sequence(self):
        """Test converting plan to execution sequence."""
        step1 = GroundStep(name=OperatorName("move"))
        step2 = GroundStep(name=OperatorName("pickup"))
        initial = create_initial_step({create_literal("start")})
        goal = create_goal_step({create_literal("goal")})

        plan = Plan(
            steps=frozenset([initial, step1, step2, goal]),
            orderings=frozenset([
                (initial.step_id, step1.step_id),
                (step1.step_id, step2.step_id),
                (step2.step_id, goal.step_id),
            ]),
        )

        sequence = plan.to_execution_sequence()

        # Should exclude dummy steps (initial/goal)
        assert len(sequence) == 2
        assert step1 in sequence
        assert step2 in sequence
        assert initial not in sequence
        assert goal not in sequence

    def test_plan_copying(self):
        """Test plan copying with modifications."""
        original = create_empty_plan("original")

        copy = original.copy_with_name("_copy")
        assert copy.name == "original_copy"
        assert copy.id != original.id

        # Test copying with other modifications
        step = GroundStep(name=OperatorName("test"))
        modified = original._copy_with(
            steps=frozenset([step]),
            cost=5.0,
        )

        assert len(modified.steps) == 1
        assert modified.cost == 5.0
        assert modified.name == original.name  # Unchanged

    def test_plan_equality_and_ordering(self):
        """Test plan equality and ordering."""
        plan1 = create_empty_plan()
        plan2 = create_empty_plan()

        # Different instances should not be equal
        assert plan1 != plan2
        assert plan1.id != plan2.id

        # Same instance should equal itself
        assert plan1 == plan1

        # Test ordering (for priority queues)
        expensive_plan = plan1._copy_with(cost=10.0)
        cheap_plan = plan1._copy_with(cost=5.0)

        assert cheap_plan < expensive_plan

    def test_plan_containment_and_iteration(self):
        """Test plan containment and iteration."""
        step1 = GroundStep(name=OperatorName("step1"))
        step2 = GroundStep(name=OperatorName("step2"))

        plan = Plan(steps=frozenset([step1, step2]))

        assert step1 in plan
        assert step2 in plan
        assert len(plan) == 2

        steps_from_iteration = list(plan)
        assert len(steps_from_iteration) == 2
        assert step1 in steps_from_iteration
        assert step2 in steps_from_iteration


if __name__ == "__main__":
    pytest.main([__file__])