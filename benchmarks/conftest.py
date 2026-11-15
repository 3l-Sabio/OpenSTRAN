import os
import sys

# Let the benchmark modules import the modules that sit next to them.
sys.path.insert(0, os.path.dirname(__file__))

# Imported before numpy, so the numeric libraries run on one thread.
import threads  # noqa: E402


def pytest_benchmark_update_machine_info(config, machine_info):
    """Record the numeric library versions with every saved run."""
    import numpy
    import scipy

    machine_info["numpy"] = numpy.__version__
    machine_info["scipy"] = scipy.__version__
    machine_info["blas_threads"] = threads.blas_threads()
