from OpenSTRAN.Model import Model

# instantiate an empty model
simpleBeam = Model()

# create a node located at the origin
N1 = simpleBeam.nodes.addNode(0, 0, 0, 'N1')  # (X [ft], Y [ft], Z[ft], name)

# create a node 10 feet away from the origin along the global X axis.
N2 = simpleBeam.nodes.addNode(10, 0, 0, 'N2')  # (X [ft], Y [ft], Z[ft], name)

# restrain the nodes from translation.
N1.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

# define a member between nodes N1 and N2.
M1 = simpleBeam.members.addMember(N1, N2)  # (i node, j node)

# add a load of -1 kips in the global Y direction along M1's span.
M1.addTrapLoad(-1, -1, 'Y', 0, 100)

# solve the model.
simpleBeam.solve()

# print the nodal reactions to the terminal.
simpleBeam.reactions()
