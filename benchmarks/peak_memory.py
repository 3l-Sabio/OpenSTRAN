"""Build and solve one benchmark model and report the memory it needed.

Run as its own process so the figure belongs to one model only:

    python benchmarks/peak_memory.py frame_2d_3x3

Prints a JSON object with the process's peak resident memory in MB once
Python has started and imported OpenSTRAN, with numpy and scipy
(``import_mb``), and once the model is built and solved (``peak_mb``).
Process memory is used instead of ``tracemalloc`` because solvers allocate
inside compiled code that ``tracemalloc`` does not see.
"""
import json
import sys

import threads  # noqa: F401  (one thread, set before numpy loads)

try:
    import resource
except ImportError:  # Windows
    resource = None


def peak_mb() -> float | None:
    """Return this process's peak resident memory in MB."""
    # On Linux, ru_maxrss starts at the size of the process that launched
    # this one, so a large parent hides a small model. VmHWM belongs to this
    # process alone.
    try:
        with open("/proc/self/status") as status:
            for line in status:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])/1024
    except OSError:
        pass

    if resource is None:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is in bytes on macOS and in kilobytes on Linux.
    divisor = 1024**2 if sys.platform == "darwin" else 1024
    return peak/divisor


def main() -> None:
    import OpenSTRAN  # noqa: F401  (also imports numpy and scipy)

    import_mb = peak_mb()

    # Importing the models also looks up their section in the database.
    from models import CASES_BY_NAME

    case = CASES_BY_NAME[sys.argv[1]]
    model = case.build()
    model.solve()
    print(json.dumps({"import_mb": import_mb, "peak_mb": peak_mb()}))


if __name__ == "__main__":
    main()
