Nodes Class
===========

The :class:`Nodes` class is a collection container that manages all nodes in the structural model. It provides methods for adding, finding, and organizing nodes within the model geometry.

Overview
--------

The Nodes class serves as the central repository for all node objects in a model. Key responsibilities include:

* Creating and storing node objects
* Preventing duplicate nodes at the same location
* Providing coordinate-based node lookup
* Maintaining node numbering and counting
* Supporting plane constraints for 2D models

Attributes
----------

* **plane**: Plane constraint ('xy', 'yz', 'zx', or None for 3D)
* **count**: Total number of nodes added
* **nodes**: Dictionary mapping node IDs to :class:`Node` objects
* **x, y, z**: Lists of all node coordinates (for convenience)

Basic Usage
-----------

Creating a Nodes Collection
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Nodes collection is automatically created when instantiating a :class:`Model`:

.. code-block:: python

   from OpenSTRAN.Model import Model

   # 3D model
   model = Model()
   nodes = model.nodes  # Nodes collection

   # 2D model with plane constraint
   model_2d = Model(plane='xy')
   nodes_2d = model_2d.nodes

Adding Nodes
^^^^^^^^^^^^

.. code-block:: python

   # Add nodes at specific coordinates (x, y, z in feet)
   N1 = nodes.add_node(0, 0, 0)      # Node at origin
   N2 = nodes.add_node(10, 0, 0)     # 10 ft along X-axis
   N3 = nodes.add_node(10, 8, 0)     # 10 ft X, 8 ft Y
   N4 = nodes.add_node(0, 8, 0)      # 8 ft along Y-axis

Duplicate Prevention
^^^^^^^^^^^^^^^^^^^^

The :meth:`add_node` method automatically prevents duplicate nodes:

.. code-block:: python

   # These create the same node
   N1 = nodes.add_node(5, 5, 5)
   N2 = nodes.add_node(5, 5, 5)  # Returns existing node N1

   print(N1 is N2)  # True - same object

Finding Nodes
^^^^^^^^^^^^^

Locate existing nodes by coordinates:

.. code-block:: python

   # Find node at specific location
   existing_node = nodes.find_node(10, 8, 0)

   if existing_node:
       print(f"Found node {existing_node.node_ID}")
   else:
       print("Node not found")

Iterating Through Nodes
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Iterate through all nodes
   for node_id, node in nodes.nodes.items():
       print(f"Node {node_id}: ({node.coordinates.x}, {node.coordinates.y}, {node.coordinates.z})")

   # Get coordinate arrays
   x_coords = nodes.x
   y_coords = nodes.y
   z_coords = nodes.z

Plane Constraints
-----------------

When a plane constraint is specified, all nodes automatically receive appropriate boundary conditions:

.. code-block:: python

   # XY plane model
   nodes_xy = Model(plane='xy').nodes

   # All nodes get automatic restraints: [0, 0, 1, 1, 1, 0]
   # Free in X and Y, restrained in Z (out-of-plane)

Available plane constraints:

* ``'xy'``: Free in-plane motion in X-Y, restrained out-of-plane in Z
* ``'yz'``: Free in-plane motion in Y-Z, restrained out-of-plane in X
* ``'zx'``: Free in-plane motion in Z-X, restrained out-of-plane in Y

Node Numbering
--------------

Nodes are automatically assigned sequential IDs starting from 1:

.. code-block:: python

   model = Model()

   N1 = model.nodes.add_node(0, 0, 0)    # node_ID = 1
   N2 = model.nodes.add_node(10, 0, 0)   # node_ID = 2
   N3 = model.nodes.add_node(0, 10, 0)   # node_ID = 3

   print(f"Total nodes: {model.nodes.count}")  # 3

Mesh Nodes
----------

Internal mesh nodes are created automatically during member discretization:

.. code-block:: python

   # Add a member (automatically creates mesh nodes)
   M1 = model.members.add_member(N1, N2, mesh=10)  # 10 mesh divisions

   # Mesh nodes are marked with mesh_node=True
   mesh_count = sum(1 for node in model.nodes.nodes.values() if node.mesh_node)
   print(f"Mesh nodes created: {mesh_count}")

Properties Access
-----------------

Access collection properties as a dictionary:

.. code-block:: python

   props = nodes.properties()
   print(f"Total nodes: {props['count']}")
   print(f"Plane constraint: {props['plane']}")

Coordinate Precision
--------------------

Node coordinates use floating-point comparison with tolerance:

.. code-block:: python

   # Tolerance for duplicate detection
   tolerance = 1e-6  # 0.000001 feet

   # These are considered the same location
   N1 = nodes.add_node(1.0000005, 2.0, 3.0)
   N2 = nodes.add_node(1.0000007, 2.0, 3.0)  # Within tolerance

   print(N1 is N2)  # True

Units
-----

* **Coordinates**: feet (ft)
* **Tolerance**: feet (same as coordinates)

Performance Considerations
--------------------------

* Node lookup uses coordinate-based hashing for efficiency
* Duplicate prevention prevents unnecessary node creation
* Mesh nodes are automatically managed during member discretization

See Also
--------

* :class:`OpenSTRAN.Node.Node`: Individual node class
* :class:`OpenSTRAN.Model.Model`: Main model class
* :class:`OpenSTRAN.Coordinates.Coordinate`: Coordinate representation