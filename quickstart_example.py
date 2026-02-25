from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape

# instantiate an empty model
simpleBeam = Model()

# create a node located at the origin
N1 = simpleBeam.nodes.add_node(0, 0, 0)  # (X [ft], Y [ft], Z[ft])

# create a node 10 feet away from the origin along the global X axis.
N2 = simpleBeam.nodes.add_node(10, 0, 0)  # (X [ft], Y [ft], Z[ft])

# restrain the nodes from translation.
N1.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

# define steel constants
E = 29000  # ksi - modulus of elasticity for steel
G = 12000  # ksi - shear modulus for steel

# import W12x14 member properties from the database
s = Shape("W12X14")

# define a member between nodes N1 and N2.
M1 = simpleBeam.members.add_member(N1, N2, i_release=False, j_release=False,
                                   E=E, Ixx=s.Ix, Iyy=s.Iy, A=s.A, G=G, J=s.J, mesh=50, bracing="continuous")

# add a load of -1 kips in the global Y direction along M1's span.
M1.add_distributed_load(-1, -1, 'Y', 0, 100)

# solve the model.
simpleBeam.solve()

# print the nodal reactions to the terminal.
simpleBeam.reactions()
