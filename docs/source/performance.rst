Performance
===========

OpenSTRAN ships a small set of benchmarks that time building and solving a range of models. They exist so that a change to the solver can be measured before and after on the same machine.

Running the benchmarks
----------------------

The benchmarks use `pytest-benchmark <https://pytest-benchmark.readthedocs.io/>`_, which is installed with the development requirements. They are kept out of the normal test run and only start when asked for:

.. code-block:: bash

   pip install -r requirements-dev.txt
   pytest benchmarks

A run takes about a minute. To keep a run for later comparison, save it:

.. code-block:: bash

   pytest benchmarks --benchmark-save=baseline

The run is written to ``.benchmarks/<platform>/0001_baseline.json``. Saved runs are numbered in the order they are made and are not committed, so ``0001`` is the first run saved on your own machine. After changing the library, compare against it:

.. code-block:: bash

   pytest benchmarks --benchmark-compare=0001 --benchmark-group-by=fullname

To print a saved run as the table shown below:

.. code-block:: bash

   python benchmarks/report.py .benchmarks/<platform>/0001_baseline.json

The models
----------

Every model uses a W12X14 section, 240 inch beams and 144 inch columns, with a uniform gravity load on each beam. The frames also carry a lateral load at the top. Each model sets its mesh explicitly, so its size does not depend on the default mesh.

* **Simply supported beam**: the kind of model the test suite solves thousands of times.
* **Portal frame**: a small frame of three members.
* **2D frame, 3 bays x 3 stories, mesh 50**: the largest system of equations, which stresses the linear solve and memory.
* **2D frame, 10 bays x 10 stories, mesh 4**: a large number of members, which stresses meshing.
* **3D frame, 2 x 2 bays x 2 stories, mesh 10**: three-dimensional connectivity.

What is measured
----------------

* **Free DoF**: the degrees of freedom left after restraints, which is the size of the system that is solved. Every node has six degrees of freedom, and a plane model restrains three of them at every node.
* **Build**: the time to create the nodes, members and loads. The section is looked up in the database once beforehand, outside the timing.
* **Solve**: the time for ``model.solve()`` on a freshly built model. This includes meshing the members, assembling and solving the linear system, and finding the maximum member forces.
* **Linear system**: the part of the solve spent assembling the stiffness matrix, solving for displacements and recovering reactions and member forces, with its share of the solve in brackets.
* **Peak memory**: the most memory the process used while building and solving the model, measured in a separate process for each model.

Times are the best of several rounds, on one BLAS thread. Before a model is timed it is solved once and checked for the right answers: the vertical reactions must sum to the applied gravity load, and the maximum deflection and moment must match expected values. For the beam these are the closed-form values; for the frames they are the values the dense solver gave at the baseline commit.

Baseline results
----------------

These figures are from one machine. They are a reference for before and after comparisons, not a statement of how fast OpenSTRAN is in general.

* **Run on**: 2026-11-15
* **Library commit**: dec90cb (dense stiffness matrix and dense solve)
* **Python**: 3.14.10, numpy 2.5.3, scipy 1.18.1
* **CPU**: Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz, 6 cores, 1 BLAS thread
* **System**: Linux 6.18.33.1-microsoft-standard-WSL2

.. list-table::
   :header-rows: 1

   * - Model
     - Nodes
     - Free DoF
     - Build (ms)
     - Solve (ms)
     - Linear system (ms)
     - Peak memory (MB)
   * - Simply supported beam, mesh 50
     - 51
     - 298
     - 0.018
     - 34.7
     - 2.7 (8%)
     - 64
   * - Portal frame, mesh 50
     - 151
     - 447
     - 0.033
     - 110
     - 10.6 (10%)
     - 73
   * - 2D frame, 3 bays x 3 stories, mesh 50
     - 1,045
     - 3,123
     - 0.179
     - 2,192
     - 909 (41%)
     - 597
   * - 2D frame, 10 bays x 10 stories, mesh 4
     - 751
     - 2,220
     - 2.9
     - 6,273
     - 516 (8%)
     - 338
   * - 3D frame, 2 x 2 bays x 2 stories, mesh 10
     - 405
     - 2,376
     - 0.403
     - 1,115
     - 378 (34%)
     - 242

Importing the library alone takes about 58 MB.

The full test suite (11,852 tests, of which 48 are skipped) ran in 83 seconds on the same machine.
