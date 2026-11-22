Member Class
============

The :class:`Member` class represents a structural member (element) connecting two nodes in the model. Members are automatically discretized into submembers for finite element analysis.

Overview
--------

Members are the primary structural elements that:

* Connect two nodes to form the structural skeleton
* Carry loads through axial, shear, and moment forces
* Are automatically discretized into submembers for analysis
* Support various boundary conditions and material properties
* Include lateral bracing considerations for buckling analysis

Each member is divided into multiple submembers for accurate finite element analysis.

Attributes
----------

Core Attributes
^^^^^^^^^^^^^^^

* **nodes**: Reference to the global :class:`Nodes` collection
* **node_i, node_j**: Start and end :class:`Node` objects
* **length**: Calculated member length (inches)
* **shape**: :class:`Shape` object with cross-section properties

Material Properties
^^^^^^^^^^^^^^^^^^^

* **E**: Young's modulus (ksi)
* **G**: Shear modulus (ksi)
* **A**: Cross-sectional area (in²)
* **Ixx**: Moment of inertia about strong axis (in⁴)
* **Iyy**: Moment of inertia about weak axis (in⁴)
* **J**: Polar moment of inertia (torsional) (in⁴)

Boundary Conditions
^^^^^^^^^^^^^^^^^^^

* **i_release, j_release**: list of released degrees of freedom [Ux, Uy, Uz, φx, φy, φz]

Analysis Parameters
^^^^^^^^^^^^^^^^^^^

* **mesh**: Number of submember divisions
* **bracing**: Lateral bracing configuration

Internal Structure
^^^^^^^^^^^^^^^^^^

* **count**: Number of submembers created
* **submembers**: Dictionary of :class:`SubMember` objects, created when the
  model is first solved

Basic Usage
-----------

Creating Members
^^^^^^^^^^^^^^^^

Members are typically created through the :class:`Members` collection:

.. code-block:: python

   from OpenSTRAN import Model
   from OpenSTRAN import Shape

   model = Model()

   # Create nodes
   N1 = model.nodes.add_node(0, 0, 0)
   N2 = model.nodes.add_node(120, 0, 0)

   # Method 1: Using shape database
   shape = Shape("W12X14")  # Standard steel section
   M1 = model.members.add_member(N1, N2, shape=shape)

   # Method 2: Custom properties
   M2 = model.members.add_member(
       N1, N2,
       E=29000,      # ksi
       A=10.0,       # in²
       Ixx=100.0,    # in⁴
       Iyy=50.0,     # in⁴
       G=12000,      # ksi
       J=5.0         # in⁴
   )

Boundary Conditions
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Fixed-fixed member (default)
   M1 = model.members.add_member(N1, N2)

   # Pinned-fixed member
   M2 = model.members.add_member(N1, N2, i_release=[0,0,0,0,1,1])

   # Pinned-pinned member
   M3 = model.members.add_member(N1, N2, i_release=[0,0,0,0,1,1], j_release=[0,0,0,0,1,1])

Member Discretization
---------------------

Members are automatically divided into submembers when the model is first
solved, so that the nodes created by loads are part of the mesh.
``M1.add_node(50)`` adds a node at midspan, or returns the node already
there; added before the first solve, it becomes part of the mesh, and its
displacements can be read from the results.

.. code-block:: python

   # Create member with 20 submembers
   M1 = model.members.add_member(N1, N2, mesh=20)
   print(f"Member length: {M1.length:.1f} inches")

   model.solve()
   print(f"Number of submembers: {M1.count}")

   # Access individual submembers
   for sub_id, submember in M1.submembers.items():
       print(f"Submember {sub_id}: {submember.length:.2f} inches")

Lateral Bracing
---------------

Members can have different lateral bracing configurations affecting buckling:

.. code-block:: python

   # Continuous bracing (default)
   M1 = model.members.add_member(N1, N2, bracing="continuous")

   # Quarter-point bracing
   M2 = model.members.add_member(N1, N2, bracing="quarter")

   # Third-point bracing
   M3 = model.members.add_member(N1, N2, bracing="third")

   # Midspan bracing
   M4 = model.members.add_member(N1, N2, bracing="midspan")

   # Custom bracing locations (distance from the start node in inches)
   M5 = model.members.add_member(N1, N2, bracing=[30, 60, 90])

Buckling Analysis
-----------------

