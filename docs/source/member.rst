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
* **Cb**: Lateral-torsional buckling coefficient (calculated)

Internal Structure
^^^^^^^^^^^^^^^^^^

* **count**: Number of submembers created
* **submembers**: Dictionary of :class:`SubMember` objects

Basic Usage
-----------

Creating Members
^^^^^^^^^^^^^^^^

Members are typically created through the :class:`Members` collection:

.. code-block:: python

   from OpenSTRAN.Model import Model
   from OpenSTRAN.Database.Shape import Shape

   model = Model()

   # Create nodes
   N1 = model.nodes.add_node(0, 0, 0)
   N2 = model.nodes.add_node(10, 0, 0)

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

Members are automatically divided into submembers for analysis:

.. code-block:: python

   # Create member with 20 submembers
   M1 = model.members.add_member(N1, N2, mesh=20)

   print(f"Member length: {M1.length:.1f} inches")
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

   # Custom bracing locations (as fraction of length)
   M5 = model.members.add_member(N1, N2, bracing=[0.25, 0.5, 0.75])

Buckling Analysis
-----------------

The lateral-torsional buckling coefficient Cb is automatically calculated:

.. code-block:: python

   # After solving the model
   model.solve()

   # Calculate Cb for buckling analysis
   cb_value = M1.calculate_Cb()
   print(f"Cb coefficient: {cb_value:.3f}")

Applying Loads
--------------

Loads are applied to members through various methods:

.. code-block:: python

   # Distributed load along member
   M1.add_distributed_load(-1.0, -1.0, 'Y', 0, 100)  # 1 kip/ft downward

   # Point load at specific location
   M1.add_point_load(5.0, 'Y', 50)  # 5 kips downward at midspan

   # Moment load
   M1.add_moment_load(10.0, 25)  # 10 kip-ft at 25% of length

Cross-Section Properties
------------------------

Using the Shape Database
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OpenSTRAN.Database.Shape import Shape

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

After solving, member results are available through submembers:

.. code-block:: python

   model.solve()

   # Access results from submembers
   for submember in M1.submembers.values():
       axial = submember.results['axial']
       shear = submember.results['shear']
       moment = submember.results['major axis moments']

       print(f"Axial force: {axial[0]:.2f} kips")
       print(f"Shear force: {shear[0]:.2f} kips")
       print(f"Moment: {moment[0]:.2f} kip-ft")

Properties Access
-----------------

.. code-block:: python

   # Get all member properties
   props = M1.properties()
   print(f"Member length: {props['length']:.1f} inches")
   print(f"Young's modulus: {props['E']:.0f} ksi")

Units
-----

* **Length**: inches (in) for dimensions, feet (ft) for coordinates
* **Force**: kips
* **Moment**: kip-inches (automatically converted)
* **Stress/Modulus**: ksi (1000 psi)

Performance Notes
-----------------

* Higher mesh values increase accuracy but slow analysis
* Submembers are created automatically during initialization

See Also
--------

* :class:`OpenSTRAN.Members.Members`: Collection of members
* :class:`OpenSTRAN.Submember.SubMember`: Individual submember class
* :class:`OpenSTRAN.Database.Shape.Shape`: Cross-section database
* :class:`OpenSTRAN.Model.Model`: Main model class