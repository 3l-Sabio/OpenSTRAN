Node Class
==========

The :class:`Node` class represents a single node (connection point) in the structural model. Nodes define the geometry of the structure and serve as attachment points for members and loads.

Overview
--------

Nodes are fundamental components that:

* Define the spatial coordinates of the structure
* Provide connection points for structural members
* Support applied loads and boundary conditions

Each node has 6 degrees of freedom: 3 translational (Ux, Uy, Uz) and 3 rotational (φx, φy, φz).

A node's displacements and reactions are not stored on the node; they are
read from the results of an analysis, ``results.node(node)`` (see
`Analysis Results`_).

Attributes
----------

Core Attributes
^^^^^^^^^^^^^^^

* **coordinates**: :class:`Coordinate` object defining (x, y, z) position
* **node_ID**: Unique integer identifier
* **mesh_node**: Boolean indicating if this is an internal mesh node
* **plane**: Plane constraint ('xy', 'yz', 'zx', or None for 3D)

Boundary Conditions
^^^^^^^^^^^^^^^^^^^

* **restraint**: List of 6 integers [Ux, Uy, Uz, φx, φy, φz] where 1=restrained, 0=free

Loads
^^^^^

* **loads**: The model's loads, ``model.loads``, to which ``add_load`` adds.
  Loads are not stored on the node itself.

Basic Usage
-----------

Creating Nodes
^^^^^^^^^^^^^^

Nodes are typically created through the :class:`Nodes` collection:

.. code-block:: python

   from OpenSTRAN import Model

   model = Model()

   # Add nodes at coordinates (x, y, z in inches)
   node1 = model.nodes.add_node(0, 0, 0)      # Origin
   node2 = model.nodes.add_node(120, 0, 0)    # 120 in (10 ft) along X
   node3 = model.nodes.add_node(0, 96, 0)     # 96 in (8 ft) along Y

Applying Boundary Conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Method 1: Direct assignment
   node1.restraint = [1, 1, 1, 0, 0, 0]  # Pinned: fixed translation, free rotation

   # Method 2: Using add_restraint method
   node2.add_restraint([1, 1, 1, 1, 1, 1])  # Fixed: all DOF restrained

Common restraint patterns:

* **Pinned support**: ``[1, 1, 1, 0, 0, 0]`` - Fixed in translation, free in rotation
* **Fixed support**: ``[1, 1, 1, 1, 1, 1]`` - All degrees of freedom restrained
* **Roller X**: ``[0, 1, 1, 0, 0, 0]`` - Free in X, fixed in Y and Z translation
* **Roller Y**: ``[1, 0, 1, 0, 0, 0]`` - Free in Y, fixed in X and Z translation

Applying Loads
^^^^^^^^^^^^^^

.. code-block:: python

   # Add concentrated forces (kips) along the global axes
   node3.add_load(5.0, 'force', 'X')    # 5 kips in X direction
   node3.add_load(-10.0, 'force', 'Y')  # 10 kips downward (negative Y)
   node3.add_load(2.5, 'force', 'Z')    # 2.5 kips in Z direction

   # Add a moment (kip-in)
   node3.add_load(180.0, 'moment', 'Z')  # 180 kip-in (15 kip-ft) moment about Z-axis

Loads on the same node add up. The type must be ``'force'`` or
``'moment'``, and the direction a global axis written in upper case, ``'X'``,
``'Y'`` or ``'Z'``; any other value raises a ``ValueError``.
``node3.add_load(5.0, 'force', 'X')`` is the same as
``model.loads.add_nodal_load(node3, 5.0, 'force', 'X')``.

Plane Constraints
-----------------

When a model has a plane constraint, nodes automatically receive appropriate restraints:

.. code-block:: python

   # 2D model in XY plane
   model_2d = Model(plane='xy')

   # Nodes automatically get out-of-plane restraint: [0, 0, 1, 1, 1, 0]
   # Free to move in X and Y and to rotate about Z; restrained in Z and
   # against rotation about X and Y

Available planes:
* ``'xy'``: Free in X/Y, restrained in Z
* ``'yz'``: Free in Y/Z, restrained in X
* ``'zx'``: Free in Z/X, restrained in Y

Analysis Results
----------------

``model.solve()`` returns the results of the analysis, which give each
node's displacements and reactions:

.. code-block:: python

   results = model.solve()
   r = results.node(node1)

   # Displacements (inches) and rotations (radians)
   print(f"Node {node1.node_ID} displacements:")
   print(f"  Ux: {r.Ux:.3f} in")
   print(f"  Uy: {r.Uy:.3f} in")
   print(f"  Uz: {r.Uz:.3f} in")
   print(f"  phi_z: {r.phi_z:.5f} rad")

   # Reactions (zero at unrestrained degrees of freedom)
   print(f"Node {node1.node_ID} reactions:")
   print(f"  Rx: {r.Rx:.2f} kips")
   print(f"  Ry: {r.Ry:.2f} kips")
   print(f"  Rz: {r.Rz:.2f} kips")
   print(f"  Rmz: {r.Rmz:.2f} kip-in")

Properties Access
-----------------

Access all node properties as a dictionary:

.. code-block:: python

   # Get all properties
   props = node1.properties()
   print(f"Node {props['node_ID']}, mesh node: {props['mesh_node']}")
   print(f"Restraint: {props['restraint']}")

Degrees of Freedom
------------------

Each node has 6 degrees of freedom:

1. **Ux**: Translation in X direction
2. **Uy**: Translation in Y direction
3. **Uz**: Translation in Z direction
4. **φx**: Rotation about X axis
5. **φy**: Rotation about Y axis
6. **φz**: Rotation about Z axis

The restraint list corresponds to these DOF in order.

Units
-----

* **Coordinates**: inches (in)
* **Forces**: kips (1000 lbs)
* **Moments**: kip-inches (kip-in) for ``add_load`` and reaction moments
* **Displacements**: inches (in)
* **Rotations**: radians (rad)

See Also
--------

* :class:`OpenSTRAN.Nodes.Nodes`: Collection of nodes
* :class:`OpenSTRAN.Coordinates.Coordinate`: Coordinate system
* :class:`OpenSTRAN.Model.Model`: Main model class
* :class:`OpenSTRAN.Results.Results`: Results of an analysis