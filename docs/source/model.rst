Model Class
===========

The :class:`Model` class is the primary container for a complete structural analysis model in OpenSTRAN. It manages the collection of nodes, members, and provides methods for solving the structural system and post-processing results.

Overview
--------

The Model class represents a three-dimensional space frame structural model. It serves as the main interface for:

* Creating and managing nodes and members
* Applying loads and boundary conditions
* Solving the structural system
* Post-processing analysis results

Key Features
------------

* **3D Analysis**: Full three-dimensional structural analysis capabilities
* **Multiple Element Types**: Supports 2D and 3D trusses and frames
* **Automatic Discretization**: Members are automatically discretized into submembers for accurate analysis
* **Load Analysis**: Supports various load types including point loads, distributed loads, and moments
* **Boundary Conditions**: Flexible restraint conditions at nodes
* **Post-Processing**: Comprehensive result extraction and reporting

Basic Usage
-----------

Creating a Model
^^^^^^^^^^^^^^^^

.. code-block:: python

   from OpenSTRAN import Model

   # Create a 3D model
   model = Model()

   # Create a 2D model constrained to the XY plane
   model_2d = Model(plane='xy')

Adding Nodes
^^^^^^^^^^^^

.. code-block:: python

   # Add nodes at specific coordinates (x, y, z in inches)
   N1 = model.nodes.add_node(0, 0, 0)      # Origin
   N2 = model.nodes.add_node(120, 0, 0)    # 120 in (10 ft) along X-axis
   N3 = model.nodes.add_node(120, 120, 0)  # 120 in along X and Y axes

Applying Boundary Conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Apply restraints: [Ux, Uy, Uz, Rx, Ry, Rz]
   # 1 = restrained (fixed), 0 = free
   N1.restraint = [1, 1, 1, 0, 0, 0]  # Pinned support
   N2.restraint = [1, 1, 1, 1, 1, 1]  # Fixed support

Adding Members
^^^^^^^^^^^^^^

.. code-block:: python

   from OpenSTRAN import Shape

   # Define material properties
   E = 29000  # ksi - Young's modulus for steel

   # Import cross-section properties
   shape = Shape("W12X14")  # W12x14 steel section

   # Add member between nodes
   M1 = model.members.add_member(N1, N2, shape=shape)

Applying Loads
^^^^^^^^^^^^^^

.. code-block:: python

   # Add distributed load (magnitude, direction, start %, end %)
   M1.add_distributed_load(-1/12, -1/12, 'Y', 0, 100)  # 1 kip/ft (1/12 kip/in) downward

Solving and Results
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Solve the structural system
   model.solve()

   # Display reactions
   model.reactions()

   # Calculate maximum deflections
   model.max_deflection()
   print(f"Maximum Y deflection: {model.Uy_max:.3f} inches")

Advanced Features
-----------------

Plane Constraints
^^^^^^^^^^^^^^^^^

Models can be constrained to 2D planes for simpler analysis:

.. code-block:: python

   # XY plane (common for building frames)
   model_xy = Model(plane='xy')

   # YZ plane
   model_yz = Model(plane='yz')

   # ZX plane
   model_zx = Model(plane='zx')

Member Releases
^^^^^^^^^^^^^^^

Members can have released connections at either end:

.. code-block:: python

   # Pinned connection at start node (member moments released about the minor and major axes)
   M1 = model.members.add_member(N1, N2, i_release=[0,0,0,0,1,1])

   # Pinned connection at both ends (member moments released about the minor and major axes)
   M2 = model.members.add_member(N2, N3, i_release=[0,0,0,0,1,1], j_release=[0,0,0,0,1,1])

Custom Cross-Sections
^^^^^^^^^^^^^^^^^^^^^

Use custom material properties instead of standard shapes:

.. code-block:: python

   # Define custom section properties
   E = 29000    # ksi
   A = 10.0     # in²
   Ixx = 100.0  # in⁴ (strong axis)
   Iyy = 50.0   # in⁴ (weak axis)
   G = 12000    # ksi
   J = 5.0      # in⁴ (torsional)

   M1 = model.members.add_member(N1, N2, E=E, A=A, Ixx=Ixx, Iyy=Iyy, G=G, J=J)

Second-Order Analysis
^^^^^^^^^^^^^^^^^^^^^

A second-order (P-Delta) analysis includes the effect of axial forces on
member stiffness. It starts from the first-order solution. Equilibrium is
formulated on the undeformed geometry, and each iteration solves
``[Ke + Kg(N)] {U} = {F}``, the elastic plus geometric stiffness with the
axial forces N of the previous iteration.

The second-order analysis uses the load control method of McGuire et al.
(Equations 12.11 and 12.16, as a single load increment) with the geometry
held fixed. The iteration stops when the unbalanced load is below ``tolerance``
times the applied loads.

