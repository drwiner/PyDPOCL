"""Simple blocks world example for PyDPOCL."""

from pydpocl.core.literal import create_literal
from pydpocl.core.step import GroundStep
from pydpocl.core.plan import create_initial_plan
from pydpocl.core.types import OperatorName


def create_blocks_world_example():
    """Create a simple blocks world planning problem."""

    # Initial state: Block A is on table, Block B is on Block A
    initial_state = {
        create_literal("on_table", "block_a"),
        create_literal("on", "block_b", "block_a"),
        create_literal("clear", "block_b"),
        create_literal("arm_empty"),
    }

    # Goal state: Block A is on Block B
    goal_state = {
        create_literal("on", "block_a", "block_b"),
    }

    # Create the initial plan
    initial_plan = create_initial_plan(initial_state, goal_state, "blocks_world")

    # Available ground steps (actions)
    ground_steps = []

    # Pickup from table
    pickup_a = GroundStep(
        name=OperatorName("pickup_from_table"),
        parameters=("block_a",),
        _preconditions=frozenset([
            create_literal("on_table", "block_a"),
            create_literal("clear", "block_a"),
            create_literal("arm_empty"),
        ]),
        _effects=frozenset([
            create_literal("holding", "block_a"),
            create_literal("on_table", "block_a", positive=False),
            create_literal("arm_empty", positive=False),
        ]),
    )
    ground_steps.append(pickup_a)

    # Pickup from another block
    pickup_b = GroundStep(
        name=OperatorName("pickup"),
        parameters=("block_b", "block_a"),
        _preconditions=frozenset([
            create_literal("on", "block_b", "block_a"),
            create_literal("clear", "block_b"),
            create_literal("arm_empty"),
        ]),
        _effects=frozenset([
            create_literal("holding", "block_b"),
            create_literal("on", "block_b", "block_a", positive=False),
            create_literal("clear", "block_a"),
            create_literal("arm_empty", positive=False),
        ]),
    )
    ground_steps.append(pickup_b)

    # Put down on table
    putdown_a = GroundStep(
        name=OperatorName("putdown_on_table"),
        parameters=("block_a",),
        _preconditions=frozenset([
            create_literal("holding", "block_a"),
        ]),
        _effects=frozenset([
            create_literal("on_table", "block_a"),
            create_literal("clear", "block_a"),
            create_literal("arm_empty"),
            create_literal("holding", "block_a", positive=False),
        ]),
    )
    ground_steps.append(putdown_a)

    putdown_b = GroundStep(
        name=OperatorName("putdown_on_table"),
        parameters=("block_b",),
        _preconditions=frozenset([
            create_literal("holding", "block_b"),
        ]),
        _effects=frozenset([
            create_literal("on_table", "block_b"),
            create_literal("clear", "block_b"),
            create_literal("arm_empty"),
            create_literal("holding", "block_b", positive=False),
        ]),
    )
    ground_steps.append(putdown_b)

    # Stack blocks
    stack_a_on_b = GroundStep(
        name=OperatorName("stack"),
        parameters=("block_a", "block_b"),
        _preconditions=frozenset([
            create_literal("holding", "block_a"),
            create_literal("clear", "block_b"),
        ]),
        _effects=frozenset([
            create_literal("on", "block_a", "block_b"),
            create_literal("clear", "block_a"),
            create_literal("clear", "block_b", positive=False),
            create_literal("arm_empty"),
            create_literal("holding", "block_a", positive=False),
        ]),
    )
    ground_steps.append(stack_a_on_b)

    return initial_plan, ground_steps


def main():
    """Demonstrate the blocks world example."""
    print("PyDPOCL Blocks World Example")
    print("=" * 40)

    initial_plan, ground_steps = create_blocks_world_example()

    print(f"Initial plan: {initial_plan}")
    print(f"Number of flaws: {len(initial_plan.flaws)}")
    print(f"Available ground steps: {len(ground_steps)}")

    print("\nInitial state (from initial step effects):")
    for effect in initial_plan.initial_step.effects:
        print(f"  {effect}")

    print("\nGoal conditions (from goal step preconditions):")
    for precond in initial_plan.goal_step.preconditions:
        print(f"  {precond}")

    print("\nFlaws to resolve:")
    for flaw in initial_plan.flaws:
        print(f"  {flaw}")

    print("\nAvailable actions:")
    for i, step in enumerate(ground_steps):
        print(f"  {i+1}. {step.signature}")
        print(f"     Preconditions: {[str(p) for p in step.preconditions]}")
        print(f"     Effects: {[str(e) for e in step.effects]}")

    # In a full implementation, we would now run the planner
    print("\n[Note: Full planning implementation would continue from here]")


if __name__ == "__main__":
    main()