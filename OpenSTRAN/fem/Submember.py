import numpy as np
import math

class SubMember():
	"""
	3D Space Frame SubMember Object Between Mesh Nodes
	<PARAMETERS>
	node_i: 3D Space Frame Node Object (See Node Class)
	node_j: 3D Space Frame Node Object (See Node Class)
	i_release: False = unpinned, True = pinned
	j_release: False = unpinned, True = pinned
	E: Young's Modulus [ksi]
	I: Moment of Inertia [in^4]
	A: Cross-Sectional Area [in^2]
	G: Shear Modulus [ksi]
	J: Polar Moment of Inertia [in^4]
	"""
	def __init__(
		self,
		node_i,
		node_j,
		i_release,
		j_release,
		E,
		Ixx,
		Iyy,
		A,
		G,
		J,
	):
		self.node_i = node_i
		self.node_j = node_j
		self.i_release = i_release
		self.j_release = j_release
		self.E = E
		self.Ixx = Ixx
		self.Iyy = Iyy
		self.A = A
		self.G = G
		self.J = J
		self.ENAs = {
			'axial':[0,0],
			'shear':[0,0],
			'transverse shear':[0,0],
			'torsional moments':[0,0],
			'minor axis moments':[0,0],
			'major axis moments':[0,0]
		}
		self.results = {
			'displacements':[],
			'axial':[],
			'shear':[],
			'transverse shear':[],
			'torsional moments':[],
			'minor axis moments':[],
			'major axis moments':[]
		}

		# calculate the member length based on the node coordinates
		self.length = self.calculateMbrLength(node_i, node_j)
		
		# determine the transformation matrix for the member from the
		# member local coordinates to a global reference frame
		self.rotationMatrix = self.buildRotationMatrix(
			node_i,
			node_j,
			i_release,
			j_release
		)

		self.TM = self.rotationMatrix.T
		
		# calculate the member local stiffness matrix
		self.Kl = self.calculateKl(
			E,
			Ixx,
			Iyy,
			A,
			G,
			J,
			self.length
		)

		# calculate the member global stiffness matrix
		self.KG = self.TM.T.dot(self.Kl).dot(self.TM)

	def calculateMbrLength(self, node_i, node_j):
		# calculate the x, y and z vector components of the member
		dx = node_j.coordinates.x - node_i.coordinates.x
		dy = node_j.coordinates.y - node_i.coordinates.y
		dz = node_j.coordinates.z - node_i.coordinates.z
		# calculate and return the member length
		return(math.sqrt(dx**2 + dy**2 + dz**2))

	def buildRotationMatrix(self, node_i, node_j, i_release, j_release):
		# assign nodal coordinates to a local variable for readability
		ix = node_i.coordinates.x
		iy = node_i.coordinates.y
		iz = node_i.coordinates.z
		jx = node_j.coordinates.x
		jy = node_j.coordinates.y
		jz = node_j.coordinates.z

		# calculate the x, y and z vector components of the member
		dx = jx - ix
		dy = jy - iy
		dz = jz - iz
		
		# Check if the member is oriented vertically and, if so, offset 
		# the member nodes by one unit in the negative global x
		# direction to define the local x-y plane.
		if (abs(dx)<0.001 and abs(dz)<0.001):
			i_offset = np.array([ix-1, iy, iz])
			j_offset = np.array([jx-1, jy, jz])
		
		# Otherwise, the member is not oriented vertically and instead,
		# the member nodes must be offset by one unit in the positive 
		# global y direction to define local x-y plane.
		else:
			i_offset = np.array([ix, iy+1, iz])
			j_offset = np.array([jx, jy+1, jz])

		# determine the local x-vector and unit x-vector of the member 
		# in the global reference frame
		local_x_vector = node_j.coordinates.vector - node_i.coordinates.vector
		local_x_unit = local_x_vector/self.length

		# determine the local y-vector and unit y-vector of the member
		# in the global reference frame. This calculation requires the
		# definition of a reference point that lies in the local x-y
		# plane in order to utilize the Gram-Schmidt process vector.
		node_k = i_offset + 0.5*(j_offset-i_offset)
		vector_in_plane = node_k-node_i.coordinates.vector
		#local y-vector in global RF (Gram-Schmidt)
		local_y_vector = vector_in_plane - np.dot(vector_in_plane,local_x_unit)*local_x_unit
		#Length of local y-vector
		magY = math.sqrt(local_y_vector[0]**2 + local_y_vector[1]**2 + local_y_vector[2]**2)
		#Local unit vector defining the local y-axis
		local_y_unit = local_y_vector/magY

		#Local z-vector in global RF using matrix cross product
		#Local unit vector defining the local z-axis
		local_z_unit = np.cross(local_x_unit, local_y_unit) 
		# combine reference frame into a standard rotation matrix for 
		# the element x,y,z => columns 1,2,3
		rotationMatrix = np.array([local_x_unit, local_y_unit, local_z_unit,]).T

		# populate the rotation matrix with the proper values

		if i_release == False and j_release == False:
			TM = np.zeros((12,12))
			TM[0:3,0:3] = rotationMatrix
			TM[3:6,3:6] = rotationMatrix
			TM[6:9,6:9] = rotationMatrix
			TM[9:12,9:12] = rotationMatrix
		elif i_release == True and j_release == False:
			TM = np.zeros((10,10))
			TM[0:3,0:3] = rotationMatrix
			TM[3,3] = rotationMatrix[0,0]
			TM[4:7,4:7] = rotationMatrix
			TM[7:10,7:10] = rotationMatrix
		elif i_release == False and j_release == True:
			TM = np.zeros((10,10))
			TM[0:3,0:3] = rotationMatrix
			TM[3:6,3:6] = rotationMatrix
			TM[6:9,6:9] = rotationMatrix
			TM[9,9] = rotationMatrix[0,0]
		elif i_release == True and j_release == True:
			TM = np.zeros((6,6))
			TM[0:3,0:3] = rotationMatrix
			TM[3:6,3:6] = rotationMatrix

		return(TM)

	def calculateKl(self, E, Izz, Iyy, A, G, J, L):
		L = float(L*12)
		if self.i_release == False and self.j_release == False:
			# beam element (fixed at i and j nodes)
			return(np.array(
				[
					[
						E*A/L,
						0,
						0,
						0,
						0,
						0,
						-E*A/L,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						12*E*Izz/L**3,
						0,
						0,
						0,
						6*E*Izz/L**2,
						0,
						-12*E*Izz/L**3,
						0,
						0,
						0,
						6*E*Izz/L**2
					],
					[
						0,
						0,
						12*E*Iyy/L**3,
						0,
						-6*E*Iyy/L**2,
						0,
						0,
						0,
						-12*E*Iyy/L**3,
						0,
						-6*E*Iyy/L**2,
						0
					],
					[
						0,
						0,
						0,
						G*J/L,
						0,
						0,
						0,
						0,
						0,
						-G*J/L,
						0,
						0
					],
					[
						0,
						0,
						-6*E*Iyy/L**2,
						0,
						4*E*Iyy/L,
						0,
						0,
						0,
						6*E*Iyy/L**2,
						0,
						2*E*Iyy/L,
						0
					],
					[
						0,
						6*E*Izz/L**2,
						0,
						0,
						0,
						4*E*Izz/L,
						0,
						-6*E*Izz/L**2,
						0,
						0,
						0,
						2*E*Izz/L
					],
					[
						-E*A/L,
						0,
						0,
						0,
						0,
						0,
						E*A/L,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						-12*E*Izz/L**3,
						0,
						0,
						0,
						-6*E*Izz/L**2,
						0,
						12*E*Izz/L**3,
						0,
						0,
						0,
						-6*E*Izz/L**2
					],
					[
						0,
						0,
						-12*E*Iyy/L**3,
						0,
						6*E*Iyy/L**2,
						0,
						0,
						0,
						12*E*Iyy/L**3,
						0,
						6*E*Iyy/L**2,
						0
					],
					[
						0,
						0,
						0,
						-G*J/L,
						0,
						0,
						0,
						0,
						0,
						G*J/L,
						0,
						0
					],
					[
						0,
						0,
						-6*E*Iyy/L**2,
						0,
						2*E*Iyy/L,
						0,
						0,
						0,
						6*E*Iyy/L**2,
						0,
						4*E*Iyy/L,
						0
					],
					[
						0,
						6*E*Izz/L**2,
						0,
						0,
						0,
						2*E*Izz/L,
						0,
						-6*E*Izz/L**2,
						0,
						0,
						0,
						4*E*Izz/L
					]
				]
			))
		elif self.i_release == True and self.j_release == False:
			# beam element pinned at node i and fixed at node j
			return(np.array(
				[
					[
						E*A/L,
						0,
						0,
						0,
						-E*A/L,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						3*E*Izz/L**3,
						0,
						0,
						0,
						-3*E*Izz/L**3,
						0,
						0,
						0,
						3*E*Izz/L**2
					],
					[
						0,
						0,
						3*E*Iyy/L**3,
						0,
						0,
						0,
						-3*E*Iyy/L**3,
						0,
						-3*E*Iyy/L**2,
						0
					],
					[
						0,
						0,
						0,
						G*J/L,
						0,
						0,
						0,
						-G*J/L,
						0,
						0
					],
					[
						-E*A/L,
						0,
						0,
						0,
						E*A/L,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						-3*E*Izz/L**3,
						0,
						0,
						0,
						3*E*Izz/L**3,
						0,
						0,
						0,
						-3*E*Izz/L**2
					],
					[
						0,
						0,
						-3*E*Iyy/L**3,
						0,
						0,
						0,
						3*E*Iyy/L**3,
						0,
						3*E*Iyy/L**2,
						0
					],
					[
						0,
						0,
						0,
						-G*J/L,
						0,
						0,
						0,
						G*J/L,
						0,
						0
					],
					[
						0,
						0,
						-3*E*Iyy/L**2,
						0,
						0,
						0,
						3*E*Iyy/L**2,
						0,
						3*E*Iyy/L,
						0
					],
					[
						0,
						3*E*Izz/L**2,
						0,
						0,
						0,
						-3*E*Izz/L**2,
						0,
						0,
						0,
						3*E*Izz/L
					]
				]
			))
		elif self.i_release == False and self.j_release == True:
			# beam element fixed at node i and pinned at node j
			return(np.array(
				[
					[
						E*A/L,
						0,
						0,
						0,
						0,
						0,
						-E*A/L,
						0,
						0,
						0
					],
					[
						0,
						3*E*Izz/L**3,
						0,
						0,
						0,
						3*E*Izz/L**2,
						0,
						-3*E*Izz/L**3,
						0,
						0
					],
					[
						0,
						0,
						3*E*Iyy/L**3,
						0,
						-3*E*Iyy/L**2,
						0,
						0,
						0,
						-3*E*Iyy/L**3,
						0
					],
					[
						0,
						0,
						0,
						G*J/L,
						0,
						0,
						0,
						0,
						0,
						-G*J/L
					],
					[
						0,
						0,
						-3*E*Iyy/L**2,
						0,
						3*E*Iyy/L,
						0,
						0,
						0,
						3*E*Iyy/L**2,
						0
					],
					[
						0,
						3*E*Izz/L**2,
						0,
						0,
						0,
						3*E*Izz/L,
						0,
						-3*E*Izz/L**2,
						0,
						0
					],
					[
						-E*A/L,
						0,
						0,
						0,
						0,
						0,
						E*A/L,
						0,
						0,
						0
					],
					[
						0,
						-3*E*Izz/L**3,
						0,
						0,
						0,
						-3*E*Izz/L**2,
						0,
						3*E*Izz/L**3,
						0,
						0
					],
					[
						0,
						0,
						-3*E*Iyy/L**3,
						0,
						3*E*Iyy/L**2,
						0,
						0,
						0,
						3*E*Iyy/L**3,
						0
					],
					[
						0,
						0,
						0,
						-G*J/L,
						0,
						0,
						0,
						0,
						0,
						G*J/L
					]
				]
			))
		elif self.i_release == True and self.j_release == True:
			# bar element (pinned at i and j nodes)
			# returns stiffness matrix in global coordinates

			return(np.array(
				[
					[
						E*A/L,
						0,
						0,
						-E*A/L,
						0,
						0
					],
					[
						0,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						0,
						0,
						0,
						0,
						0
					],
					[
						-E*A/L,
						0,
						0,
						E*A/L,
						0,
						0
					],
					[
						0,
						0,
						0,
						0,
						0,
						0
					],
					[
						0,
						0,
						0,
						0,
						0,
						0
					],
				]
			))

	def calculateKG(self):
		# define section properties as local variables for readability
		J = self.J
		A = self.A
		L = float(self.length*12)

		# define first order results as local varaibles for readability
		Fx1 = self.results['axial'][0]
		Fx2 = self.results['axial'][1]
		Fy1 = self.results['shear'][0]
		Fy2 = self.results['shear'][1]
		Fz1 = self.results['transverse shear'][0]
		Fz2 = self.results['transverse shear'][1]
		Mx1 = self.results['torsional moments'][0]
		Mx2 = self.results['torsional moments'][1]
		My1 = self.results['minor axis moments'][0]
		My2 = self.results['minor axis moments'][1]
		Mz1 = self.results['major axis moments'][0]
		Mz2 = self.results['major axis moments'][1]

		# beam element (fixed at i and j nodes)
		return(np.array(
			[
				[
					Fx2/L,
					0,
					0,
					0,
					0,
					0,
					-Fx2/L,
					0,
					0,
					0,
					0,
					0
				],
				[
					0,
					6*Fx2/(5*L),
					0,
					My1/L,
					Mx2/L,
					Fx2/10,
					0,
					-6*Fx2/(5*L),
					0,
					My2/L,
					-Mx2/L,
					Fx2/10
				],
				[
					0,
					0,
					6*Fx2/(5*L),
					Mz1/L,
					-Fx2/10,
					Mx2/L,
					0,
					0,
					-6*Fx2/(5*L),
					Mz2/L,
					-Fx2/10,
					-Mx2/L
				],
				[
					0,
					My1/L,
					Mz1/L,
					Fx2*J/(A*L),
					(-2*Mz1-Mz2)/6,
					(2*My1-My2)/6,
					0,
					-My1/L,
					-Mz1/L,
					-Fx2*J/(A*L),
					(-Mz1+Mz2)/6,
					(My1+My2)/6
				],
				[
					0,
					Mx2/L,
					-Fx2/10,
					(-2*Mz1-Mz2)/6,
					2*Fx2*L/15,
					0,
					0,
					-Mx2/L,
					Fx2/10,
					(-Mz1+Mz2)/6,
					-Fx2*L/30,
					Mx2/2
				],
				[
					0,
					Fx2/10,
					Mx2/L,
					(2*My1-My2)/6,
					0,
					2*Fx2*L/15,
					0,
					-Fx2/10,
					-Mx2/L,
					(My1+My2)/6,
					-Mx2/2,
					-Fx2*L/30
				],
				[
					-Fx2/L,
					0,
					0,
					0,
					0,
					0,
					Fx2/L,
					0,
					0,
					0,
					0,
					0
				],
				[
					0,
					-6*Fx2/(5*L),
					0,
					-My1/L,
					-Mx2/L,
					-Fx2/10,
					0,
					6*Fx2/(5*L),
					0,
					-My2/L,
					Mx2/L,
					-Fx2/10
				],
				[
					0,
					0,
					-6*Fx2/(5*L),
					-Mz1/L,
					Fx2/10,
					-Mx2/L,
					0,
					0,
					6*Fx2/(5*L),
					-Mz2/L,
					Fx2/10,
					Mx2/L
				],
				[
					0,
					My2/L,
					Mz2/L,
					-Fx2*J/(A*L),
					(-Mz1+Mz2)/6,
					(My1+My2)/6,
					0,
					-My2/L,
					-Mz2/L,
					Fx2*J/(A*L),
					(Mz1-2*Mz2)/6,
					(-My1-2*My2)/6
				],
				[
					0,
					-Mx2/L,
					-Fx2/10,
					(-Mz1+Mz2)/6,
					-Fx2*L/30,
					-Mx2/2,
					0,
					Mx2/L,
					Fx2/10,
					(Mz1-2*Mz2)/6,
					2*Fx2*L/15,
					0
				],
				[
					0,
					Fx2/10,
					-Mx2/L,
					(My1+My2)/6,
					Mx2/2,
					-Fx2*L/30,
					0,
					-Fx2/10,
					Mx2/L,
					(-My1-2*My2)/6,
					0,
					2*Fx2*L/15
				]
			]
		))