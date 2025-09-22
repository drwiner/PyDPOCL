"""Literal representation for PyDPOCL planning system."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from pydpocl.core.types import (
    Grounded,
    Identifiable,
    LiteralId,
    ObjectName,
    PredicateName,
)


@dataclass(frozen=True, slots=True)
class Literal(Identifiable, Grounded):
    """Immutable representation of a planning literal.

    A literal consists of a predicate name, arguments, and a truth value.
    This implementation uses immutable data structures for efficiency
    and thread safety.
    """

    predicate: PredicateName
    arguments: tuple[ObjectName, ...]
    positive: bool = True
    _id: UUID | None = None
    is_static: bool = False

    def __post_init__(self) -> None:
        """Initialize the unique identifier after creation."""
        if self._id is None:
            object.__setattr__(self, "_id", uuid4())

    @property
    def id(self) -> UUID:
        """Return the unique identifier for this literal."""
        return self._id or uuid4()

    @property
    def literal_id(self) -> LiteralId:
        """Return the typed literal identifier."""
        return LiteralId(self.id)

    @property
    def is_grounded(self) -> bool:
        """Return True if this literal is fully grounded (no variables)."""
        return all(not arg.startswith("?") for arg in self.arguments)

    @property
    def arity(self) -> int:
        """Return the number of arguments in this literal."""
        return len(self.arguments)

    @property
    def signature(self) -> str:
        """Return a string signature for this literal."""
        args_str = ", ".join(self.arguments)
        predicate_str = f"{self.predicate}({args_str})"
        return predicate_str if self.positive else f"not {predicate_str}"

    def negate(self) -> Literal:
        """Return the negation of this literal."""
        return Literal(
            predicate=self.predicate,
            arguments=self.arguments,
            positive=not self.positive,
            _id=uuid4(),  # New ID for negated literal
            is_static=self.is_static,
        )

    def unify(self, other: Literal) -> dict[str, ObjectName] | None:
        """Attempt to unify this literal with another.

        Returns a substitution dictionary if unification succeeds,
        None otherwise.
        """
        if self.predicate != other.predicate or self.arity != other.arity:
            return None

        if self.positive != other.positive:
            return None

        substitution: dict[str, ObjectName] = {}

        for arg1, arg2 in zip(self.arguments, other.arguments, strict=False):
            # Variable-variable unification
            if arg1.startswith("?") and arg2.startswith("?"):
                if arg1 in substitution:
                    if substitution[arg1] != arg2:
                        return None
                else:
                    substitution[arg1] = ObjectName(arg2)

            # Variable-constant unification
            elif arg1.startswith("?"):
                if arg1 in substitution:
                    if substitution[arg1] != arg2:
                        return None
                else:
                    substitution[arg1] = ObjectName(arg2)

            elif arg2.startswith("?"):
                if arg2 in substitution:
                    if substitution[arg2] != arg1:
                        return None
                else:
                    substitution[arg2] = ObjectName(arg1)

            # Constant-constant unification
            else:
                if arg1 != arg2:
                    return None

        return substitution

    def substitute(self, substitution: dict[str, ObjectName]) -> Literal:
        """Apply a substitution to this literal."""
        new_arguments = tuple(
            ObjectName(substitution.get(arg, arg)) for arg in self.arguments
        )

        return Literal(
            predicate=self.predicate,
            arguments=new_arguments,
            positive=self.positive,
            _id=uuid4(),  # New ID for substituted literal
            is_static=self.is_static,
        )

    def conflicts_with(self, other: Literal) -> bool:
        """Check if this literal conflicts with another literal.

        Two literals conflict if they have the same predicate and arguments
        but opposite truth values.
        """
        return (
            self.predicate == other.predicate
            and self.arguments == other.arguments
            and self.positive != other.positive
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return self.signature

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"Literal(predicate={self.predicate!r}, "
            f"arguments={self.arguments!r}, positive={self.positive}, "
            f"id={self.id}, is_static={self.is_static})"
        )

    def __hash__(self) -> int:
        """Return hash value for use in sets and dictionaries."""
        return hash((self.predicate, self.arguments, self.positive))

    def __eq__(self, other: object) -> bool:
        """Check equality with another literal."""
        if not isinstance(other, Literal):
            return NotImplemented

        return (
            self.predicate == other.predicate
            and self.arguments == other.arguments
            and self.positive == other.positive
        )

    def __lt__(self, other: object) -> bool:
        """Define ordering for literals (for use in sorted collections)."""
        if not isinstance(other, Literal):
            return NotImplemented

        # Order by: predicate, arguments, then positive flag
        return (self.predicate, self.arguments, self.positive) < (
            other.predicate,
            other.arguments,
            other.positive,
        )


def create_literal(
    predicate: str,
    *arguments: str,
    positive: bool = True,
    is_static: bool = False,
) -> Literal:
    """Convenience function for creating literals."""
    return Literal(
        predicate=PredicateName(predicate),
        arguments=tuple(ObjectName(arg) for arg in arguments),
        positive=positive,
        is_static=is_static,
    )


def parse_literal(literal_str: str) -> Literal:
    """Parse a literal from a string representation.

    Examples:
        "at(robot, room1)" -> Literal(predicate="at", arguments=("robot", "room1"))
        "not holding(robot, block)" -> Literal(..., positive=False)
    """
    literal_str = literal_str.strip()

    # Handle negation
    positive = True
    if literal_str.startswith("not "):
        positive = False
        literal_str = literal_str[4:].strip()
    elif literal_str.startswith("¬"):
        positive = False
        literal_str = literal_str[1:].strip()

    # Parse predicate and arguments
    if "(" not in literal_str:
        # Propositional literal
        return create_literal(literal_str, positive=positive)

    predicate_part, args_part = literal_str.split("(", 1)
    predicate = predicate_part.strip()

    if not args_part.endswith(")"):
        raise ValueError(f"Invalid literal format: {literal_str}")

    args_str = args_part[:-1].strip()
    if args_str:
        arguments = [arg.strip() for arg in args_str.split(",")]
    else:
        arguments = []

    return create_literal(predicate, *arguments, positive=positive)
