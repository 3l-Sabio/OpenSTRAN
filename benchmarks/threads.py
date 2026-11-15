"""Limit the numeric libraries to one thread.

Import this module before numpy, for its effect. Timings are then repeatable
and do not depend on how many CPUs the machine has. Each variable below is
read by one BLAS vendor, once, when its library is loaded.
"""
import os
import sys

VARIABLES = (
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)

# If numpy was loaded before this module with any variable unset, the limit
# cannot be relied on.
_in_time = "numpy" not in sys.modules or all(
    os.environ.get(variable) == "1" for variable in VARIABLES)

for variable in VARIABLES:
    os.environ[variable] = "1"


def blas_threads() -> int | None:
    """Return 1 if the one-thread limit is in effect, otherwise None."""
    return 1 if _in_time else None
