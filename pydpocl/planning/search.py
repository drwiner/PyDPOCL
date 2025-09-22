"""Search strategies for planning."""

from __future__ import annotations

import heapq
from collections import deque
from typing import Generic, Protocol, TypeVar

from pydpocl.core.plan import Plan

T = TypeVar("T")


class SearchStrategy(Protocol, Generic[T]):
    """Protocol for search strategies."""

    def add_plan(self, plan: T) -> None:
        """Add a plan to the frontier."""
        ...

    def get_next_plan(self) -> T | None:
        """Get the next plan to expand."""
        ...

    def is_empty(self) -> bool:
        """Check if the frontier is empty."""
        ...

    def size(self) -> int:
        """Get the size of the frontier."""
        ...


class BestFirstSearch:
    """Best-first search using a priority queue."""

    def __init__(self) -> None:
        self._frontier: list[Plan] = []
        self._counter = 0  # For tie-breaking

    def add_plan(self, plan: Plan) -> None:
        """Add a plan to the frontier."""
        # Use counter for stable sorting when plans have equal priority
        heapq.heappush(self._frontier, (plan, self._counter))
        self._counter += 1

    def get_next_plan(self) -> Plan | None:
        """Get the next plan to expand."""
        if not self._frontier:
            return None
        plan, _ = heapq.heappop(self._frontier)
        return plan

    def is_empty(self) -> bool:
        """Check if the frontier is empty."""
        return len(self._frontier) == 0

    def size(self) -> int:
        """Get the size of the frontier."""
        return len(self._frontier)


class BreadthFirstSearch:
    """Breadth-first search using a queue."""

    def __init__(self) -> None:
        self._frontier: deque[Plan] = deque()

    def add_plan(self, plan: Plan) -> None:
        """Add a plan to the frontier."""
        self._frontier.append(plan)

    def get_next_plan(self) -> Plan | None:
        """Get the next plan to expand."""
        if not self._frontier:
            return None
        return self._frontier.popleft()

    def is_empty(self) -> bool:
        """Check if the frontier is empty."""
        return len(self._frontier) == 0

    def size(self) -> int:
        """Get the size of the frontier."""
        return len(self._frontier)


class DepthFirstSearch:
    """Depth-first search using a stack."""

    def __init__(self) -> None:
        self._frontier: list[Plan] = []

    def add_plan(self, plan: Plan) -> None:
        """Add a plan to the frontier."""
        self._frontier.append(plan)

    def get_next_plan(self) -> Plan | None:
        """Get the next plan to expand."""
        if not self._frontier:
            return None
        return self._frontier.pop()

    def is_empty(self) -> bool:
        """Check if the frontier is empty."""
        return len(self._frontier) == 0

    def size(self) -> int:
        """Get the size of the frontier."""
        return len(self._frontier)


def create_search_strategy(strategy_name: str) -> SearchStrategy[Plan]:
    """Factory function for creating search strategies."""
    strategies = {
        "best_first": BestFirstSearch,
        "breadth_first": BreadthFirstSearch,
        "depth_first": DepthFirstSearch,
    }

    if strategy_name not in strategies:
        raise ValueError(f"Unknown search strategy: {strategy_name}")

    return strategies[strategy_name]()
