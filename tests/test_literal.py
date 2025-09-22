"""Tests for literal representation."""

import pytest
from uuid import uuid4

from pydpocl.core.literal import (
    Literal,
    create_literal,
    parse_literal,
    PredicateName,
    ObjectName,
)


class TestLiteral:
    """Test cases for the Literal class."""

    def test_literal_creation(self):
        """Test basic literal creation."""
        lit = create_literal("at", "robot", "room1")

        assert lit.predicate == PredicateName("at")
        assert lit.arguments == (ObjectName("robot"), ObjectName("room1"))
        assert lit.positive is True
        assert lit.arity == 2

    def test_literal_negation(self):
        """Test literal negation."""
        lit = create_literal("holding", "robot", "block")
        neg_lit = lit.negate()

        assert lit.positive is True
        assert neg_lit.positive is False
        assert lit.predicate == neg_lit.predicate
        assert lit.arguments == neg_lit.arguments
        assert lit.id != neg_lit.id  # Should have different IDs

    def test_literal_signature(self):
        """Test literal string representations."""
        lit = create_literal("at", "robot", "room1")
        assert lit.signature == "at(robot, room1)"
        assert str(lit) == "at(robot, room1)"

        neg_lit = lit.negate()
        assert neg_lit.signature == "not at(robot, room1)"

    def test_literal_grounding(self):
        """Test grounding detection."""
        grounded = create_literal("at", "robot", "room1")
        assert grounded.is_grounded is True

        variable = create_literal("at", "?x", "room1")
        assert variable.is_grounded is False

    def test_literal_unification(self):
        """Test literal unification."""
        lit1 = create_literal("at", "?x", "room1")
        lit2 = create_literal("at", "robot", "room1")

        substitution = lit1.unify(lit2)
        assert substitution is not None
        assert substitution["?x"] == ObjectName("robot")

        # Test unification failure
        lit3 = create_literal("holding", "robot", "block")
        substitution = lit1.unify(lit3)
        assert substitution is None

    def test_literal_substitution(self):
        """Test applying substitutions."""
        lit = create_literal("at", "?x", "?y")
        substitution = {"?x": ObjectName("robot"), "?y": ObjectName("room1")}

        result = lit.substitute(substitution)
        assert result.arguments == (ObjectName("robot"), ObjectName("room1"))
        assert result.id != lit.id  # Should have new ID

    def test_literal_conflicts(self):
        """Test conflict detection."""
        lit1 = create_literal("at", "robot", "room1")
        lit2 = create_literal("at", "robot", "room1", positive=False)

        assert lit1.conflicts_with(lit2) is True
        assert lit2.conflicts_with(lit1) is True

        lit3 = create_literal("at", "robot", "room2")
        assert lit1.conflicts_with(lit3) is False

    def test_literal_equality(self):
        """Test literal equality."""
        lit1 = create_literal("at", "robot", "room1")
        lit2 = create_literal("at", "robot", "room1")

        # Same content but different instances
        assert lit1 == lit2
        assert hash(lit1) == hash(lit2)

        lit3 = create_literal("at", "robot", "room2")
        assert lit1 != lit3

    def test_literal_ordering(self):
        """Test literal ordering for sorted collections."""
        lit1 = create_literal("at", "robot", "room1")
        lit2 = create_literal("holding", "robot", "block")
        lit3 = create_literal("at", "robot", "room2")

        literals = [lit2, lit1, lit3]
        sorted_literals = sorted(literals)

        # Should be sorted by predicate, then arguments
        assert sorted_literals[0].predicate == "at"
        assert sorted_literals[1].predicate == "at"
        assert sorted_literals[2].predicate == "holding"

    def test_parse_literal(self):
        """Test parsing literals from strings."""
        # Basic literal
        lit1 = parse_literal("at(robot, room1)")
        assert lit1.predicate == PredicateName("at")
        assert lit1.arguments == (ObjectName("robot"), ObjectName("room1"))
        assert lit1.positive is True

        # Negated literal
        lit2 = parse_literal("not holding(robot, block)")
        assert lit2.predicate == PredicateName("holding")
        assert lit2.positive is False

        # Propositional literal
        lit3 = parse_literal("goal_achieved")
        assert lit3.predicate == PredicateName("goal_achieved")
        assert lit3.arguments == ()

    def test_static_literals(self):
        """Test static literal handling."""
        static_lit = create_literal("adjacent", "room1", "room2", is_static=True)
        assert static_lit.is_static is True

        dynamic_lit = create_literal("at", "robot", "room1")
        assert dynamic_lit.is_static is False


if __name__ == "__main__":
    pytest.main([__file__])