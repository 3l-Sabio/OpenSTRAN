import numpy as np

from .Nodes import Nodes
from .Members import Members
from .Solver import Solver
from .Plotter import Plotter

class Model():
	"""
	3D Space Frame Model

	The model neglects deformations due to transverse shear stresses 
	and torsional warping. The model does not account for such 
	deformations under the premise that torsional effects are generally 
	negligible in typical civil engineering practice.

	OPTIONAL PARAMETERS:
	plane = 'xy' – defines a model constrained to the X-Y plane
	plane = 'yz' – defines a model constrained to the Y-Z plane
	plane = 'xz' – defines a model constrained to the X-Z plane
 
	no definition of a plane indicates the model is not restrained to a 
	two-dimensional plane.

	USAGE:

	import OpenStruct
	2Dframe = OpenStruct.Model(plane='xy')
	3Dframe = OpenStruct.Model()
	"""
	def __init__(self, plane=None):
		self.nodes = Nodes(plane)
		self.members = Members(self.nodes)
		self.solver = Solver()
		self.plotter = Plotter()

	def solve(self):
		self.solver.solve(self.nodes, self.members)
		self.maxReactions()
		self.maxMbrForces()

	def maxReactions(self):
		Rx = []
		Ry = []
		Rz = []
		Rmx = []
		Rmy = []
		Rmz = []

		for node in self.nodes.nodes.values():
			if node.meshNode == False:
				Rx.append(node.Rx)
				Ry.append(node.Ry)
				Rz.append(node.Rz)
				Rmx.append(node.Rmx)
				Rmy.append(node.Rmy)
				Rmz.append(node.Rmz)

		self.Rx_max = abs(max(Rx, key=lambda x: abs(x)))
		self.Ry_max = abs(max(Ry, key=lambda x: abs(x)))
		self.Rz_max = abs(max(Rz, key=lambda x: abs(x)))
		self.Rmx_max = abs(max(Rmx, key=lambda x: abs(x)))
		self.Rmy_max = abs(max(Rmy, key=lambda x: abs(x)))
		self.Rmz_max = abs(max(Rmz, key=lambda x: abs(x)))

	def maxMbrForces(self):
		axial = []
		torque = []
		Vy = []
		Vz = []
		Mzz = []
		Myy = []

		for mbr in self.members.members.values():
			for submbr in mbr.submembers.values():
				axial.append(submbr.results['axial'][0])
				axial.append(submbr.results['axial'][1]*-1)
				torque.append(submbr.results['torsional moments'][0])
				torque.append(submbr.results['torsional moments'][1]*-1)
				Vy.append(submbr.results['shear'][0])
				Vy.append(submbr.results['shear'][1]*-1)
				Vz.append(submbr.results['transverse shear'][0])
				Vz.append(submbr.results['transverse shear'][1]*-1)
				Mzz.append(submbr.results['major axis moments'][0])
				Mzz.append(submbr.results['major axis moments'][1]*-1)
				Myy.append(submbr.results['minor axis moments'][0])
				Myy.append(submbr.results['minor axis moments'][1]*-1)

		self.axial_max = abs(max(axial, key=lambda x: abs(x)))
		self.axial_maxima = self.localMaxima(axial)
		self.axial_minima = self.localMinima(axial)
		
		self.torque_max = abs(max(torque, key=lambda x: abs(x)))
		self.torque_maxima = self.localMaxima(torque)
		self.torque_minima = self.localMinima(torque) 

		self.Vy_max = abs(max(Vy, key=lambda x: abs(x)))
		self.Vy_maxima = self.localMaxima(Vy)
		self.Vy_minima = self.localMinima(Vy)

		self.Vz_max = abs(max(Vz, key=lambda x: abs(x)))
		self.Vz_maxima = self.localMaxima(Vz)
		self.Vz_minima = self.localMinima(Vz)

		self.Mzz_max = abs(max(Mzz, key=lambda x: abs(x)))
		self.Mzz_maxima = self.localMaxima(Mzz)
		self.Mzz_minima = self.localMinima(Mzz)

		self.Myy_max = abs(max(Myy, key=lambda x: abs(x)))
		self.Myy_maxima = self.localMaxima(Myy)
		self.Myy_minima = self.localMinima(Myy)

	def localMaxima(self, forces):
		maxima = [False for force in forces]
		length = len(forces)-1
		for i, force in enumerate(forces):
			if i == 0:
				if force > 0:
					maxima[i] = True
			if i % 2 == 0 or i == 1:
				continue
			elif i == length:
				if force > 0:
					maxima[i] = True
			else:
				if forces[i-2] > force:
					continue
				if np.isclose(forces[i-2],force) and np.isclose(forces[i+2],force):
					continue
				if np.isclose(forces[i-2],force) and forces[i+2] < force:
					maxima[i] = True
					continue
				if forces[i-2] < force and forces[i+2] < force:
					maxima[i] = True
					continue
				if forces[i-2] < force and np.isclose(forces[i+2],force):
					maxima[i] = True
					continue
		return(maxima)

	def localMinima(self, forces):
		minima = [False for force in forces]
		length = len(forces)-1
		for i, force in enumerate(forces):
			if i == 0:
				if force < 0:
					minima[i] = True
			if i % 2 == 0 or i == 1:
				continue
			elif i == length:
				if force < 0:
					minima[i] = True
			else:
				if forces[i-2] < force:
					continue
				if np.isclose(forces[i-2], force) and np.isclose(forces[i+2],force):
					continue
				if np.isclose(forces[i-2],force) and forces[i+2] > force:
					minima[i] = True
					continue
				if forces[i-2] > force and np.isclose(forces[i+2],force):
					minima[i] = True
					continue
				if forces[i-2] > force and forces[i+2] > force:
					minima[i] = True
					continue
		return(minima)

	def reactions(self):
		print('Nodal Reactions')
		for node in self.nodes.nodes.values():
			if node.meshNode == False:
				print('	Node {node}:'.format(node=node.nodeID))
				print('		Rx = {Rx} kips'.format(Rx=round(node.Rx,2)))
				print('		Ry = {Ry} kips'.format(Ry=round(node.Ry,2)))
				print('		Rz = {Rz} kips'.format(Rz=round(node.Rz,2)))
				print('		Mx = {Mx} kip-ft'.format(Mx=round(node.Rmx,2)))
				print('		My = {My} kip-ft'.format(My=round(node.Rmy,2)))
				print('		Mz = {Mz} kip-ft'.format(Mz=round(node.Rmz,2)))

	def show(self, deflection=False, axial=False, shear=False, moment=False):
		if deflection == False and axial == False and shear == False and moment == False:
			self.plotter.ShowModel(self.nodes, self.members)
		elif deflection == True:
			self.plotter.ShowDeformation(self.nodes, self.members, self.solver.UG)
		elif axial == True:
			self.plotter.ShowAxial(self.nodes, self.members)
		elif shear == True:
			self.plotter.ShowShear(self.nodes, self.members)
		elif moment == True:
			self.plotter.ShowMoment(self.nodes, self.members)

