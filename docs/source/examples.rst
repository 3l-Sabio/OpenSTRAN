Examples
========

This section provides examples of how to use OpenSTRAN for structural analysis. The following Quick Start Example will get you up started.

Quick Start Example
-------------------

The following example demonstrates how to create a simple beam model, apply loads, and solve for deflections and reactions.

.. code-block:: python

   from OpenSTRAN import Model
   from OpenSTRAN import Shape

   # instantiate an empty model
   model = Model()

   # create a node located at the origin
   N1 = model.nodes.add_node(0, 0, 0)  # (X [in], Y [in], Z [in])

   # create a node 120 inches (10 feet) away from the origin along the global X axis.
   N2 = model.nodes.add_node(120, 0, 0)  # (X [in], Y [in], Z [in])

   # restrain the nodes from translation, and N1 from twisting about the
   # beam's axis, which nothing else resists.
   N1.restraint = [1, 1, 1, 1, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
   N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

   # define steel constants
   E = 29000  # ksi - modulus of elasticity for steel
   G = 12000  # ksi - shear modulus for steel

   # import W12x14 member properties from the database
   s = Shape("W12X14")

   M1 = model.members.add_member(N1, N2, shape=s)

   # add a load of -1 kip per foot (-1/12 kip per inch) in the global Y
   # direction along M1's span.
   M1.add_distributed_load(-1/12, -1/12, 'Y', 0, 100)

   # solve the model.
   results = model.solve()

   # print the nodal reactions to the terminal.
   model.reactions()

   # print the maximum deflection (0.0876 in) and the moment at midspan
   # (-150 kip-in) to the terminal.
   print(results.Uy_max)
   print(results.member(M1).moment(50))

This example creates a 10-foot long beam with pinned supports at both ends, applies a uniform load of 1 kip/ft, and calculates the maximum deflection and the moment at midspan.

Hung Beam Example
-----------------

The following example demonstrates how to create a hung beam by releasing moments where the hung beam is attached to the cantilevered ends of two simply supported beams.

.. code-block:: python

   from OpenSTRAN import Model
   from OpenSTRAN import Shape

   # instantiate an empty model
   model = Model()

   # create 6 nodes located at the listed locations, in inches, along the
   # global X axis (0, 12, 15, 25, 28 and 40 feet).
   x_coords = [0,144,180,300,336,480]
   nodes = []

   for x in x_coords:
      nodes.append(model.nodes.add_node(x,0,0))
   
   # restrain nodes 1, 2, 5 and 6 from translation.
   for i, node in enumerate(nodes):
      if i in [0,1,4,5]:
         node.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

   # restrain node 1 from twisting about the beams' axis, which nothing else
   # resists.
   nodes[0].restraint = [1, 1, 1, 1, 0, 0]

   # define steel constants
   E = 29000  # ksi - modulus of elasticity for steel
   G = 12000  # ksi - shear modulus for steel

   # import W12x14 member properties from the database
   cantilever = Shape("W12X14")
   hung_beam = Shape("W10X12")

   hinge = [0,0,0,0,1,1] # [Ux, Uy, Uz, φx, φy, φz] -> weak and strong axis end moments released

   # connect consecutive nodes. The third member, from 15 to 25 feet, is the
   # hung beam, pinned to the cantilevered ends of the other two beams.
   members = []
   for i in range(len(nodes) - 1):
      if i == 2:
         members.append(model.members.add_member(nodes[i], nodes[i+1], i_release=hinge, j_release=hinge, shape=hung_beam))
      else:
         members.append(model.members.add_member(nodes[i], nodes[i+1], shape=cantilever))

   # add a load of -1 kip per foot (-1/12 kip per inch) in the global Y
   # direction along all member spans
   for mbr in members:
      mbr.add_distributed_load(-1/12, -1/12, 'Y', 0, 100)

   # solve the model.
   results = model.solve()

   # print the nodal reactions to the terminal.
   model.reactions()

   # print the maximum deflection to the terminal.
   print(results.Uy_max)

   # print the moment at midspan of the hung beam, which acts as a simply
   # supported 10-foot beam: -150 kip-in (12.5 kip-ft).
   print(results.member(members[2]).moment(50))

This example creates two 15-foot beams, each on two pinned supports 12 feet apart and cantilevering 3 feet towards the other, and a 10-foot hung beam pinned between their cantilevered ends. It applies a uniform load of 1 kip/ft to every member, and calculates the maximum deflection and the moment at midspan of the hung beam.
