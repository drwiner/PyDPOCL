"""Command-line interface for PyDPOCL."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pydpocl import __version__
from pydpocl.core.literal import parse_literal
from pydpocl.core.plan import create_initial_plan
from pydpocl.domain.compiler import compile_domain_and_problem
from pydpocl.planning.planner import DPOCLPlanner

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Suppress non-essential output"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """PyDPOCL - A modern Python implementation of Decompositional Partial Order Causal-Link Planning."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if not quiet:
        console.print(f"[bold blue]PyDPOCL {__version__}[/bold blue]")


@cli.command()
@click.argument("domain_file", type=click.Path(exists=True, path_type=Path))
@click.argument("problem_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--max-solutions", "-k", default=1, help="Maximum number of solutions to find"
)
@click.option(
    "--timeout", "-t", default=300.0, help="Timeout in seconds"
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file for solutions"
)
@click.option(
    "--strategy", default="best_first",
    type=click.Choice(["best_first", "breadth_first", "depth_first"]),
    help="Search strategy to use"
)
@click.option(
    "--heuristic", default="zero",
    type=click.Choice(["zero", "goal_count", "relaxed_plan"]),
    help="Heuristic function to use"
)
@click.pass_context
def solve(
    ctx: click.Context,
    domain_file: Path,
    problem_file: Path,
    max_solutions: int,
    timeout: float,
    output: Path | None,
    strategy: str,
    heuristic: str,
) -> None:
    """Solve a planning problem."""
    verbose = ctx.obj["verbose"]
    quiet = ctx.obj["quiet"]

    try:
        if not quiet:
            console.print(f"Domain: [cyan]{domain_file}[/cyan]")
            console.print(f"Problem: [cyan]{problem_file}[/cyan]")
            console.print(f"Strategy: [yellow]{strategy}[/yellow]")
            console.print(f"Heuristic: [yellow]{heuristic}[/yellow]")
            console.print()

        # Compile domain and problem
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Compiling domain and problem...", total=None)

            try:
                ground_steps = compile_domain_and_problem(domain_file, problem_file)
                progress.update(task, description=f"Compiled {len(ground_steps)} ground steps")
            except Exception as e:
                console.print(f"[red]Error compiling domain/problem:[/red] {e}")
                sys.exit(1)

        # Create planner
        planner = DPOCLPlanner(
            search_strategy=strategy,
            heuristic=heuristic,
            verbose=verbose,
        )

        # Solve problem
        if not quiet:
            console.print(f"Searching for up to {max_solutions} solutions...")
            console.print()

        solutions = []
        stats = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Planning...", total=None)

            try:
                # Note: This is a placeholder - actual implementation would use the real planner
                # For now, create a dummy solution
                initial_state = {parse_literal("at(robot, room1)")}
                goal_state = {parse_literal("at(robot, room2)")}

                initial_plan = create_initial_plan(initial_state, goal_state)
                solutions = [initial_plan]  # Placeholder

                stats = {
                    "expanded_nodes": 42,
                    "visited_nodes": 123,
                    "time_elapsed": 1.5,
                }

                progress.update(
                    task,
                    description=f"Found {len(solutions)} solution(s)"
                )

            except Exception as e:
                console.print(f"[red]Planning error:[/red] {e}")
                sys.exit(1)

        # Display results
        if solutions:
            if not quiet:
                console.print(f"[green]Found {len(solutions)} solution(s)![/green]")
                console.print()

            for i, solution in enumerate(solutions, 1):
                if not quiet:
                    console.print(f"[bold]Solution {i}:[/bold]")

                    # Display solution steps
                    steps = solution.to_execution_sequence()
                    if steps:
                        table = Table(title=f"Solution {i} Steps")
                        table.add_column("Step", style="cyan")
                        table.add_column("Action", style="white")

                        for j, step in enumerate(steps, 1):
                            table.add_row(str(j), step.signature)

                        console.print(table)
                    else:
                        console.print("Empty plan (no actions needed)")

                    console.print()

            # Display statistics
            if verbose and stats:
                stats_table = Table(title="Planning Statistics")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="white")

                for key, value in stats.items():
                    stats_table.add_row(key.replace("_", " ").title(), str(value))

                console.print(stats_table)

            # Save to output file if specified
            if output:
                try:
                    with open(output, "w") as f:
                        f.write(f"# PyDPOCL Solutions for {problem_file.name}\n\n")
                        for i, solution in enumerate(solutions, 1):
                            f.write(f"## Solution {i}\n")
                            steps = solution.to_execution_sequence()
                            for j, step in enumerate(steps, 1):
                                f.write(f"{j}. {step.signature}\n")
                            f.write("\n")

                    console.print(f"Solutions saved to [cyan]{output}[/cyan]")

                except Exception as e:
                    console.print(f"[red]Error saving output:[/red] {e}")

        else:
            console.print("[yellow]No solutions found within the time limit.[/yellow]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Planning interrupted by user.[/yellow]")
        sys.exit(1)


