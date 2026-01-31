from OpenSTRAN.Model import Model
import time

# instantiate an empty model
simpleBeam = Model()

# create a node located at the origin
N1 = simpleBeam.nodes.add_node(0, 0, 0)  # (X [ft], Y [ft], Z[ft])

# create a node 10 feet away from the origin along the global X axis.
N2 = simpleBeam.nodes.add_node(10, 0, 0)  # (X [ft], Y [ft], Z[ft])

# restrain the nodes from translation.
N1.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

# define a member between nodes N1 and N2.
M1 = simpleBeam.members.addMember(N1, N2, mesh=50)  # (i node, j node)

# add a load of -1 kips in the global Y direction along M1's span.
M1.add_distributed_load(-1, -1, 'Y', 0, 100)

# print(simpleBeam.nodes.properties())

start = time.time()
# solve the model.
simpleBeam.solve()
stop = time.time()

print(f"time to run: {stop-start:2f} seconds")

# print the nodal reactions to the terminal.
# simpleBeam.reactions()
