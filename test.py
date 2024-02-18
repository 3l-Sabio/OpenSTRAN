from OpenSTRAN.model import Model

simpleBeam = Model()

N1 = simpleBeam.nodes.addNode(0,0,0,'N1')
N2 = simpleBeam.nodes.addNode(10,0,0,'N2')

N1.restraint = [1,1,1,0,0,0]
N2.restraint = [1,1,1,0,0,0]

M1 = simpleBeam.members.addMember(N1, N2)

simpleBeam.loads.addPointLoad(M1, direction='Y', D=-10, location=50)

simpleBeam.plot()