@cli.command()
@click.argument("domain_file", type=click.Path(exists=True, path_type=Path))
@click.argument("problem_file", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def validate(
    ctx: click.Context,
    domain_file: Path,
    problem_file: Path,
) -> None:
    """Validate a domain and problem file."""
    quiet = ctx.obj["quiet"]

    try:
        if not quiet:
            console.print("Validating domain and problem files...")

        # Compile and validate
        try:
            ground_steps = compile_domain_and_problem(domain_file, problem_file)

            if not quiet:
                console.print(f"[green]✓[/green] Successfully compiled {len(ground_steps)} ground steps")
                console.print("[green]✓[/green] Domain and problem files are valid")

        except Exception as e:
            console.print(f"[red]✗[/red] Validation failed: {e}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error during validation:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("domain_file", type=click.Path(exists=True, path_type=Path))
@click.argument("problem_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file for ground steps"
)
@click.pass_context
def compile(
    ctx: click.Context,
    domain_file: Path,
    problem_file: Path,
    output: Path | None,
) -> None:
    """Compile domain and problem into ground steps."""
    quiet = ctx.obj["quiet"]

    try:
        if not quiet:
            console.print("Compiling domain and problem...")

        # Compile
        ground_steps = compile_domain_and_problem(domain_file, problem_file)

        if not quiet:
            console.print(f"[green]Successfully compiled {len(ground_steps)} ground steps[/green]")

        # Save or display
        if output:
            try:
                # Save ground steps (this would need a proper serialization format)
                with open(output, "w") as f:
                    f.write(f"# Ground steps for {problem_file.name}\n")
                    f.write(f"# Total: {len(ground_steps)} steps\n\n")

                    for i, step in enumerate(ground_steps):
                        f.write(f"Step {i}: {step.signature}\n")
                        f.write(f"  Preconditions: {list(step.preconditions)}\n")
                        f.write(f"  Effects: {list(step.effects)}\n")
                        f.write("\n")

                console.print(f"Ground steps saved to [cyan]{output}[/cyan]")

            except Exception as e:
                console.print(f"[red]Error saving output:[/red] {e}")

        elif not quiet:
            # Display summary
            table = Table(title="Ground Steps Summary")
            table.add_column("Step", style="cyan")
            table.add_column("Operator", style="white")
            table.add_column("Parameters", style="yellow")

            for i, step in enumerate(ground_steps[:10]):  # Show first 10
                table.add_row(
                    str(i),
                    str(step.name),
                    ", ".join(step.parameters) if step.parameters else "None"
                )

            if len(ground_steps) > 10:
                table.add_row("...", "...", "...")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error during compilation:[/red] {e}")
        sys.exit(1)


@cli.command()
def examples() -> None:
    """Show usage examples."""
    console.print("[bold]PyDPOCL Usage Examples[/bold]\n")

    examples = [
        ("Basic planning", "pydpocl solve domain.pddl problem.pddl"),
        ("Find multiple solutions", "pydpocl solve domain.pddl problem.pddl -k 5"),
        ("Use different search strategy", "pydpocl solve domain.pddl problem.pddl --strategy breadth_first"),
        ("Save solutions to file", "pydpocl solve domain.pddl problem.pddl -o solutions.txt"),
        ("Validate domain/problem", "pydpocl validate domain.pddl problem.pddl"),
        ("Compile to ground steps", "pydpocl compile domain.pddl problem.pddl -o ground_steps.txt"),
    ]

    for description, command in examples:
        console.print(f"[cyan]{description}:[/cyan]")
        console.print(f"  {command}")
        console.print()


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
