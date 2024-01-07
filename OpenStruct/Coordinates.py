from numpy import array

class Coordinate():
	"""
	3D Space Coordinate
	
	REQUIRED PARAMETERS:
	x: x coordinate in feet
	y: y coordinate in feet
	z: z coordinate in feet

	USAGE:
	import .Coordinate
	coordinate = Coordinate(x,y,z)
	"""
	def __init__(self, x, y, z):
		# store the x, y, and z coordinates as floating point values
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)

		# store the x, y , and z coordinates as a tuple
		self.coordinates = (self.x, self.y, self.z)

		# store the x, y, and z coordinates as a mathematical point vector
		self.vector = array([x,y,z])