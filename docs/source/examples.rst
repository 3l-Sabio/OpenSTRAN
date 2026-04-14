Examples
========

This section provides examples of how to use OpenSTRAN for structural analysis. The following Quick Start Example will get you up started.

Quick Start Example
-------------------

The following example demonstrates how to create a simple beam model, apply loads, and solve for deflections and reactions.

.. code-block:: python

   from OpenSTRAN.Model import Model
   from OpenSTRAN.Database.Shape import Shape

   # instantiate an empty model
   model = Model()

   # create a node located at the origin
   N1 = model.nodes.add_node(0, 0, 0)  # (X [ft], Y [ft], Z[ft])

   # create a node 10 feet away from the origin along the global X axis.
   N2 = model.nodes.add_node(10, 0, 0)  # (X [ft], Y [ft], Z[ft])

   # restrain the nodes from translation.
   N1.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
   N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

   # define steel constants
   E = 29000  # ksi - modulus of elasticity for steel
   G = 12000  # ksi - shear modulus for steel

   # import W12x14 member properties from the database
   s = Shape("W12X14")

   M1 = model.members.add_member(N1, N2, shape=s)

   # add a load of -1 kips in the global Y direction along M1's span.
   M1.add_distributed_load(-1, -1, 'Y', 0, 100)

   # solve the model.
   model.solve()

   # print the nodal reactions to the terminal.
   model.reactions()

   # perform post processing steps on the model
   model.max_deflection()

   # print the maximum deflection to the terminal.
   print(model.Uy_max)

This example creates a 10-foot long beam with pinned supports at both ends, applies a uniform load of 1 kip/ft, and calculates the maximum deflection.

Hung Beam Example
-----------------

The following example demonstrates how to create a hung beam by releasing moments where the hung beam is attached to the cantilevered ends of two simply supported beams.

.. code-block:: python

   from OpenSTRAN.Model import Model
   from OpenSTRAN.Database.Shape import Shape

   # instantiate an empty model
   model = Model()

   # create 6 nodes located at the listed locations along the global X axis.
   x_coords = [0,12,15,25,28,40]
   nodes = []

   for x in x_coords:
      nodes.append(model.nodes.add_node(x,0,0))
   
   # restrain nodes 1,2, 5 and 6 nodes from translation.
   for i, node in enumerate(nodes):
      if i in [0,1,4,5]:
         node.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

   # define steel constants
   E = 29000  # ksi - modulus of elasticity for steel
   G = 12000  # ksi - shear modulus for steel

   # import W12x14 member properties from the database
   cantilever = Shape("W12X14")
   hung_beam = Shape("W10X12")

   hinge = [0,0,0,0,1,1] # [Ux, Uy, Uz, φx, φy, φz] -> weak and strong axis end moments released

   members = []
   for i, node in enumerate(nodes):
      if i in [0,1,3,4]:
         members.append(model.members.add_member(node, nodes[i+1], shape=cantilever))
      elif i in [2]:
         members.append(model.members.add_member(node, nodes[i+2], i_release=hinge, j_release=hinge, shape=hung_beam))

   # add a load of -1 kips in the global Y direction along all member spans
   for mbr in members:
      mbr.add_distributed_load(-1, -1, 'Y', 0, 100)

   # solve the model.
   model.solve()

   # print the nodal reactions to the terminal.
   model.reactions()

   # perform post processing steps on the model
   model.max_deflection()

   # print the maximum deflection to the terminal.
   print(model.Uy_max)

This example creates a 10-foot long beam with pinned supports at both ends, applies a uniform load of 1 kip/ft, and calculates the maximum deflection.
