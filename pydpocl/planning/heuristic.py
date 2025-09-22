"""Heuristic functions for planning."""

from __future__ import annotations

from typing import Protocol

from pydpocl.core.plan import Plan


class Heuristic(Protocol):
    """Protocol for heuristic functions."""

    def estimate(self, plan: Plan) -> float:
        """Estimate the cost to complete the plan."""
        ...


class ZeroHeuristic:
    """Heuristic that always returns zero (uniform cost search)."""

    def estimate(self, plan: Plan) -> float:
        """Always return zero."""
        return 0.0


class GoalCountHeuristic:
    """Heuristic based on the number of unachieved goals."""

    def estimate(self, plan: Plan) -> float:
        """Return the number of unresolved flaws."""
        return float(len(plan.flaws))


class RelaxedPlanHeuristic:
    """Heuristic based on solving a relaxed version of the problem."""

    def estimate(self, plan: Plan) -> float:
        """Estimate based on relaxed planning."""
        # This would implement a relaxed planning algorithm
        # For now, return a simple estimate
        return float(len(plan.flaws)) * 0.5


def create_heuristic(heuristic_name: str) -> Heuristic:
    """Factory function for creating heuristics."""
    heuristics = {
        "zero": ZeroHeuristic,
        "goal_count": GoalCountHeuristic,
        "relaxed_plan": RelaxedPlanHeuristic,
    }

    if heuristic_name not in heuristics:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    return heuristics[heuristic_name]()