The lateral-torsional buckling coefficient Cb is calculated from the moments
of an analysis, with the member's bracing:

.. code-block:: python

   results = model.solve()

   # Calculate Cb for buckling analysis
   cb_value = results.member(M1).calculate_Cb()
   print(f"Cb coefficient: {cb_value:.3f}")

Known issue: Cb is computed from moments interpolated linearly between mesh
nodes. It is wrong when a quarter point of an unbraced span falls on a mesh
node, and it raises an ``IndexError`` for a member whose start node has the
larger coordinates, for ``bracing=[]``, or for a member shorter than 18 in
with the default ``'continuous'`` bracing. A member with no major-axis
moment gives ``nan``, with a ``RuntimeWarning``.

Applying Loads
--------------

Loads are applied to members through various methods:

.. code-block:: python

   # Distributed load along member
   M1.add_distributed_load(-1/12, -1/12, 'Y', 0, 100)  # 1 kip/ft (1/12 kip/in) downward

   # Point load at specific location
   M1.add_point_load(-5.0, 'Y', 50)  # 5 kips downward at midspan

Moments are applied to nodes with ``Node.add_load``.
Member loads are recorded in the model's loads (``model.loads``) and applied
each time the model is solved. Directions are global (``'X'``, ``'Y'``,
``'Z'``) or local to the member (``'x'``, ``'y'``, ``'z'``); any other value
raises a ``ValueError``. ``M1.add_point_load(-5.0, 'Y', 50)`` is the same as
``model.loads.add_point_load(M1, -5.0, 'Y', 50)``.

Cross-Section Properties
------------------------

Using the Shape Database
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OpenSTRAN import Shape

   # Common steel sections
   w14x30 = Shape("W14X30")
   w12x14 = Shape("W12X14")
   tube = Shape("TUB2X2X0.25")

   # Access properties
   print(f"Area: {w14x30.A} in²")
   print(f"Ix: {w14x30.Ix} in⁴")
   print(f"Iy: {w14x30.Iy} in⁴")

Custom Properties
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Define custom rectangular section
   b = 12.0   # width (in)
   h = 24.0   # height (in)
   A = b * h
   Ixx = b * h**3 / 12    # strong axis
   Iyy = h * b**3 / 12    # weak axis
   J = 0.5 * (b + h) * min(b, h)**3  # approximate torsional

   M1 = model.members.add_member(N1, N2, A=A, Ixx=Ixx, Iyy=Iyy, J=J)

Analysis Results
----------------

``model.solve()`` returns the results of the analysis, which give each
member's internal forces along its span and the end forces of its
submembers:

.. code-block:: python

   results = model.solve()
   member = results.member(M1)

   # Internal forces at a location along the span, in percent
   print(f"Moment at midspan: {member.moment(50):.2f} kip-in")
   print(f"Shear at quarter span: {member.shear(25):.2f} kips")

   # End forces of each submember, (i end, j end)
   for sub in member.submembers:
       axial = sub.forces['axial']
       shear = sub.forces['shear']
       moment = sub.forces['major axis moments']

       print(f"Axial force: {axial[0]:.2f} kips")
       print(f"Shear force: {shear[0]:.2f} kips")
       print(f"Moment: {moment[0]:.2f} kip-in")

See the Results section of the model documentation for the other values.

Properties Access
-----------------

.. code-block:: python

   # Get all member properties
   props = M1.properties()
   print(f"Member length: {props['length']:.1f} inches")
   print(f"Young's modulus: {props['E']:.0f} ksi")

Units
-----

* **Length**: inches (in) for node coordinates, brace locations, section dimensions and member ``length``
* **Force**: kips
* **Distributed load**: kips per inch
* **Moment**: kip-inches
* **Stress/Modulus**: ksi (1000 psi)

Performance Notes
-----------------

* Higher mesh values slow analysis. Internal forces are exact between mesh
  nodes, but displacements (and so ``Uy_max``) are found only at nodes, and
  second-order results and Cb depend on the mesh
* Submembers are created when the model is first solved

See Also
--------

* :class:`OpenSTRAN.Members.Members`: Collection of members
* :class:`OpenSTRAN.Submember.SubMember`: Individual submember class
* :class:`OpenSTRAN.Database.Shape.Shape`: Cross-section database
* :class:`OpenSTRAN.Model.Model`: Main model class
* :class:`OpenSTRAN.Results.MemberResult`: Results of a member