from .mainScreen import mainScreen

class Model():
	def __init__(self):
		self.nodes = Nodes()
		self.members = Members()
		self.loads = Loads()
		self.plotter = mainScreen(self)

	def plot(self):
		self.plotter.root.mainloop()

class Nodes():
	def __init__(self):
		self.nodes = {}
		self.count = 0

	def addNode(self, x, y, z, label):
		self.count += 1
		self.nodes[self.count] = Node(x, y, z, label)
		return(self.nodes[self.count])

	def removeNode(self, node):
		for i, n in self.nodes.items():
			if n == node:
				break
			else:
				continue

		self.nodes.pop(i)

	def returnNode(self, label):
		for node in self.nodes.values():
			if node.label == label:
				return(node)
			else:
				continue

class Node():
	def __init__(self, x, y, z, label):
		self.x = x
		self.y = y
		self.z = z
		self.label = label
		self.restraint = [0,0,0,0,0,0]

	def update(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

class Members():
	def __init__(self):
		self.members = {}
		self.count = 0

	def addMember(
		self,
		node_i,
		node_j,
		shape = None,
		i_release = None,
		j_release = None,
		E = None,
		Ixx = None,
		Iyy = None,
		A = None,
		G = None,
		J = None,
		mesh = None,
		bracing = None,
		label = None
		):

		self.count += 1
		member = Member(
			node_i = node_i,
			node_j = node_j,
			shape = shape,
			i_release = i_release,
			j_release = j_release,
			E = E,
			Ixx = Ixx,
			Iyy = Iyy,
			A = A,
			G = G,
			J = J,
			mesh = mesh,
			bracing = bracing,
			label = str('M{i}'.format(i=self.count))
		)
		self.members[self.count] = member
		return(member)

	def removeMember(self, member):
		for n, mbr in self.members.items():
			if member == mbr:
				break
		self.members.pop(n)

	def getLabel(self, member):
		for n, mbr in self.members.items():
			if member == mbr:
				return(n)

class Member():
	def __init__(
		self,
		node_i,
		node_j,
		shape = None,
		i_release = None,
		j_release = None,
		E = None,
		Ixx = None,
		Iyy = None,
		A = None,
		G = None,
		J = None,
		mesh = None,
		bracing = None,
		label = None
		):

		self.node_i = node_i
		self.node_j = node_j
		self.i_release = False if i_release == None else i_release
		self.j_release = False if j_release == None else j_release
		self.shape = 'W12X14' if shape == None else shape
		self.E = 29000 if E == None else E	
		self.Izz = 88.6 if Ixx == None else Ixx
		self.Iyy = 2.36 if Iyy == None else Iyy
		self.A = 4.16 if A == None else A
		self.G = 12000 if G == None else G
		self.J = 0.0704 if J == None else J
		self.mesh = 50 if mesh == None else mesh
		self.bracing = 'continuous' if bracing == None else bracing
		self.label = None if label == None else label

class Loads():
	def __init__(self):
		self.pointLoads = {}
		self.pointLoadCount = 0
		self.distLoads = {}
		self.distLoadCount = 0

	def addPointLoad(
			self,
			mbr,
			direction,
			D=0,
			L=0,
			S=0,
			Lr=0,
			R=0,
			W=0,
			E=0,
			location=0
		):
		self.pointLoadCount += 1
		pointLoad = PointLoad(mbr, direction, D, L, S, Lr, R, W, E, location)
		self.pointLoads[self.pointLoadCount] = pointLoad

	def removePointLoad(self, load):
		for i, pointLoad in self.pointLoads.items():
			if pointLoad == load:
				break
			else:
				continue

		self.pointLoads.pop(i)

	def addDistLoad(self, mbr, direction, D, L, S, Lr, R, W, E, location):
		self.distLoadCount += 1
		distLoad = DistLoad(mbr, direction, D, L, S, Lr, R, W, E, location)
		self.distLoads[self.distLoadCount] = distLoad

	def removeDistLoad(self, load):
		for i, distLoad in self.distLoads.items():
			if distLoad == load:
				break
			else:
				continue

		self.distLoads.pop(i)

class DistLoad():
	def __init__(self, mbr, direction, D, L, S, Lr, R, W, E, location):
		self.member = mbr
		self.direction = direction
		self.D = (float(D[:D.index(';')]),float(D[D.index(';')+1:]))
		self.L = (float(L[:L.index(';')]),float(L[L.index(';')+1:]))
		self.S = (float(S[:S.index(';')]),float(S[S.index(';')+1:]))
		self.Lr = (float(Lr[:Lr.index(';')]),float(Lr[Lr.index(';')+1:]))
		self.R = (float(R[:R.index(';')]),float(R[R.index(';')+1:]))
		self.W = (float(W[:W.index(';')]),float(W[W.index(';')+1:]))
		self.E = (float(E[:E.index(';')]),float(E[E.index(';')+1:]))
		self.location = (float(location[:location.index(';')]),float(location[location.index(';')+1:]))
		
	def calculateASD(self):
		self.ASD_S = ASD(self.D[0], self.L[0], self.S[0], self.Lr[0], self.R[0], self.W[0], self.E[0])
		self.ASD_E = ASD(self.D[1], self.L[1], self.S[1], self.Lr[1], self.R[1], self.W[1], self.E[1])

		self.loadCombinations_S = {
			'Dead Load Only (D)':self.D[0],
			'Live Load Only (L)':self.L[0],
			'Roof Live Load Only (Lr)':self.Lr[0],
			'Snow Load Only (S)':self.S[0],
			'Rain Load Only (R)':self.R[0],
			'Wind Load Only (W)':self.W[0],
			'Earthquake Load Only (E)':self.E[0],
			'ASD 2-4a D':self.ASD_S.loadCase['1'],
			'ASD 2-4b D + L':self.ASD_S.loadCase['2'],
			'ASD 2-4c D + (Lr or S or R)':self.ASD_S.loadCase['3'],
			'ASD 2-4d D + 0.75L + 0.75(Lr or S or R)':self.ASD_S.loadCase['4'],
			'ASD 2-4e D + 0.6W or 0.7E':self.ASD_S.loadCase['5'],
			'ASD 2-4f D + 0.75L + 0.75(0.6W) + 0.75(Lr or S or R)':self.ASD_S.loadCase['6a'],
			'ASD 2-4g D + 0.75L + 0.75(0.6E) + 0.75S':self.ASD_S.loadCase['6b'],
			'ASD 2-4h 0.6D + 0.6W':self.ASD_S.loadCase['8'],
			'ASD 2-4i 0.6D + 0.7E':self.ASD_S.loadCase['9']
		}

		self.loadCombinations_E = {
			'Dead Load Only (D)':self.D[1],
			'Live Load Only (L)':self.L[1],
			'Roof Live Load Only (Lr)':self.Lr[1],
			'Snow Load Only (S)':self.S[1],
			'Rain Load Only (R)':self.R[1],
			'Wind Load Only (W)':self.W[1],
			'Earthquake Load Only (E)':self.E[1],
			'ASD 2-4a D':self.ASD_E.loadCase['1'],
			'ASD 2-4b D + L':self.ASD_E.loadCase['2'],
			'ASD 2-4c D + (Lr or S or R)':self.ASD_E.loadCase['3'],
			'ASD 2-4d D + 0.75L + 0.75(Lr or S or R)':self.ASD_E.loadCase['4'],
			'ASD 2-4e D + 0.6W or 0.7E':self.ASD_E.loadCase['5'],
			'ASD 2-4f D + 0.75L + 0.75(0.6W) + 0.75(Lr or S or R)':self.ASD_E.loadCase['6a'],
			'ASD 2-4g D + 0.75L + 0.75(0.6E) + 0.75S':self.ASD_E.loadCase['6b'],
			'ASD 2-4h 0.6D + 0.6W':self.ASD_E.loadCase['8'],
			'ASD 2-4i 0.6D + 0.7E':self.ASD_E.loadCase['9']
		}

class PointLoad():
	def __init__(self, mbr, direction, D, L, S, Lr, R, W, E, location):
		self.member = mbr
		self.direction = direction
		self.D = float(D)
		self.L = float(L)
		self.S = float(S)
		self.Lr = float(Lr)
		self.R = float(R)
		self.W = float(W)
		self.E = float(E)
		self.location = location
		self.LRFD = {}

	def calculateASD(self):
		self.ASD = ASD(self.D, self.L, self.S, self.Lr, self.R, self.W, self.E)

		self.loadCombinations = {
			'Dead Load Only (D)':self.D,
			'Live Load Only (L)':self.L,
			'Roof Live Load Only (Lr)':self.Lr,
			'Snow Load Only (S)':self.S,
			'Rain Load Only (R)':self.R,
			'Wind Load Only (W)':self.W,
			'Earthquake Load Only (E)':self.E,
			'ASD 2-4a D':self.ASD.loadCase['1'],
			'ASD 2-4b D + L':self.ASD.loadCase['2'],
			'ASD 2-4c D + (Lr or S or R)':self.ASD.loadCase['3'],
			'ASD 2-4d D + 0.75L + 0.75(Lr or S or R)':self.ASD.loadCase['4'],
			'ASD 2-4e D + 0.6W or 0.7E':self.ASD.loadCase['5'],
			'ASD 2-4f D + 0.75L + 0.75(0.6W) + 0.75(Lr or S or R)':self.ASD.loadCase['6a'],
			'ASD 2-4g D + 0.75L + 0.75(0.6E) + 0.75S':self.ASD.loadCase['6b'],
			'ASD 2-4h 0.6D + 0.6W':self.ASD.loadCase['8'],
			'ASD 2-4i 0.6D + 0.7E':self.ASD.loadCase['9']
		}

class ASD():
	def __init__(self, D, L, S, Lr, R, W, E):
		self.loadCase = {}

		self.loadCase['1'] = self.ASD_2_4a(D)
		self.loadCase['2'] = self.ASD_2_4b(D, L)
		self.loadCase['3'] = self.ASD_2_4c(D, Lr, S, R)
		self.loadCase['4'] = self.ASD_2_4d(D, L, Lr, S, R)
		self.loadCase['5'] = self.ASD_2_4e(D, W, E)
		self.loadCase['6a'] = self.ASD_2_4f(D, L, Lr, S, R, W)
		self.loadCase['6b'] = self.ASD_2_4g(D, L, S, E)
		self.loadCase['8'] = self.ASD_2_4h(D, W)
		self.loadCase['9'] = self.ASD_2_4i(D, E)
		self.loadCase['Envelope'] = self.Envelope()

	def ASD_2_4a(self, D):
		return(D)

	def ASD_2_4b(self, D, L):
		return(D + L)

	def ASD_2_4c(self, D, Lr, S, R):
		loads = []
		loads.append(D + Lr)
		loads.append(D + S)
		loads.append(D + R)

		return(max(loads, key=lambda x: abs(x)))

	def ASD_2_4d(self, D, L, Lr, S, R):
		loads = []
		loads.append(D + 0.75*L + 0.75*Lr)
		loads.append(D + 0.75*L + 0.75*S)
		loads.append(D + 0.75*L + 0.75*R)

		return(max(loads, key=lambda x: abs(x)))

	def ASD_2_4e(self, D, W, E):
		loads = []
		loads.append(D + 0.6*W)
		loads.append(D + 0.7*E)

		return(max(loads, key=lambda x: abs(x)))

	def ASD_2_4f(self, D, L, Lr, S, R, W):
		loads = []
		loads.append(D + 0.75*L + 0.75*0.6*W + 0.75*Lr)
		loads.append(D + 0.75*L + 0.75*0.6*W + 0.75*S)
		loads.append(D + 0.75*L + 0.75*0.6*W + 0.75*R)

		return(max(loads, key=lambda x: abs(x)))

	def ASD_2_4g(self, D, L, S, E):
		return(D + 0.75*L + 0.75*0.6*E + 0.75*S)

	def ASD_2_4h(self, D, W):
		return(0.6*D + 0.6*W)

	def ASD_2_4i(self, D, E):
		return(0.6*D + 0.7*E)

	def Envelope(self):
		loads = []
		for case, load in self.loadCase.items():
			if case == 'Envelope':
				continue
			else:
				loads.append(load)

		return(max(loads,key=lambda x: abs(x)))
