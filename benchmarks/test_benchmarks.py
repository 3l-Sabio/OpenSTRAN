"""Benchmarks for building and solving models.

Run with:

    pytest benchmarks

The timed calls go through the public API, so the figures stay comparable
when the internals of the library change. The one exception is the solver's
share of a solve, which is taken by wrapping ``Solver.solve``. If that method
moves, the solve benchmarks fail and the wrapper has to follow it.
"""
import gc
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import pytest

from OpenSTRAN.Solver import Solver

from models import CASES
from models import CASES_BY_NAME
from models import Case

PEAK_MEMORY_SCRIPT = Path(__file__).with_name("peak_memory.py")

# Parametrized by name so the saved results hold a plain string per case.
parametrize_cases = pytest.mark.parametrize(
    "name", [case.name for case in CASES])


@pytest.fixture
def solver_times(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record how long each call to ``Solver.solve`` takes during the test.

    That call assembles the stiffness matrix, solves for displacements,
    recovers reactions and member forces, and collects them into the
    results, which includes finding the maximum member forces.

    The wrapper replaces the method on the class, not on a model's solver,
    so it ties no solver into a reference cycle: a solver and its matrices
    are freed as soon as its model is. monkeypatch restores the method after
    the test.
    """
    times: list[float] = []
    inner = Solver.solve

    def timed_solve(self, *args, **kwargs):
        start = perf_counter()
        try:
            return inner(self, *args, **kwargs)
        finally:
            times.append(perf_counter() - start)

    monkeypatch.setattr(Solver, "solve", timed_solve)
    return times


def check_answers(
    case: Case, solver_times: list[float]
) -> dict[str, float | int]:
    """Solve the case once, untimed, and check the results it gives.

    Equilibrium alone is not enough, because a wrong stiffness matrix still
    balances the applied loads, so the maximum deflection and moment are
    checked as well.

    Returns:
        dict[str, float | int]: The model's size and results, to save with
        the timings.
    """
    model = case.build()
    results = model.solve()

    assert len(solver_times) == 1, (
        "Solver.solve was not called once by model.solve(); update the "
        "solver_times fixture to time the solver where it now lives")

    nodes = results.nodes
    vertical_reaction = sum(results.node(node).Ry for node in nodes)
    Uy_max = results.Uy_max
    Mzz_max = results.Mzz_max

    assert vertical_reaction == pytest.approx(case.vertical_load, rel=1e-6)
    assert Uy_max == pytest.approx(case.Uy_max, rel=1e-6)
    assert Mzz_max == pytest.approx(case.Mzz_max, rel=1e-6)

    return {
        "nodes": len(nodes),
        "dof": len(nodes)*6,
        # The degrees of freedom left after restraints: the size of the
        # system that is solved.
        "free_dof": sum(node.restraint.count(0) for node in nodes),
        "Uy_max": Uy_max,
        "Mzz_max": Mzz_max,
        "vertical_reaction": vertical_reaction,
    }


def measure_peak_memory(case: Case) -> dict[str, float | None]:
    """Solve the case in a fresh process and return its memory figures."""
    completed = subprocess.run(
        [sys.executable, str(PEAK_MEMORY_SCRIPT), case.name],
        capture_output=True, text=True,
    )
    if completed.returncode != 0:
        pytest.fail(f"{PEAK_MEMORY_SCRIPT.name} {case.name} failed:\n"
                    f"{completed.stderr}")
    return json.loads(completed.stdout)


# A built model refers to itself through its nodes and loads, so only the
# garbage collector frees it. It is kept from running during the timing.
@pytest.mark.benchmark(disable_gc=True)
@parametrize_cases
def test_build(benchmark, name: str):
    """Time creating the nodes, members and loads."""
    case = CASES_BY_NAME[name]
    benchmark.group = "build"
    benchmark(case.build)


@parametrize_cases
def test_solve(benchmark, solver_times: list[float], name: str):
    """Time ``model.solve()`` on a freshly built model."""
    case = CASES_BY_NAME[name]
    benchmark.group = "solve"

    # Everything that can fail runs before the timing. pytest-benchmark saves
    # a timing even if the test fails afterwards, so a solve that gives wrong
    # answers must fail here, where there is nothing to save yet.
    results = check_answers(case, solver_times)

    # The model solved above refers to itself through its nodes and loads,
    # so it is collected before another process builds and solves one.
    gc.collect()
    memory = measure_peak_memory(case)

    benchmark.extra_info["description"] = case.description
    benchmark.extra_info.update(results)
    benchmark.extra_info["import_mb"] = memory["import_mb"]
    benchmark.extra_info["peak_mb"] = memory["peak_mb"]

    solver_times.clear()

    def setup():
        # A model refers to itself through its nodes and loads, so the model
        # of the previous round is only freed by a collection. Doing that
        # here keeps it out of the next timed solve.
        gc.collect()
        return (case.build(),), {}

    def solve(model):
        model.solve()

    # A new model is built for every round, outside the timing, because the
    # first solve of a model also meshes its members.
    benchmark.pedantic(solve, setup=setup, rounds=case.rounds, iterations=1)

    benchmark.extra_info["solver_min_s"] = min(solver_times)
