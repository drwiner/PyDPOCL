# PyDPOCL - A Python Implementation of Decompositional Partial Order Causal-Link Planning

PyDPOCL is a Python implementation of the DPOCL (Decompositional Partial Order Causal-Link) planning algorithm, a plan-space search technique that resolves flaws in partial plans to find complete solutions.

## Overview

DPOCL is a plan-space planning algorithm that:
- Searches through the space of partial plans rather than state space
- Uses causal links to maintain dependencies between plan steps
- Resolves flaws (open conditions and threats) incrementally
- Supports hierarchical decomposition of complex actions

This implementation includes:
- Complete POCL planning engine with threat detection and resolution
- Ground step preprocessing from PDDL domain and problem files
- Support for hierarchical planning with step decomposition
- Flexible heuristics and search strategies
- Example domains including travel planning scenarios

## Requirements

- Python 3.10 or higher
- NumPy (for data analysis scripts)
- Matplotlib (for visualization scripts)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd PyDPOCL
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Planning Example

```python
from PyDPOCL import GPlanner, just_compile

# Compile PDDL domain and problem into ground steps
domain_file = 'Ground_Compiler_Library/domains/travel_domain.pddl'
problem_file = 'Ground_Compiler_Library/domains/travel-to-la.pddl'
ground_steps = just_compile(domain_file, problem_file, 'example_ground_steps')

# Create planner and solve
planner = GPlanner(ground_steps)
solutions = planner.solve(k=10, cutoff=300)  # Find up to 10 solutions within 300 seconds
```

### Running the Example Experiment

```bash
python run_experiment.py
```

This will run the planner on several travel planning problems of increasing complexity.

## Core Components

### PyDPOCL.py
Main planner implementation containing:
- `GPlanner`: The main planning class
- `Frontier`: Priority queue for managing partial plans
- Search algorithms and flaw resolution strategies

### GPlan.py
Plan representation including:
- Plan steps and causal links
- Ordering constraints
- Flaw tracking and management

### Flaws.py
Flaw types and resolution:
- `OPF`: Open Precondition Flaws
- `TCLF`: Threatened Causal Link Flaws

### Ground_Compiler_Library/
PDDL preprocessing components:
- Domain and problem parsing
- Ground step generation
- Graph representations for ordering and causal relationships

## Example Domains

The `Ground_Compiler_Library/domains/` directory contains several example planning domains:

- **Travel Domain**: Multi-modal transportation planning with cars and planes
- **Ark Domain**: Hierarchical planning examples with decomposition

## Algorithm Details

DPOCL works by:

1. **Initialization**: Start with a partial plan containing only initial and goal steps
2. **Flaw Selection**: Choose an unresolved flaw from the current plan
3. **Flaw Resolution**: Generate child plans that resolve the selected flaw
4. **Threat Detection**: Check for and resolve any threatened causal links
5. **Iteration**: Repeat until k complete plans are found or time limit reached

### Key Features

- **Partial Order Scheduling**: Plans specify only necessary ordering constraints
- **Causal Link Protection**: Maintains explicit causal dependencies
- **Hierarchical Decomposition**: Supports abstract actions that decompose into sub-plans
- **Flexible Search**: Configurable search strategies and heuristics

## Performance Analysis

The repository includes analysis tools for comparing different search strategies and heuristics:

- `read_output.py`: Analyzes experimental results
- Various `.txt` files contain experimental data

## Contributing

This is a research implementation of the DPOCL algorithm. Contributions are welcome, particularly:

- Additional PDDL domains and problems
- Performance optimizations
- Enhanced visualization tools
- Documentation improvements

## References

This implementation is based on research in plan-space planning and hierarchical task networks. For more details on the DPOCL algorithm, see the relevant AI planning literature.

## License

[Add your preferred license here]

## Author

David Winer - drwiner@cs.utah.edu

---

**Note**: This is a research-oriented implementation. For production planning applications, consider more mature planning frameworks.