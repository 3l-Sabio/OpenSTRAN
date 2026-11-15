"""Print a saved benchmark run as the table used on the docs page.

    python benchmarks/report.py .benchmarks/<platform>/0001_baseline.json

The output is reStructuredText: the environment the run was made in,
followed by one table row per model.
"""
import json
import sys


def milliseconds(seconds: float | None) -> str:
    """Format a time in seconds as milliseconds."""
    if seconds is None:
        return "n/a"
    ms = seconds*1000
    if ms < 1:
        return f"{ms:.3f}"
    return f"{ms:,.1f}" if ms < 100 else f"{ms:,.0f}"


def megabytes(value: float | None) -> str:
    """Format a memory figure in MB."""
    return "n/a" if value is None else f"{value:,.0f}"


def main() -> None:
    with open(sys.argv[1]) as file:
        run = json.load(file)

    machine = run["machine_info"]
    commit = run["commit_info"]
    by_group: dict[str, dict[str, dict]] = {}
    for benchmark in run["benchmarks"]:
        by_group.setdefault(benchmark["group"], {})[
            benchmark["param"]] = benchmark

    solves = by_group.get("solve")
    if not solves:
        sys.exit("This run holds no solve benchmarks, so there is no table "
                 "to print.")
    builds = by_group.get("build", {})

    commit_id = commit["id"][:7] + (
        " plus uncommitted changes" if commit.get("dirty") else "")
    cpu = machine.get("cpu", {})
    threads = machine.get("blas_threads")
    print(f"* **Run on**: {run['datetime'][:10]}")
    print(f"* **Commit**: {commit_id}")
    print(f"* **Python**: {machine['python_version']}, "
          f"numpy {machine.get('numpy', 'n/a')}, "
          f"scipy {machine.get('scipy', 'n/a')}")
    print(f"* **CPU**: {cpu.get('brand_raw') or machine['machine']}, "
          f"{cpu.get('count', 'n/a')} cores, "
          + (f"{threads} BLAS thread" if threads
             else "BLAS thread count not confirmed"))
    print(f"* **System**: {machine['system']} {machine['release']}")
    print()

    header = ["Model", "Nodes", "Free DoF", "Build (ms)", "Solve (ms)",
              "Linear system (ms)", "Peak memory (MB)"]
    print(".. list-table::")
    print("   :header-rows: 1")
    print()
    print("   * - " + "\n     - ".join(header))

    for name, solve in solves.items():
        info = solve["extra_info"]
        build = builds.get(name)
        solve_s = solve["stats"]["min"]
        solver_s = info.get("solver_min_s")
        linear = milliseconds(solver_s)
        if solver_s is not None:
            linear += f" ({solver_s/solve_s:.0%})"
        row = [
            info["description"],
            f"{info['nodes']:,}",
            f"{info['free_dof']:,}",
            milliseconds(build["stats"]["min"] if build else None),
            milliseconds(solve_s),
            linear,
            megabytes(info.get("peak_mb")),
        ]
        print("   * - " + "\n     - ".join(row))

    imports = [b["extra_info"].get("import_mb")
               for b in solves.values()]
    imports = [value for value in imports if value is not None]
    if imports:
        print()
        print(f"Importing the library alone takes about "
              f"{megabytes(sum(imports)/len(imports))} MB.")


if __name__ == "__main__":
    main()
