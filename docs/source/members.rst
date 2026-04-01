Members Class
=============

The :class:`Members` class is a collection container that manages all member (element) objects in the structural model. It provides methods for adding and organizing structural members.

Overview
--------

The Members class serves as the central repository for all member objects in a model. Key responsibilities include:

* Creating and storing member objects
* Managing member numbering and counting
* Providing access to cross-section databases
* Handling member discretization and meshing
* Supporting various boundary conditions and material properties

Attributes
----------

* **nodes**: Reference to the global :class:`Nodes` collection
* **count**: Total number of members added
* **members**: Dictionary mapping member IDs to :class:`Member` objects

Basic Usage
-----------

Creating a Members Collection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Members collection is automatically created when instantiating a :class:`Model`:

.. code-block:: python

   from OpenSTRAN.Model import Model

   model = Model()
   members = model.members  # Members collection

Adding Members
^^^^^^^^^^^^^^

.. code-block:: python

   # Create nodes first
   N1 = model.nodes.add_node(0, 0, 0)
   N2 = model.nodes.add_node(10, 0, 0)
   N3 = model.nodes.add_node(10, 8, 0)
   N4 = model.nodes.add_node(0, 8, 0)

   # Add members between nodes
   M1 = members.add_member(N1, N2)  # Base member
   M2 = members.add_member(N2, N3)  # Right column
   M3 = members.add_member(N3, N4)  # Top beam
   M4 = members.add_member(N4, N1)  # Left column

Using Cross-Section Database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OpenSTRAN.Database.Shape import Shape

   # Use standard steel sections
   w_section = Shape("W12X14")    # Wide flange
   tube_section = Shape("TUB2X2X0.25")  # Tube

   # Add members with shapes
   M1 = members.add_member(N1, N2, shape=w_section)
   M2 = members.add_member(N2, N3, shape=tube_section)

Custom Material Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Define custom properties
   steel_props = {
       'E': 29000,     # Young's modulus (ksi)
       'A': 8.0,       # Area (in²)
       'Ixx': 80.0,    # Strong axis moment of inertia (in⁴)
       'Iyy': 20.0,    # Weak axis moment of inertia (in⁴)
       'G': 12000,     # Shear modulus (ksi)
       'J': 3.0        # Torsional constant (in⁴)
   }

   M1 = members.add_member(N1, N2, **steel_props)

Boundary Conditions
-------------------

Members can have different connection types at each end:

.. code-block:: python

   # Fixed-fixed (default)
   M1 = members.add_member(N1, N2)

   # Pinned-fixed
   M2 = members.add_member(N1, N2, i_release=True)

   # Fixed-pinned
   M3 = members.add_member(N1, N2, j_release=True)

   # Pinned-pinned
   M4 = members.add_member(N1, N2, i_release=True, j_release=True)

Member Discretization
---------------------

Control analysis accuracy through mesh density:

.. code-block:: python

   # Coarse mesh (fast, less accurate)
   M1 = members.add_member(N1, N2, mesh=10)

   # Medium mesh (balanced)
   M2 = members.add_member(N1, N2, mesh=50)  # default

   # Fine mesh (slow, more accurate)
   M3 = members.add_member(N1, N2, mesh=100)

Lateral Bracing
---------------

Specify bracing conditions for buckling analysis:

.. code-block:: python

   # Continuous bracing (most conservative)
   M1 = members.add_member(N1, N2, bracing="continuous")

   # Discrete bracing patterns
   M2 = members.add_member(N1, N2, bracing="quarter")    # At quarter points
   M3 = members.add_member(N1, N2, bracing="third")      # At third points
   M4 = members.add_member(N1, N2, bracing="midspan")    # At midspan

   # Custom bracing locations (0-1 scale)
   M5 = members.add_member(N1, N2, bracing=[0.2, 0.4, 0.6, 0.8])

Iterating Through Members
-------------------------

.. code-block:: python

   # Access all members
   for member_id, member in members.members.items():
       print(f"Member {member_id}: {member.length:.1f} inches")

   # Get member count
   print(f"Total members: {members.count}")

Member Properties
-----------------

Access comprehensive member information:

.. code-block:: python

   # Get collection properties
   props = members.properties()
   print(f"Total members: {props['count']}")

   # Individual member properties
   member_props = M1.properties()
   print(f"Length: {member_props['length']:.1f} inches")
   print(f"Area: {member_props['A']:.2f} in²")
   print(f"E: {member_props['E']:.0f} ksi")

Default Properties
------------------

When no shape is specified, default steel properties are used:

.. code-block:: python

   # Default values
   defaults = {
       'E': 29000.0,   # ksi
       'Ixx': 88.6,    # in⁴
       'Iyy': 2.36,    # in⁴
       'A': 4.16,      # in²
       'G': 12000.0,   # ksi
       'J': 0.0704     # in⁴
   }

   M1 = members.add_member(N1, N2)  # Uses defaults

Shape Database Integration
--------------------------

The Members class integrates with the cross-section database:

.. code-block:: python

   from OpenSTRAN.Database.Shape import Shape

   # Available shapes
   shapes = ["W8X10", "W10X12", "W12X14", "W14X16", "TUB1X1X0.125", "TUB2X2X0.25"]

   for shape_name in shapes:
       try:
           shape = Shape(shape_name)
           M = members.add_member(N1, N2, shape=shape)
           print(f"Added {shape_name}: A={shape.A:.2f} in²")
       except:
           print(f"Shape {shape_name} not found")

Performance Considerations
--------------------------

* Higher mesh values improve accuracy but increase computation time
* Continuous bracing provides conservative buckling results
* Shape database lookup is cached for efficiency

Units
-----

* **Length**: feet (ft) for node coordinates, inches (in) for member properties
* **Force/Stress**: kips/ksi
* **Area**: in²
* **Moments of Inertia**: in⁴

See Also
--------

* :class:`OpenSTRAN.Member.Member`: Individual member class
* :class:`OpenSTRAN.Database.Shape.Shape`: Cross-section properties
* :class:`OpenSTRAN.Nodes.Nodes`: Node collection
* :class:`OpenSTRAN.Model.Model`: Main model class