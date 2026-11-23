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
* **Solver**: the part of the solve spent in ``model.solver.solve``, with its share of the solve in brackets. This is assembling the stiffness matrix, solving for displacements, recovering reactions and member forces, and collecting them into the results, which includes finding the maximum member forces. The rest of the solve is meshing the members.
* **Peak memory**: the most memory the process used by the time the model was built and solved, including Python and the libraries it imported, measured in a separate process for each model.

Times are the best of several rounds, on one BLAS thread. Garbage collection is turned off while a build is timed, and the model of the previous round is collected before each timed solve. Before a model is timed it is solved once and checked for the right answers: the vertical reactions must sum to the applied gravity load, and the maximum deflection and moment must match expected values. For the beam these are the closed-form values; for the frames they are the values the dense solver gave at commit dec90cb.

Baseline results
----------------

These figures are from one machine, with the dense stiffness matrix and dense solve. They are a reference for before and after comparisons, not a statement of how fast OpenSTRAN is in general. The list and the table are the output of ``report.py``, whose library commit is the last commit that changed ``src/``.

* **Run on**: 2026-11-23
* **Library commit**: d141b0a
* **Python**: 3.14.10, numpy 2.5.3, scipy 1.18.1
* **CPU**: Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz, 6 logical CPUs, 1 BLAS thread
* **System**: Linux 6.18.33.1-microsoft-standard-WSL2

.. list-table::
   :header-rows: 1

   * - Model
     - Nodes
     - Free DoF
     - Build (ms)
     - Solve (ms)
     - Solver (ms)
     - Peak memory (MB)
   * - Simply supported beam, mesh 50
     - 51
     - 298
     - 0.020
     - 13.2
     - 5.3 (40%)
     - 64
   * - Portal frame, mesh 50
     - 151
     - 447
     - 0.037
     - 45.0
     - 12.3 (27%)
     - 71
   * - 2D frame, 3 bays x 3 stories, mesh 50
     - 1,045
     - 3,123
     - 0.193
     - 1,469
     - 640 (44%)
     - 594
   * - 2D frame, 10 bays x 10 stories, mesh 4
     - 751
     - 2,220
     - 3.1
     - 6,042
     - 376 (6%)
     - 335
   * - 3D frame, 2 x 2 bays x 2 stories, mesh 10
     - 405
     - 2,376
     - 0.441
     - 903
     - 300 (33%)
     - 239

Starting Python and importing OpenSTRAN, numpy and scipy takes about 57 MB.

The full test suite (11,991 tests, of which 48 are skipped) ran in 42 seconds on the same machine.
