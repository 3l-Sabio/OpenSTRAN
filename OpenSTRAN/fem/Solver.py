import numpy as np
import math

class Solver():
	"""
	docstring for Solver
	"""
	def __init__(self):
		self.nDoF = 0
		self.pinDoF = []
		self.restrainedDoF = []
		self.Kp = None
		#self.restrainedIndex = []
		self.forceVector = None
		self.UG = None
		self.FG = None

	def solve(self, nodes, members):
		# reinstantiate empty arrays for second order analylsis
		self.restrainedDoF = []

		# determine the total degrees of freedom for the model
		self.nDoF = nodes.count*6

		# determine the rotational restrained degrees of freedom
		for mbr in members.members.values():

			for submbr in mbr.submembers.values():

				if submbr.i_release == False and submbr.j_release == False:
					continue

				elif submbr.i_release == True and submbr.j_release == False:
					self.pinDoF.append(submbr.node_i.nodeID*6-1)
					self.pinDoF.append(submbr.node_i.nodeID*6)

				elif submbr.i_release == False and submbr.j_release == True:
					self.pinDoF.append(submbr.node_j.nodeID*6-1)
					self.pinDoF.append(submbr.node_j.nodeID*6)

				elif submbr.i_release == True and submbr.j_release == True:
					self.pinDoF.append(submbr.node_i.nodeID*6-2)
					self.pinDoF.append(submbr.node_i.nodeID*6-1)
					self.pinDoF.append(submbr.node_i.nodeID*6)
					self.pinDoF.append(submbr.node_j.nodeID*6-2)
					self.pinDoF.append(submbr.node_j.nodeID*6-1)
					self.pinDoF.append(submbr.node_j.nodeID*6)

		# remove duplicates from the rotational restrained degrees of 
		# freedom. Duplicates may exist because a user could potentially
		# define an i and j release on each side of a single node
		self.pinDoF = list(dict.fromkeys(self.pinDoF))

		# instantiate the Primary Stiffness Matrix
		self.Kp = np.zeros([self.nDoF, self.nDoF])

		# instantiate a list of the restrained degrees of freedom
		for i, node in enumerate(nodes.nodes.items()):
			if node[1].restraint == [0,0,0,0,0,0]:
				continue
			else:
				for n, DoF in enumerate(node[1].restraint):
					if DoF == 1:
						self.restrainedDoF.append(i*6 + n)

		# check pins to see if attached members contribute to stiffness
		for DoF in [x-1 for x in self.pinDoF]:
			if(np.sum(self.Kp[DoF,:]) < 1*10**-6):
				self.restrainedDoF.append(DoF)

		# remove duplicates from restrained degrees of freedom
		self.restrainedDoF = list(dict.fromkeys(self.restrainedDoF))

		# sort the restrained degrees of freedom in ascending order
		self.restrainedDoF.sort()

		# instantiate the force vector
		self.forceVector = np.zeros((self.nDoF,1))
		for i, node in enumerate(nodes.nodes.items()):
			self.forceVector[i*6][0] = node[1].Fx
			self.forceVector[i*6 + 1][0] = node[1].Fy
			self.forceVector[i*6 + 2][0] = node[1].Fz
			self.forceVector[i*6 + 3][0] = node[1].Mx
			self.forceVector[i*6 + 4][0] = node[1].My
			self.forceVector[i*6 + 5][0] = node[1].Mz

		# construct the 'Primary Stiffness Matrix' for the structure
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				nodeID_i = submbr.node_i.nodeID
				nodeID_j = submbr.node_j.nodeID
				i_release = submbr.i_release
				j_release = submbr.j_release
				KG = submbr.KG
				self.AddMemberToKp(nodeID_i, nodeID_j, i_release, j_release, KG)


		# 'Impose' the influence of supports to produce the
		# 'Structure Stiffness Matrix'
		self.Ks = np.delete(self.Kp, self.restrainedDoF, 0)
		self.Ks = np.delete(self.Ks, self.restrainedDoF, 1)
		self.Ks = np.matrix(self.Ks)

		# solve for unknown displacements
		reducedForceVector = np.delete(self.forceVector, self.restrainedDoF, 0)

		U = np.linalg.solve(self.Ks, reducedForceVector)
		self.UG = np.zeros([self.nDoF,1])
		index = 0
		for i in range(self.nDoF):
			if i in self.restrainedDoF:
				continue
			else:
				self.UG[i] = U[index]
				index += 1

		# back substitute displacements to calculate reaction forces
		self.FG = np.matmul(self.Kp, self.UG)

		# use nodal displacements to determine member forces
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				if submbr.i_release == False and submbr.j_release == False:				
					ia = submbr.node_i.nodeID*6-6
					ib = submbr.node_i.nodeID*6-1
					ja = submbr.node_j.nodeID*6-6
					jb = submbr.node_j.nodeID*6-1

					mbrDisplacements = np.array([
						self.UG[ia,0],
						self.UG[ia+1,0],
						self.UG[ia+2,0],
						self.UG[ia+3,0],
						self.UG[ia+4,0],
						self.UG[ib,0],
						self.UG[ja,0],
						self.UG[ja+1,0],
						self.UG[ja+2,0],
						self.UG[ja+3,0],
						self.UG[ja+4,0],
						self.UG[jb,0]
					]).T

					submbr.results['displacements'] = np.matmul(submbr.TM,mbrDisplacements)
					forces = np.matmul(submbr.Kl,submbr.results['displacements'])

					submbr.results['axial'] = [forces[0],forces[6]]
					submbr.results['shear'] = [forces[1],forces[7]]
					submbr.results['transverse shear'] = [forces[2],forces[8]]
					submbr.results['torsional moments'] = [forces[3],forces[9]]
					submbr.results['minor axis moments'] = [forces[4],forces[10]]
					submbr.results['major axis moments']= [forces[5],forces[11]]
			
				elif submbr.i_release == True and submbr.j_release == False:
					ia = submbr.node_i.nodeID*6-6
					ib = submbr.node_i.nodeID*6-3
					ja = submbr.node_j.nodeID*6-6
					jb = submbr.node_j.nodeID*6-1

					mbrDisplacements = np.array([
						self.UG[ia,0],
						self.UG[ia+1,0],
						self.UG[ia+2,0],
						self.UG[ib,0],
						self.UG[ja,0],
						self.UG[ja+1,0],
						self.UG[ja+2,0],
						self.UG[ja+3,0],
						self.UG[ja+4,0],
						self.UG[jb,0]
					]).T

					submbr.results['displacements'] = np.matmul(submbr.TM,mbrDisplacements)				
					forces = np.matmul(submbr.Kl,submbr.results['displacements'])

					submbr.results['axial'] = [forces[0],forces[4]]
					submbr.results['transverse shear'] = [forces[1],forces[5]]
					submbr.results['shear'] = [forces[2],forces[6]]
					submbr.results['torsional moments'] = [forces[3],forces[7]]
					submbr.results['major axis moments'] = [0,forces[8]]
					submbr.results['minor axis moments']= [0,forces[9]]

				elif submbr.i_release == False and submbr.j_release == True:				
					ia = submbr.node_i.nodeID*6-6
					ib = submbr.node_i.nodeID*6-1
					ja = submbr.node_j.nodeID*6-6
					jb = submbr.node_j.nodeID*6-3

					mbrDisplacements = np.array([
						self.UG[ia,0],
						self.UG[ia+1,0],
						self.UG[ia+2,0],
						self.UG[ia+3,0],
						self.UG[ia+4,0],
						self.UG[ib,0],
						self.UG[ja,0],
						self.UG[ja+1,0],
						self.UG[ja+2,0],
						self.UG[jb,0]
					]).T

					submbr.results['displacements'] = np.matmul(submbr.TM,mbrDisplacements)			
					forces = np.matmul(submbr.Kl,submbr.results['displacements'])

					submbr.results['axial'] = [forces[0],forces[6]]
					submbr.results['transverse shear'] = [forces[1],forces[7]]
					submbr.results['shear'] = [forces[2],forces[8]]
					submbr.results['torsional moments'] = [forces[3],forces[9]]
					submbr.results['major axis moments'] = [forces[4],0]
					submbr.results['minor axis moments']= [forces[5],0]

				elif submbr.i_release == True and submbr.j_release == True:
					ia = submbr.node_i.nodeID*6-6
					ib = submbr.node_i.nodeID*6-3
					ja = submbr.node_j.nodeID*6-6
					jb = submbr.node_j.nodeID*6-3

					mbrDisplacements = np.array([
						self.UG[ia,0],
						self.UG[ia+1,0],
						self.UG[ib,0],
						self.UG[ja,0],
						self.UG[ja+1,0],
						self.UG[jb,0]
					]).T

					submbr.results['displacements'] = np.matmul(submbr.TM,mbrDisplacements)
					forces = np.matmul(submbr.Kl,submbr.results['displacements'])
					
					submbr.results['axial'] = [forces[0],forces[3]]
					submbr.results['transverse shear'] = [forces[1],forces[4]]
					submbr.results['shear'] = [forces[2],forces[5]]
					submbr.results['torsional moments'] = [0,0]
					submbr.results['major axis moments'] = [0,0]
					submbr.results['minor axis moments']= [0,0]

		# remove the influence of equivalent nodal actions
		for mbr in members.members.values():
			for n, submbr in mbr.submembers.items():

				# determine DOFs associated with the submember nodes
				ia = submbr.node_i.nodeID*6-6
				ib = submbr.node_i.nodeID*6-1
				ja = submbr.node_j.nodeID*6-6
				jb = submbr.node_j.nodeID*6-1

				# remove influence of equivalent nodal actions from
				# the Global Force Vector

				self.FG[ia] = self.FG[ia] - submbr.node_i.eFx
				self.FG[ia+1] = self.FG[ia+1] - submbr.node_i.eFy
				self.FG[ia+2] = self.FG[ia+2] - submbr.node_i.eFz
				self.FG[ia+3] = self.FG[ia+3] - submbr.node_i.eMx
				self.FG[ia+4] = self.FG[ia+4] - submbr.node_i.eMy
				self.FG[ib] = self.FG[ib] - submbr.node_i.eMz

				self.FG[ja] = self.FG[ja] - submbr.node_j.eFx
				self.FG[ja+1] = self.FG[ja+1] - submbr.node_j.eFy
				self.FG[ja+2] = self.FG[ja+2] - submbr.node_j.eFz
				self.FG[ja+3] = self.FG[ja+3] - submbr.node_j.eMx
				self.FG[ja+4] = self.FG[ja+4] - submbr.node_j.eMy
				self.FG[jb] = self.FG[jb] - submbr.node_j.eMz

				# remove influence of equivalent nodal actions from 
				# the member forces

				submbr.results['axial'][0] = submbr.results['axial'][0] - submbr.ENAs['axial'][0]
				submbr.results['axial'][1] = submbr.results['axial'][1] - submbr.ENAs['axial'][1]

				submbr.results['transverse shear'][0] = submbr.results['transverse shear'][0] - submbr.ENAs['transverse shear'][0]
				submbr.results['transverse shear'][1] = submbr.results['transverse shear'][1] - submbr.ENAs['transverse shear'][1]

				submbr.results['shear'][0] = submbr.results['shear'][0] - submbr.ENAs['shear'][0]
				submbr.results['shear'][1] = submbr.results['shear'][1] - submbr.ENAs['shear'][1]

				submbr.results['torsional moments'][0] = submbr.results['torsional moments'][0] - submbr.ENAs['torsional moments'][0]
				submbr.results['torsional moments'][1] = submbr.results['torsional moments'][1] - submbr.ENAs['torsional moments'][1]

				submbr.results['major axis moments'][0] = submbr.results['major axis moments'][0] - submbr.ENAs['major axis moments'][0]
				submbr.results['major axis moments'][1] = submbr.results['major axis moments'][1] - submbr.ENAs['major axis moments'][1]

				submbr.results['minor axis moments'][0] = submbr.results['minor axis moments'][0] - submbr.ENAs['minor axis moments'][0]
				submbr.results['minor axis moments'][1] = submbr.results['minor axis moments'][1] - submbr.ENAs['minor axis moments'][1]

				# store nodal reactions
				if submbr.node_i.meshNode == False:
					submbr.node_i.Rx = self.FG[ia][0]
					submbr.node_i.Ry = self.FG[ia+1][0]
					submbr.node_i.Rz = self.FG[ia+2][0]
					submbr.node_i.Rmx = self.FG[ia+3][0]
					submbr.node_i.Rmy = self.FG[ia+4][0]
					submbr.node_i.Rmz = self.FG[ib][0]
				elif submbr.node_j.meshNode == False:
					submbr.node_j.Rx = self.FG[ja][0]
					submbr.node_j.Ry = self.FG[ja+1][0]
					submbr.node_j.Rz = self.FG[ja+2][0]
					submbr.node_j.Rmx = self.FG[ja+3][0]
					submbr.node_j.Rmy = self.FG[ja+4][0]
					submbr.node_j.Rmz = self.FG[jb][0]

	def AddMemberToKp(self, nodeID_i, nodeID_j, i_release, j_release, KG):

		if i_release == False and j_release == False:
			K11 = KG[0:6,0:6]
			K12 = KG[0:6,6:12]
			K21 = KG[6:12,0:6]
			K22 = KG[6:12,6:12]

			ia = 6*nodeID_i-6
			ib = 6*nodeID_i-1
			ja = 6*nodeID_j-6
			jb = 6*nodeID_j-1
		
		elif i_release == True and j_release == False:
			K11 = KG[0:4,0:4]
			K12 = KG[0:4,4:10]
			K21 = KG[4:10,0:4]
			K22 = KG[4:10,4:10]

			ia = 6*nodeID_i-6
			ib = 6*nodeID_i-3
			ja = 6*nodeID_j-6
			jb = 6*nodeID_j-1

		elif i_release == False and j_release == True:
			K11 = KG[0:6,0:6]
			K12 = KG[0:6,6:10]
			K21 = KG[6:10,0:6]
			K22 = KG[6:10,6:10]

			ia = 6*nodeID_i-6
			ib = 6*nodeID_i-1
			ja = 6*nodeID_j-6
			jb = 6*nodeID_j-3

		elif i_release == True and j_release == True:
			K11 = KG[0:3,0:3]
			K12 = KG[0:3,3:6]
			K21 = KG[3:6,0:3]
			K22 = KG[3:6,3:6]

			ia = 6*nodeID_i-6
			ib = 6*nodeID_i-4
			ja = 6*nodeID_j-6
			jb = 6*nodeID_j-4

		self.Kp[ia:ib+1,ia:ib+1] = self.Kp[ia:ib+1,ia:ib+1] + K11
		self.Kp[ia:ib+1,ja:jb+1] = self.Kp[ia:ib+1,ja:jb+1] + K12
		self.Kp[ja:jb+1,ia:ib+1] = self.Kp[ja:jb+1,ia:ib+1] + K21
		self.Kp[ja:jb+1,ja:jb+1] = self.Kp[ja:jb+1,ja:jb+1] + K22
