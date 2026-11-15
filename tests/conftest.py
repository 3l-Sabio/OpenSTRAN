import os

# the BLAS thread pool is set to 1 at the module level before numpy is imported
# so matrix mathematical operations ran by the test suite do not use more than
# a single CPU.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
