#!/usr/bin/env python3
"""
Example usage of PyDPOCL planning system.

This script demonstrates how to use the PyDPOCL planner with a simple
travel planning domain.
"""

from PyDPOCL import GPlanner, just_compile
import pickle
import os

def run_simple_example():
    """Run a simple planning example with the travel domain."""

    print("PyDPOCL Example - Travel Planning")
    print("=" * 40)

    # Define domain and problem files
    domain_file = 'Ground_Compiler_Library/domains/travel_domain.pddl'
    problem_file = 'Ground_Compiler_Library/domains/travel-to-la.pddl'

    print(f"Domain: {domain_file}")
    print(f"Problem: {problem_file}")
    print()

    # Check if files exist
    if not os.path.exists(domain_file):
        print(f"Error: Domain file {domain_file} not found!")
        return

    if not os.path.exists(problem_file):
        print(f"Error: Problem file {problem_file} not found!")
        return

    # Compile PDDL files to ground steps
    print("Compiling PDDL domain and problem...")
    uploadable_ground_step_library_name = 'example_ground_steps'

    try:
        # Try to load existing ground steps first
        ground_steps = []
        i = 0
        while True:
            try:
                with open(uploadable_ground_step_library_name + str(i), 'rb') as f:
                    ground_steps.append(pickle.load(f))
                i += 1
            except FileNotFoundError:
                break

        if not ground_steps:
            # Compile if no existing ground steps found
            print("No existing ground steps found, compiling...")
            ground_steps = just_compile(domain_file, problem_file, uploadable_ground_step_library_name)
        else:
            print(f"Loaded {len(ground_steps)} ground step libraries from cache")

    except Exception as e:
        print(f"Error during compilation: {e}")
        return

    # Create planner
    print("Creating planner...")
    planner = GPlanner(ground_steps)

    # Solve the planning problem
    print("Solving planning problem...")
    print("Looking for up to 5 solutions with 60 second timeout...")
    print()

    try:
        solutions = planner.solve(k=5, cutoff=60)

        if solutions:
            print(f"Found {len(solutions)} solution(s)!")

            # Display first solution
            solution = solutions[0]
            print(f"\\nFirst solution (cost: {solution.cost}):")
            print("-" * 30)

            for i, step in enumerate(solution.steps):
                if hasattr(step, 'action') and step.action:
                    print(f"{i+1}. {step.action}")
                elif hasattr(step, 'name'):
                    print(f"{i+1}. {step.name}")
                else:
                    print(f"{i+1}. {step}")

        else:
            print("No solutions found within the time limit.")

    except Exception as e:
        print(f"Error during planning: {e}")
        return

    print("\\nExample completed successfully!")

if __name__ == "__main__":
    run_simple_example()