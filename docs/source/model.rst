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

   from OpenSTRAN.Model import Model

   # Create a 3D model
   model = Model()

   # Create a 2D model constrained to the XY plane
   model_2d = Model(plane='xy')

Adding Nodes
^^^^^^^^^^^^

.. code-block:: python

   # Add nodes at specific coordinates (x, y, z in feet)
   N1 = model.nodes.add_node(0, 0, 0)    # Origin
   N2 = model.nodes.add_node(10, 0, 0)   # 10 ft along X-axis
   N3 = model.nodes.add_node(10, 10, 0)  # 10 ft along X and Y axes

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

   from OpenSTRAN.Database.Shape import Shape

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
   M1.add_distributed_load(-1, -1, 'Y', 0, 100)  # 1 kip/ft downward

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

   # Pinned connection at start node
   M1 = model.members.add_member(N1, N2, i_release=True)

   # Pinned connection at both ends
   M2 = model.members.add_member(N2, N3, i_release=True, j_release=True)

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
   print(f"Max moment: {model.Mzz_max:.2f} kip-ft")

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

OpenSTRAN uses Imperial units throughout:

* **Length**: feet (ft) for coordinates, inches (in) for member dimensions
* **Force**: kips (1000 lbs)
* **Moment**: kip-feet (kip-ft)
* **Stress**: ksi (1000 psi)
* **Modulus**: ksi

Limitations
-----------

* First-order elastic analysis only
* Neglects shear and torsional deformations
* No matrix sparseness optimization
* Imperial units only

See Also
--------

* :class:`OpenSTRAN.Nodes.Nodes`: Node collection management
* :class:`OpenSTRAN.Members.Members`: Member collection management
* :class:`OpenSTRAN.Node.Node`: Individual node class
* :class:`OpenSTRAN.Member.Member`: Individual member class