import matplotlib.pyplot as plt
import matplotlib.colors
import numpy as np
#from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class Plotter():
	def __init__(self):
		self.label_offset = 0.01
		self.xMargin = 5
		self.yMargin = 5
		self.zMargin = 5
		self.elevation = 30
		self.rotation = 210
		self.scale = 1

	def ShowModel(self, nodes, members):
		fig = plt.figure()
		axes = fig.add_subplot(projection='3d')

		#Set offset distance for node label
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset
		
		#Provide space/margin around the structure
		x_margin = self.xMargin
		y_margin = self.yMargin
		z_margin = self.zMargin

		
		# plot the nodes
		for coordinates, node in nodes.nodes.items():
			if node.meshNode == True:
				continue
			else:
				x = coordinates.x
				y = coordinates.y
				z = coordinates.z

				axes.plot3D(x,z,y, 'bo', ms=6)
				label = str('N{i}'.format(i=node.nodeID))
				axes.text(x+dx, z+dz, y+dy, label, fontsize=16)

		# plot the members
		for n, mbr in members.members.items():
			# node i coordinates
			ix = mbr.node_i.coordinates.x
			iy = mbr.node_i.coordinates.y
			iz = mbr.node_i.coordinates.z
			# node j coordinates
			jx = mbr.node_j.coordinates.x
			jy = mbr.node_j.coordinates.y
			jz = mbr.node_j.coordinates.z

			axes.plot3D([ix,jx],[iz,jz],[iy,jy],'b')
			
		#Set axis limits
		maxX = max(nodes.x)
		maxY = max(nodes.y)
		maxZ = max(nodes.z)
		minX = min(nodes.x)
		minY = min(nodes.y)
		minZ = min(nodes.z)
		axes.set_xlim([minX-x_margin, maxX+x_margin])
		axes.set_ylim([minY-y_margin, maxY+y_margin])
		axes.set_zlim([minZ, maxZ+z_margin])

		axes.set_xlabel('X-coordinate (FT)')
		axes.set_ylabel('Y-coordinate (FT)')
		axes.set_zlabel('Z-coordinate (FT)')
		axes.set_title('Structure to Analyse')
		axes.grid()

		plt.show()

	def ShowDeformation(self, nodes, members, UG):
		fig = plt.figure()
		axes = fig.add_subplot(projection='3d')
		axes.set_axis_off() 

		#Provide space/margin around structure
		x_margin = self.xMargin #x-axis margin
		y_margin = self.yMargin #y-axis margin
		z_margin = self.zMargin #z-axis margin
		scaleFactor = self.scale
	
		# plot the members
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				# node i coordinates
				ix = submbr.node_i.coordinates.x
				iy = submbr.node_i.coordinates.y
				iz = submbr.node_i.coordinates.z
				# node j coordinates
				jx = submbr.node_j.coordinates.x
				jy = submbr.node_j.coordinates.y
				jz = submbr.node_j.coordinates.z
				# member DoFs
				ia = submbr.node_i.nodeID*6-6
				ib = submbr.node_i.nodeID*6-4
				ja = submbr.node_j.nodeID*6-6
				jb = submbr.node_j.nodeID*6-4
			
				axes.plot3D([ix, jx], [iz, jz], [iy, jy], 'grey', lw=0.75) #Member
				axes.plot3D([ix + UG[ia,0]*scaleFactor, jx + UG[ja,0]*scaleFactor], 
							[iz + UG[ib,0]*scaleFactor, jz + UG[jb,0]*scaleFactor], 
							[iy + UG[ia+1,0]*scaleFactor, jy + UG[ja+1,0]*scaleFactor], 
							'purple', lw=0.5) # Deflected member

		#Set axis limits
		maxX = max(nodes.x)
		maxY = max(nodes.y)
		maxZ = max(nodes.z)
		minX = min(nodes.x)
		minY = min(nodes.y)
		minZ = min(nodes.z)
		axes.set_xlim([minX-x_margin, maxX+x_margin])
		axes.set_ylim([minY-y_margin, maxY+y_margin])
		axes.set_zlim([minZ, maxZ+z_margin])

		axes.set_xlabel('X-coordinate (FT)')
		axes.set_zlabel('Y-coordinate (FT)')
		axes.set_ylabel('Z-coordinate (FT)')
		axes.set_title('Deflected Shape')
		axes.grid()

		plt.show()

	def ShowAxial(self, nodes, members):	
		fig = plt.figure()
		axes = fig.add_subplot(projection='3d')

		#Set offset distance for node label
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		#Provide space/margin around structure
		x_margin = self.xMargin #x-axis margin
		y_margin = self.yMargin #y-axis margin
		z_margin = self.zMargin #z-axis margin
		
		# Change colormap based on distribution of axial forces
		axial_forces = []
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				axial_forces.append(submbr.results['axial'][0])

		if(min(axial_forces)<0 and max(axial_forces)<0):
			#All member forces are compression
			norm = matplotlib.colors.DivergingNorm(vmin=min(axial_forces),
												  vcenter = min(axial_forces) + 0.5*(max(axial_forces) - min(axial_forces)),
												  vmax = max(axial_forces))

			cmap = plt.cm.Reds_r #Defining the color scale to use (note _r reverses the colormap)
			
		elif(min(axial_forces)>0 and max(axial_forces)>0):
			#All member forces are tension
			norm = matplotlib.colors.DivergingNorm(vmin=min(axial_forces),
												  vcenter = min(axial_forces) + 0.5*(max(axial_forces) - min(axial_forces)),
												  vmax = max(axial_forces))
			cmap = plt.cm.Blues_r
			
		else:
			norm = matplotlib.colors.DivergingNorm(vmin=min(axial_forces),
												  vcenter = 0,
												  vmax = max(axial_forces))
			cmap = plt.cm.seismic
			
		#Add color scale to figure
		sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
		fig.colorbar(sm)
		
		# plot the members
		for n, mbr in members.members.items():
			# member axial force
			mbrForceX = mbr.results['axial'][0]
			# node i coordinates
			ix = mbr.node_i.coordinates.x
			iy = mbr.node_i.coordinates.y
			iz = mbr.node_i.coordinates.z
			# node j coordinates
			jx = mbr.node_j.coordinates.x
			jy = mbr.node_j.coordinates.y
			jz = mbr.node_j.coordinates.z
					
			if(abs(mbrForceX)>0.001):
				axes.plot3D([ix,jx],[iz,jz],[iy,jy], color=cmap(norm(mbrForceX))) #Non-zero force member
			else:
				axes.plot3D([ix,jx],[iz,jz],[iy,jy], 'grey', linestyle='--')
				
			
			#Plot labels on nodes at each end of member
			#if(Labels=='Fx' and abs(mbrForceX[n])>0.001):
			#	Fx = round(mbrForceX[n]/1000,1)
			#	label = "Mbr " + str(n+1) + '(' + str(node_i)+'/'+str(node_j)+')' +"\n" + str(Fx) + "kN"
			#	xPos = ix + 0.5*(jx-ix)+label_offset
			#	yPos = iy + 0.5*(jy-iy)+label_offset
			#	zPos = iz + 0.5*(jz-iz)+label_offset
			#	axes.text(xPos, yPos, zPos, label,fontsize=font_size, bbox = dict(facecolor='grey', alpha=0.1))
						

		#Plot nodes
		for coordinates, node in nodes.nodes.items():
			x = coordinates.x
			y = coordinates.y
			z = coordinates.z

			axes.plot3D(x,z,y, 'go', ms=1)
			label = str('N{i}'.format(i=node.nodeID))
			axes.text(x+dx, z+dz, y+dy, label, fontsize=16)
			
	 
		#Plot reaction labels
		#if(Reactions=='Show'):
		#	for r in restraintNodes:
		#		r = int(r)
		#		Rx = round(FG[6*r-6].item()/1000,2)
		#		Ry = round(FG[6*r-5].item()/1000,2)
		#		Rz = round(FG[6*r-4].item()/1000,2)
		#		Mx = round(FG[6*r-3].item()/1000,2)
		#		My = round(FG[6*r-2].item()/1000,2)
		#		Mz = round(FG[6*r-1].item()/1000,2)
		#		ix = nodes[r-1,0] #x-coord of node i of this member
		#		iy = nodes[r-1,1] #y-coord of node i of this member
		#		iz = nodes[r-1,2] #z-coord of node i of this member
		#		xPos = ix + label_offset
		#		yPos = iy + label_offset
		#		zPos = iz + label_offset
		#		rLabel = "Node " + str(r)+'\n'+'Fx: '+str(Rx)+' kN'+'\n'+'Fy: '+str(Ry)+' kN'+'\n'+'Fz: '+str(Rz)+' kN'+'\n'+'Mx: '+str(Mx)+' kNm'+'\n'+'My: '+str(My)+' kNm'+'\n'+'Mz: '+str(Mz)+' kNm'
		#		axes.text(xPos, yPos, zPos, rLabel,fontsize=font_size, bbox = dict(facecolor='grey', alpha=0.1))
		
		#Set axis limits
		maxX = max(nodes.x)
		maxY = max(nodes.y)
		maxZ = max(nodes.z)
		minX = min(nodes.x)
		minY = min(nodes.y)
		minZ = min(nodes.z)
		axes.set_xlim([minX-x_margin, maxX+x_margin])
		axes.set_ylim([minY-y_margin, maxY+y_margin])
		axes.set_zlim([minZ, maxZ+z_margin])

		axes.set_xlabel('X-coordinate (FT)')
		axes.set_ylabel('Y-coordinate (FT)')
		axes.set_zlabel('Z-coordinate (FT)')
		axes.set_title('Tension/compression members')
		axes.grid()	  

		plt.show()

	def ShowShear(self, nodes, members):
		fig = plt.figure()
		axes = fig.add_subplot(projection='3d')
		axes.set_axis_off()
		scale = self.scale
		shearScale = scale*10**-2

		#Provide space/margin around structure
		x_margin = self.xMargin #x-axis margin
		y_margin = self.yMargin #y-axis margin
		z_margin = self.zMargin #z-axis margin
		scaleFactor = 1

		# plot the shear force diagram ('SFD')
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				# node i coordinates
				ix = submbr.node_i.coordinates.x
				iy = submbr.node_i.coordinates.y
				iz = submbr.node_i.coordinates.z
				# node j coordinates
				jx = submbr.node_j.coordinates.x
				jy = submbr.node_j.coordinates.y
				jz = submbr.node_j.coordinates.z
				# member DoFs
				ia = submbr.node_i.nodeID*6-6
				ib = submbr.node_i.nodeID*6-4
				ja = submbr.node_j.nodeID*6-6
				jb = submbr.node_j.nodeID*6-4
				# member shears
				si = submbr.results['shear'][0]*shearScale
				sj = submbr.results['shear'][1]*shearScale
				# plot the undeformed member
				axes.plot3D([ix, jx], [iz, jz], [iy, jy], 'grey', lw=0.75) #Member

				# correct the shape of the segment shear force diagram
				if(si<0 and sj>0):
					si = -abs(si)
					sj = -abs(sj)
				elif(si<0 and sj<0):
					si = -abs(si)
					sj = abs(sj)
				elif(si>0 and sj>0):
					si = abs(si)
					sj = -abs(sj)
				elif(si>0 and sj<0):
					si = abs(si)
					sj = abs(sj)
				elif(si>0 and sj==0): # probably need this to be something close to zero
					si = abs(si)
				elif(si<0 and sj==0): # probably need this to be something close to zero
					si = -abs(si)
				elif(si==0 and sj>0):
					sj = -abs(sj)
				elif(si==0 and sj<0):
					sj = abs(sj)

				# rotate SFD to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,si,0])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,sj,0])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment SFD
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# plot the shear force diagram
				axes.add_collection3d(Poly3DCollection([list(zip(xr,zr,yr))], alpha=0.2, facecolor='red', edgecolor='red'))
				Fi = round(submbr.results['shear'][0]/1000,1)
				Fj = round(submbr.results['shear'][1]/1000,1)

		#Set axis limits
		maxX = max(nodes.x)
		maxY = max(nodes.y)
		maxZ = max(nodes.z)
		minX = min(nodes.x)
		minY = min(nodes.y)
		minZ = min(nodes.z)
		axes.set_xlim([minX-x_margin, maxX+x_margin])
		axes.set_ylim([minY-y_margin, maxY+y_margin])
		axes.set_zlim([minZ, maxZ+z_margin])

		axes.set_xlabel('X-coordinate (FT)')
		axes.set_zlabel('Y-coordinate (FT)')
		axes.set_ylabel('Z-coordinate (FT)')
		axes.set_title('Major Shear Force Diagram')
		axes.grid()	  

		plt.show()

	def ShowMoment(self, nodes, members):
		fig = plt.figure()
		axes = fig.add_subplot(projection='3d')
		axes.set_axis_off()
		scale = self.scale

		momentScale = scale*10**-3.5

		#Provide space/margin around structure
		x_margin = self.xMargin #x-axis margin
		y_margin = self.yMargin #y-axis margin
		z_margin = self.zMargin #z-axis margin
		scaleFactor = 1

		# plot the shear force diagram ('SFD')
		for mbr in members.members.values():
			for submbr in mbr.submembers.values():
				# node i coordinates
				ix = submbr.node_i.coordinates.x
				iy = submbr.node_i.coordinates.y
				iz = submbr.node_i.coordinates.z
				# node j coordinates
				jx = submbr.node_j.coordinates.x
				jy = submbr.node_j.coordinates.y
				jz = submbr.node_j.coordinates.z
				# member DoFs
				ia = submbr.node_i.nodeID*6-6
				ib = submbr.node_i.nodeID*6-4
				ja = submbr.node_j.nodeID*6-6
				jb = submbr.node_j.nodeID*6-4
				# member shears
				mi = submbr.results['major axis moments'][0]*momentScale
				mj = submbr.results['major axis moments'][1]*momentScale
				# plot the undeformed member
				axes.plot3D([ix, jx], [iz, jz], [iy, jy], 'grey', lw=0.75) #Member

				# correct the shape of the segment shear force diagram
				if(mi<0 and mj>0):
					mi = -abs(mi)
					mj = -abs(mj)
				elif(mi<0 and mj<0):
					mi = -abs(mi)
					mj = abs(mj)
				elif(mi>0 and mj>0):
					mi = abs(mi)
					mj = -abs(mj)
				elif(mi>0 and mj<0):
					mi = abs(mi)
					mj = abs(mj)
				elif(mi>0 and mj==0): # probably need this to be something close to zero
					mi = abs(mi)
				elif(mi<0 and mj==0): # probably need this to be something close to zero
					mi = -abs(mi)

				# rotate SFD to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,mi,0])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,mj,0])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment SFD
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# plot the shear force diagram
				axes.add_collection3d(Poly3DCollection([list(zip(xr,zr,yr))], alpha=0.2, facecolor='red', edgecolor='red'))
				Mi = round(submbr.results['major axis moments'][0]/1000,1)
				Mj = round(submbr.results['major axis moments'][1]/1000,1)

		#Set axis limits
		maxX = max(nodes.x)
		maxY = max(nodes.y)
		maxZ = max(nodes.z)
		minX = min(nodes.x)
		minY = min(nodes.y)
		minZ = min(nodes.z)
		axes.set_xlim([minX-x_margin, maxX+x_margin])
		axes.set_ylim([minY-y_margin, maxY+y_margin])
		axes.set_zlim([minZ, maxZ+z_margin])

		axes.set_xlabel('X-coordinate (FT)')
		axes.set_zlabel('Y-coordinate (FT)')
		axes.set_ylabel('Z-coordinate (FT)')
		axes.set_title('Major Bending Moment Diagram')
		axes.grid()	  

		plt.show()