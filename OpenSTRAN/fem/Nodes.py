from .Coordinates import Coordinate
from .Node import Node

class Nodes():
	"""
	Container for user defined node objects
	"""
	def __init__(self, plane=None):
		self.nodes = {}
		self.count = 0
		self.plane = plane
		self.x = []
		self.y = []
		self.z = []

	def addNode(self, x, y, z, meshNode=False):
		"""
		Method to add node objects to the model
		
		REQUIRED PARAMETES:
		x: x coordinate in feet
		y: y coordinate in feet
		z: z coordinate in feet

		USAGE:
		N1 = frame.nodes.addNode(0,0,0)
		N2 = frame.nodes.addNode(0,10,0)
		N3 = frame.nodes.addNode(10,10,0)
		N4 = frame.nodes.addNode(10,0,0)
		"""
		node = self.findNode(x,y,z)
		if node == None:
			self.count += 1
			self.x.append(x)
			self.y.append(y)
			self.z.append(z)
			coordinates = Coordinate(x, y, z)
			node = Node(
				coordinates = coordinates,
				nodeID = self.count,
				plane = self.plane,
				meshNode = meshNode
			)
			self.nodes[coordinates] = node
		return(node)

	def findNode(self, x, y, z):
		"""
		Method that iterates through the nodes in the model and returns
		a matching node object for the passed coordinates or a None type
		object if no matching node is found.

		REQUIRED PARAMETERS:
		x: x coordinate in feet
		y: y coordinate in feet
		z: z coordinate in feet
		"""
		
		# define a floating point error
		pointError = 1*10**-10

		# iterate through the model nodes
		for coordinates, node in self.nodes.items():
			x_e = coordinates.x
			y_e = coordinates.y
			z_e = coordinates.z
			if ((x_e - pointError) < x < (x_e + pointError) and (
				y_e - pointError) < y < (y_e + pointError) and (
				z_e - pointError) < z < (z_e + pointError)):
				return(node)
			else:
				continue
		return(None)