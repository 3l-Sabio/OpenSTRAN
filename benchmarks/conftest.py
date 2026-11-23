import os
import subprocess
import sys
from pathlib import Path

# Let the benchmark modules import the modules that sit next to them.
sys.path.insert(0, os.path.dirname(__file__))

# Imported before numpy, so the numeric libraries run on one thread.
import threads  # noqa: E402

LIBRARY = Path(__file__).resolve().parent.parent / "src"


def pytest_benchmark_update_machine_info(config, machine_info):
    """Record the numeric library versions with every saved run."""
    import numpy
    import scipy

    machine_info["numpy"] = numpy.__version__
    machine_info["scipy"] = scipy.__version__
    machine_info["blas_threads"] = threads.blas_threads()


def pytest_benchmark_update_commit_info(config, commit_info):
    """Record the library code each saved run measured.

    That is the last commit that changed ``src/`` and whether ``src/`` has
    changes that are not committed. A run made with uncommitted changes to
    the benchmarks or the docs only is then still labelled with a commit.
    """
    def git(*args: str) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args, "--", str(LIBRARY)], cwd=LIBRARY,
                capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            return None
        return completed.stdout.strip()

    commit_info["library_id"] = git("log", "-1", "--format=%h")
    status = git("status", "--porcelain")
    commit_info["library_dirty"] = None if status is None else bool(status)
