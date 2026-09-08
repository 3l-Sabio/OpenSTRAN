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

# Add a -10 kip point load 35% along the member.
M1.add_point_load(-10, 'Y', 35)

# Add a -1 kip/ft distributed load over the middle half of the span.
M1.add_distributed_load(-1, -1, 'Y', 25, 75)

# solve the model.
model.solve()

# print the nodal reactions to the terminal.
model.reactions()

# perform post processing steps on the model
model.max_deflection()

# print the maximum deflection to the terminal.
print(f"max deflection (Uy): {model.Uy_max}")