.. code-block:: python

   model.solve(second_order=True)

   # Optional convergence settings (defaults shown)
   model.solve(second_order=True, tolerance=1e-8, max_iterations=50)

   # Iterations used by the last second-order analysis
   print(model.solver.iterations)

Results are stored in the same node and member fields as a first-order
analysis. Member end forces include the geometric stiffness, and the
moments along each submember (``Member.moment()`` and the maxima found by
``maxMbrForces()``) include the moment of the axial force about the
deflected axis.

A ``RuntimeError`` is raised if the iteration does not converge, or if the
tangent stiffness stops being positive definite. The second case means the
loads are most likely at or above the second-order limit load. That limit
can be lower than the elastic critical load below, because the axial forces
change as the structure deflects: the portal frame of McGuire et al.,
Example 9.6, modeled with two-element columns and one-element girders, has a
critical load factor of 2.20, but its P-Delta analysis fails between 2.06
and 2.07 times the loads.

A ``ValueError`` is raised if the elastic stiffness is singular. The error 
names a node that has no stiffness against some of its unrestrained degrees
of freedom, for example the rotation of a joint at which every member is 
released, or reports that the structure is a unstable. 

If a ``ValueError`` is raised, a first-order analysis still solves such a model
with a ``LinAlgWarning``. After such an error, or if the analysis is interrupted, 
the model holds the first-order solution.

Elastic Critical Load
^^^^^^^^^^^^^^^^^^^^^

The elastic critical load factor is the smallest factor by which the applied
loads can be multiplied before the structure buckles. It solves the
eigenproblem ``[Ke + lambda Kg] {d} = 0``, with the geometric stiffness
``Kg`` formed from the first-order axial forces:

.. code-block:: python

   factor = model.critical_load_factor()
   print(f"The structure buckles at {factor:.2f} times the applied loads")

``Kg`` here leaves out the axial terms of the geometric stiffness, which
only reduce axial stiffness and would otherwise give a meaningless factor
``EA/|N|`` when no bending or twisting mode is free. Axial forces at the
level of rounding error are treated as zero. A ``ValueError`` is raised if
the applied loads put no member in compression, if every member in
compression is restrained against bending and twisting, or if the elastic
stiffness is singular, as above. The model is left holding
the first-order solution under the applied loads.

Known Issue: Released Members
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Second-order results and critical loads near an end release are
approximate when a member is released at one end only, or when the released
submember carries a distributed load.

Use several submembers (the default mesh is 50) for released members in
second-order and critical load analyses.

Result Post-Processing
----------------------

The Model class provides comprehensive post-processing capabilities:

Reaction Forces
^^^^^^^^^^^^^^^

.. code-block:: python

   # Solve and get maximum reactions
   model.solve()
   model.maxReactions()

   print(f"Max X reaction: {model.Rx_max:.2f} kips")
   print(f"Max Y reaction: {model.Ry_max:.2f} kips")
   print(f"Max Z reaction: {model.Rz_max:.2f} kips")

Member Forces
^^^^^^^^^^^^^

.. code-block:: python

   # Get maximum member forces
   model.maxMbrForces()

   print(f"Max axial force: {model.axial_max:.2f} kips")
   print(f"Max shear force: {model.Vy_max:.2f} kips")
   print(f"Max moment: {model.Mzz_max:.2f} kip-in")

Deflections
^^^^^^^^^^^

.. code-block:: python

   # Calculate maximum deflections
   model.max_deflection()

   print(f"Max X deflection: {model.Ux_max:.3f} inches")
   print(f"Max Y deflection: {model.Uy_max:.3f} inches")
   print(f"Max Z deflection: {model.Uz_max:.3f} inches")

Units
-----

OpenSTRAN does not convert units. Units must be entered per the reference unit table below:

* **Length**: inches (in) for node coordinates, brace locations, member dimensions and deflections
* **Force**: kips (1000 lbs)
* **Distributed load**: kips per inch
* **Moment**: kip-inches (kip-in) for moments applied to nodes and for results
* **Stress**: ksi (1000 psi)
* **Modulus**: ksi

Limitations
-----------

* Elastic analysis only; second-order analysis is P-Delta on the undeformed
  geometry (no large displacements)
* Second-order results near a release are approximate with a coarse mesh
  when the member is released at one end only or carries a distributed
  load (see the known issue above)
* Neglects shear and torsional deformations
* No matrix sparseness optimization
* No unit conversion; inputs are in inches and kips

See Also
--------

* :class:`OpenSTRAN.Nodes.Nodes`: Node collection management
* :class:`OpenSTRAN.Members.Members`: Member collection management
* :class:`OpenSTRAN.Node.Node`: Individual node class
* :class:`OpenSTRAN.Member.Member`: Individual member class