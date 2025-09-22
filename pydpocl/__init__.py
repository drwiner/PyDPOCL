"""PyDPOCL - A modern Python implementation of Decompositional Partial Order Causal-Link Planning.

This package provides a clean, efficient, and extensible implementation of the DPOCL
planning algorithm with modern Python practices.
"""

from pydpocl.core.flaw_simple import CausalLink, OpenConditionFlaw
from pydpocl.core.plan import Plan
from pydpocl.core.step import Step
from pydpocl.domain.compiler import compile_domain_and_problem
from pydpocl.planning.planner import DPOCLPlanner
from pydpocl.planning.search import SearchStrategy

__version__ = "2.0.0"
__author__ = "David Winer"
__email__ = "drwiner@cs.utah.edu"

__all__ = [
    "Plan",
    "Step",
    "OpenConditionFlaw",
    "CausalLink",
    "DPOCLPlanner",
    "SearchStrategy",
    "compile_domain_and_problem",
]
