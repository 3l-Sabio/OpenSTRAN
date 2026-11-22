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

Loads are kept in ``model.loads`` (a :class:`~OpenSTRAN.Loads.Loads`
object), in the order they were added, and are applied each time the model
is solved. A load added after a solve therefore counts in the next one, as
long as it lands on existing nodes: members are meshed at the first solve, so
a point load at a new location adds a node that no member is connected to.
Adding a load never replaces one: ``model.loads.clear()`` removes every load,
so that the model can be loaded differently. The nodes that member loads
created stay in the model.

Loads can also be added to ``model.loads`` directly, with
``add_nodal_load(node, ...)``, ``add_point_load(member, ...)`` and
``add_distributed_load(member, ...)``. They take the same arguments as the
node and member methods, after the node or member, and check them in the
same way. A node or member of another model raises a ``ValueError``.

Solving and Results
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Solve the structural system
   results = model.solve()

   # Display reactions
   model.reactions()

   # Maximum deflection
   print(f"Maximum Y deflection: {results.Uy_max:.3f} inches")

``solve()`` returns the results of the analysis; see `Results`_ below.

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

   results = model.solve(second_order=True)

   # Optional convergence settings (defaults shown)
   results = model.solve(second_order=True, tolerance=1e-8, max_iterations=50)

   # Iterations used by the second-order analysis
   print(results.iterations)

The results have the same form as those of a first-order analysis, with
``results.second_order`` set to ``True``. Member end forces include the
geometric stiffness, and the moments along each member
(``results.member(M1).moment()``, the submember extrema and
``results.Mzz_max``) include the moment of the axial force about the
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
the model keeps the results of its previous analysis, if any.

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
stiffness is singular, as above. The results of the model are left as they
were.

Known Issue: Released Members
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Second-order results and critical loads near an end release are
approximate when a member is released at one end only, or when the released
submember carries a distributed load.

Use several submembers (the default mesh is 50) for released members in
second-order and critical load analyses.

Results
-------

``solve()`` returns a :class:`~OpenSTRAN.Results.Results` object, which the
model also keeps as ``model.results``. It holds the displacements and
reactions of every node, and the end forces and internal forces of every
member, for that analysis:

* It does not change when the model is solved again, or when
  ``critical_load_factor()`` runs, so the results of several analyses can be
  kept side by side.
* It cannot be modified.
* If a solve fails or is interrupted, it raises, and ``model.results`` keeps
  the results of the previous analysis (``None`` before the first).

.. code-block:: python

   first = model.solve()
   second = model.solve(second_order=True)

   print(first.second_order, second.second_order)  # False True
   print(model.results is second)                  # True

Nodes
^^^^^

.. code-block:: python

   r = results.node(N1)
   print(f"Uy = {r.Uy:.4f} in, phi_z = {r.phi_z:.5f} rad")
   print(f"Ry = {r.Ry:.2f} kips, Rmz = {r.Rmz:.2f} kip-in")

Each node result has the translations ``Ux``, ``Uy`` and ``Uz`` (inches),
the rotations ``phi_x``, ``phi_y`` and ``phi_z`` (radians), and the
reactions ``Rx``, ``Ry``, ``Rz`` (kips) and ``Rmx``, ``Rmy``, ``Rmz``
(kip-in). Reactions are zero at unrestrained degrees of freedom.
``results.node()`` raises a ``KeyError`` for a node that was not part of
the analysis, such as one added after it.

``model.reactions()`` prints the reactions of the last analysis at the nodes
you added and at any mesh node with a support.

Members
^^^^^^^

.. code-block:: python

   member = results.member(M1)

   # Internal forces at a location along the span, in percent
   print(member.moment(50))           # major-axis moment, kip-in
   print(member.moment(50, 'minor'))  # minor-axis moment, kip-in
   print(member.shear(25))            # major-axis shear, kips

   # End forces and internal force extrema of each submember
   for sub in member.submembers:
       print(sub.forces['axial'])                         # (i end, j end)
       print(sub.force_extrema()['major axis moments'])   # (largest, smallest)

``moment()`` and ``shear()`` evaluate the exact internal forces, between mesh
nodes too. The end forces of a submember are the forces the nodes apply to
its ends, in local coordinates, under the keys ``'axial'``, ``'shear'``,
``'transverse shear'``, ``'torsional moments'``, ``'minor axis moments'``
and ``'major axis moments'``.

The lateral-torsional buckling coefficient of a member comes from the
moments of the analysis and the member's ``bracing``:

.. code-block:: python

   cb = results.member(M1).calculate_Cb()

Maxima
^^^^^^

The largest absolute values in the model are properties of the results:

.. code-block:: python

   print(f"Max Y reaction: {results.Ry_max:.2f} kips")
   print(f"Max moment: {results.Mzz_max:.2f} kip-in")
   print(f"Max Y deflection: {results.Uy_max:.3f} inches")

* Reactions: ``Rx_max``, ``Ry_max``, ``Rz_max``, ``Rmx_max``, ``Rmy_max``,
  ``Rmz_max``
* Translations: ``Ux_max``, ``Uy_max``, ``Uz_max``
* Member forces: ``axial_max``, ``torque_max``, ``Vy_max``, ``Vz_max``,
  ``Mzz_max``, ``Myy_max``

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
* :class:`OpenSTRAN.Results.Results`: Results of an analysis
* :class:`OpenSTRAN.Loads.Loads`: Loads applied to the model