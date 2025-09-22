"""Tests for step representation."""

import pytest
from uuid import uuid4

from pydpocl.core.step import (
    GroundStep,
    HierarchicalStep,
    create_initial_step,
    create_goal_step,
    OperatorName,
)
from pydpocl.core.literal import create_literal


class TestGroundStep:
    """Test cases for the GroundStep class."""

    def test_step_creation(self):
        """Test basic step creation."""
        preconditions = frozenset([
            create_literal("at", "robot", "room1"),
            create_literal("adjacent", "room1", "room2"),
        ])
        effects = frozenset([
            create_literal("at", "robot", "room2"),
            create_literal("at", "robot", "room1", positive=False),
        ])

        step = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
            _preconditions=preconditions,
            _effects=effects,
        )

        assert step.name == OperatorName("move")
        assert step.parameters == ("robot", "room1", "room2")
        assert step.preconditions == preconditions
        assert step.effects == effects
        assert step.is_primitive is True
        assert step.is_hierarchical is False

    def test_step_signature(self):
        """Test step string representations."""
        step = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
        )

        assert step.signature == "move(robot, room1, room2)"
        assert str(step) == "move(robot, room1, room2)"

        # Test step without parameters
        step_no_params = GroundStep(name=OperatorName("start"))
        assert step_no_params.signature == "start"

    def test_step_grounding(self):
        """Test grounding detection."""
        grounded = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
        )
        assert grounded.is_grounded is True

        with_variables = GroundStep(
            name=OperatorName("move"),
            parameters=("?x", "room1", "room2"),
        )
        assert with_variables.is_grounded is False

    def test_step_supports(self):
        """Test condition support checking."""
        effects = frozenset([
            create_literal("at", "robot", "room2"),
        ])

        step = GroundStep(
            name=OperatorName("move"),
            _effects=effects,
        )

        supported_condition = create_literal("at", "robot", "room2")
        unsupported_condition = create_literal("at", "robot", "room3")

        assert step.supports(supported_condition) is True
        assert step.supports(unsupported_condition) is False

    def test_step_threatens(self):
        """Test threat detection."""
        effects = frozenset([
            create_literal("at", "robot", "room1", positive=False),
        ])

        step = GroundStep(
            name=OperatorName("move"),
            _effects=effects,
        )

        threatened_condition = create_literal("at", "robot", "room1")
        safe_condition = create_literal("at", "robot", "room2")

        assert step.threatens(threatened_condition) is True
        assert step.threatens(safe_condition) is False

    def test_step_conflicts(self):
        """Test step conflict detection."""
        step1 = GroundStep(
            name=OperatorName("pickup"),
            _effects=frozenset([create_literal("holding", "robot", "block")]),
        )

        step2 = GroundStep(
            name=OperatorName("putdown"),
            _effects=frozenset([create_literal("holding", "robot", "block", positive=False)]),
        )

        step3 = GroundStep(
            name=OperatorName("move"),
            _effects=frozenset([create_literal("at", "robot", "room2")]),
        )

        assert step1.conflicts_with(step2) is True
        assert step1.conflicts_with(step3) is False

    def test_step_substitution(self):
        """Test applying substitutions to steps."""
        preconditions = frozenset([create_literal("at", "?x", "?from")])
        effects = frozenset([create_literal("at", "?x", "?to")])

        step = GroundStep(
            name=OperatorName("move"),
            parameters=("?x", "?from", "?to"),
            _preconditions=preconditions,
            _effects=effects,
        )

        substitution = {
            "?x": "robot",
            "?from": "room1",
            "?to": "room2",
        }

        result = step.substitute(substitution)

        assert result.parameters == ("robot", "room1", "room2")
        assert result.id != step.id  # Should have new ID

        # Check that preconditions and effects were substituted
        expected_precond = create_literal("at", "robot", "room1")
        expected_effect = create_literal("at", "robot", "room2")

        assert any(p.predicate == expected_precond.predicate and
                  p.arguments == expected_precond.arguments
                  for p in result.preconditions)
        assert any(e.predicate == expected_effect.predicate and
                  e.arguments == expected_effect.arguments
                  for e in result.effects)

    def test_step_unification(self):
        """Test step unification."""
        step1 = GroundStep(
            name=OperatorName("move"),
            parameters=("?x", "room1", "room2"),
        )

        step2 = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
        )

        substitution = step1.unify(step2)
        assert substitution is not None
        assert substitution["?x"] == "robot"

        # Test unification failure - different operators
        step3 = GroundStep(
            name=OperatorName("pickup"),
            parameters=("robot", "block"),
        )

        substitution = step1.unify(step3)
        assert substitution is None

    def test_step_copy_with(self):
        """Test copying with modifications."""
        original = GroundStep(
            name=OperatorName("move"),
            parameters=("robot", "room1", "room2"),
            height=0,
            depth=1,
        )

        copy = original.copy_with(
            name=OperatorName("transport"),
            depth=2,
        )

        assert copy.name == OperatorName("transport")
        assert copy.parameters == ("robot", "room1", "room2")  # Unchanged
        assert copy.depth == 2
        assert copy.id != original.id  # New ID

    def test_step_equality(self):
        """Test step equality based on ID."""
        step1 = GroundStep(name=OperatorName("move"))
        step2 = GroundStep(name=OperatorName("move"))

        # Different instances should have different IDs and not be equal
        assert step1 != step2
        assert step1.id != step2.id

        # Same instance should equal itself
        assert step1 == step1

    def test_step_ordering(self):
        """Test step ordering for sorted collections."""
        step1 = GroundStep(name=OperatorName("move"), parameters=("robot", "room1", "room2"))
        step2 = GroundStep(name=OperatorName("pickup"), parameters=("robot", "block"))
        step3 = GroundStep(name=OperatorName("move"), parameters=("robot", "room2", "room3"))

        steps = [step2, step1, step3]
        sorted_steps = sorted(steps)

        # Should be sorted by name, then parameters
        assert sorted_steps[0].name == "move"
        assert sorted_steps[1].name == "move"
        assert sorted_steps[2].name == "pickup"


class TestSpecialSteps:
    """Test cases for special step types."""

    def test_initial_step(self):
        """Test initial step creation."""
        initial_state = {
            create_literal("at", "robot", "room1"),
            create_literal("adjacent", "room1", "room2"),
        }

        step = create_initial_step(initial_state)

        assert step.name == "__INITIAL__"
        assert step.parameters == ()
        assert len(step.preconditions) == 0
        assert len(step.effects) == len(initial_state)
        assert step.instantiable is False

    def test_goal_step(self):
        """Test goal step creation."""
        goal_state = {
            create_literal("at", "robot", "room2"),
            create_literal("holding", "robot", "block"),
        }

        step = create_goal_step(goal_state)

        assert step.name == "__GOAL__"
        assert step.parameters == ()
        assert len(step.preconditions) == len(goal_state)
        assert len(step.effects) == 0
        assert step.instantiable is False


if __name__ == "__main__":
    pytest.main([__file__])