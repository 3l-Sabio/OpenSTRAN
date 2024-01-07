from OpenStruct.Model import Model

model = Model(plane='xy')

N1 = model.nodes.addNode(0,0,0)
N2 = model.nodes.addNode(10,0,0)
N3 = model.nodes.addNode(20,0,0)

N1.addRestraint([1,1,1,1,1,1])
N2.addRestraint([1,0,1,0,0,0])
N3.addRestraint([1,1,1,0,0,0])

M1 = model.members.addMember(N1, N2)
M2 = model.members.addMember(N2, N3)

M1.addTrapLoad(-1,-1,'Y',0,100)

model.solve()

model.plot()