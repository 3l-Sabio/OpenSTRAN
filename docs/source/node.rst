Node Class
==========

The :class:`Node` class represents a single node (connection point) in the structural model. Nodes define the geometry of the structure and serve as attachment points for members and loads.

Overview
--------

Nodes are fundamental components that:

* Define the spatial coordinates of the structure
* Provide connection points for structural members
* Support applied loads and boundary conditions
* Store analysis results (displacements, reactions)

Each node has 6 degrees of freedom: 3 translational (Ux, Uy, Uz) and 3 rotational (φx, φy, φz).

Attributes
----------

Core Attributes
^^^^^^^^^^^^^^^

* **coordinates**: :class:`Coordinate` object defining (x, y, z) position
* **node_ID**: Unique integer identifier
* **mesh_node**: Boolean indicating if this is an internal mesh node
* **plane**: Plane constraint ('xy', 'yz', 'zx', or None for 3D)

Loads
^^^^^

* **Fx, Fy, Fz**: Applied forces in X, Y, Z directions (kips)
* **Mx, My, Mz**: Applied moments about X, Y, Z axes (kip-ft)
* **eFx, eFy, eFz, eMx, eMy, eMz**: Equivalent loads from member discretization

Boundary Conditions
^^^^^^^^^^^^^^^^^^^

* **restraint**: List of 6 integers [Ux, Uy, Uz, φx, φy, φz] where 1=restrained, 0=free

Analysis Results
^^^^^^^^^^^^^^^^

* **Ux, Uy, Uz**: Translational displacements (inches)
* **phi_x, phi_y, phi_z**: Rotational displacements (radians)
* **Rx, Ry, Rz**: Reaction forces (kips)
* **Rmx, Rmy, Rmz**: Reaction moments (kip-ft)

Basic Usage
-----------

Creating Nodes
^^^^^^^^^^^^^^

Nodes are typically created through the :class:`Nodes` collection:

.. code-block:: python

   from OpenSTRAN.Model import Model

   model = Model()

   # Add nodes at coordinates (x, y, z in feet)
   node1 = model.nodes.add_node(0, 0, 0)      # Origin
   node2 = model.nodes.add_node(10, 0, 0)     # 10 ft along X
   node3 = model.nodes.add_node(0, 8, 0)      # 8 ft along Y

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

   # Add concentrated forces
   node3.Fx = 5.0    # 5 kips in X direction
   node3.Fy = -10.0  # 10 kips downward (negative Y)
   node3.Fz = 2.5    # 2.5 kips in Z direction

   # Add moments using add_load method
   node3.add_load(15.0, 'moment', 'Z')  # 15 kip-ft moment about Z-axis

   # Note: moments are automatically converted from kip-ft to kip-in internally

Plane Constraints
-----------------

When a model has a plane constraint, nodes automatically receive appropriate restraints:

.. code-block:: python

   # 2D model in XY plane
   model_2d = Model(plane='xy')

   # Nodes automatically get out-of-plane restraint: [0, 0, 1, 1, 1, 0]
   # Free in X and Y, restrained in Z, free torsion, restrained in X and Y rotation

Available planes:
* ``'xy'``: Free in X/Y, restrained in Z
* ``'yz'``: Free in Y/Z, restrained in X
* ``'zx'``: Free in Z/X, restrained in Y

Analysis Results
----------------

After solving the model, nodes contain displacement and reaction results:

.. code-block:: python

   model.solve()

   # Displacements (inches)
   print(f"Node {node1.node_ID} displacements:")
   print(f"  Ux: {node1.Ux:.3f} in")
   print(f"  Uy: {node1.Uy:.3f} in")
   print(f"  Uz: {node1.Uz:.3f} in")

   # Reactions (only at restrained nodes)
   if not node1.mesh_node:  # Skip mesh nodes
       print(f"Node {node1.node_ID} reactions:")
       print(f"  Rx: {node1.Rx:.2f} kips")
       print(f"  Ry: {node1.Ry:.2f} kips")
       print(f"  Rz: {node1.Rz:.2f} kips")

Properties Access
-----------------

Access all node properties as a dictionary:

.. code-block:: python

   # Get all properties
   props = node1.properties()
   print(props.keys())
   # dict_keys(['coordinates', 'node_ID', 'mesh_node', 'Fx', 'Fy', 'Fz', ...])

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

* **Coordinates**: feet (ft)
* **Forces**: kips (1000 lbs)
* **Moments**: kip-feet (kip-ft)
* **Displacements**: inches (in)
* **Rotations**: radians (rad)

See Also
--------

* :class:`OpenSTRAN.Nodes.Nodes`: Collection of nodes
* :class:`OpenSTRAN.Coordinates.Coordinate`: Coordinate system
* :class:`OpenSTRAN.Model.Model`: Main model class