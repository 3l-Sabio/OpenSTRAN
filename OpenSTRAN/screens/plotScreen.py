import sys
import os

# import third party packages
import matplotlib
import matplotlib.style
import numpy as np

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

# Configure Matplotlib backend for use
matplotlib.use('TkAgg')

# enable line segment simplification to reduce rendering time
#https://matplotlib.org/stable/users/explain/performance.html
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0
matplotlib.style.use('fast')
#matplotlib.style.use('dark_background')

# matplotlib backend imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backend_tools import ToolBase

from matplotlib import markers
from matplotlib.path import Path

from matplotlib.figure import Figure
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D
from mpl_toolkits.mplot3d import art3d
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class customToolbar(NavigationToolbar2Tk):	
	def __init__(self, canvas_, axes_, parent_):
		self.canvas_ = canvas_
		self.axes_ = axes_
		self.showGrid = False

		# https://stackoverflow.com/questions/23172916/matplotlib-tkinter-customizing-toolbar-tooltips
		self.toolitems = (
			('ISO','Reset original view','ISO','isometric'),
			(None,None,None,None),
			('XY','Orient view to global XY axis','XY','orientXY'),
			(None,None,None,None),
			('-XY','Orient view to global -XY axis','-XY','orientNXY'),
			(None,None,None,None),
			('XZ','Orient view to global XZ axis','XZ','orientXZ'),
			(None,None,None,None),
			('-XZ','Orient view to global -XZ axis','-XZ','orientNXZ'),
			(None,None,None,None),
			('ZY','Orient view to global ZY axis','ZY','orientZY'),
			(None,None,None,None),
			('-ZY','Orient view to global -ZY axis','-ZY','orientNZY'),
			(None,None,None,None),
			('Grid','Display the grid','grid','displayGrid'),
			('Zoom','Zoom to rectangle','zoom_to_rect','zoom'),
			('Save','Save an image of the model','filesave','save_figure'),
			#('Subplots', 'Configure subplots', 'subplots', 'configure_subplots')
		)
		
		NavigationToolbar2Tk.__init__(self,canvas_,parent_)

	def _Button(self, text, image_file, toggle, command):
		if not toggle:
			b = tk.Button(
				master=self, text=text, command=command,
				relief="flat", overrelief="groove", borderwidth=1,
			)
		else:
			var = tk.IntVar(master=self)
			b = tk.Checkbutton(
				master=self, text=text, command=command, indicatoron=False,
				variable=var, offrelief="flat", overrelief="groove",
				borderwidth=1
			)
			b.var = var
		file = image_file[(image_file.rfind('\\'))+1:]
		if file in [
			'ISO.png',
			'XY.png',
			'-XY.png',
			'XZ.png',
			'-XZ.png',
			'ZY.png',
			'-ZY.png',
			'grid.png',
		]:
			image_file = os.path.join(
				os.path.dirname(__file__),
				'..',
				'projectFiles',
				'Icons',
				file
			)
		b._image_file = image_file
		if image_file is not None:
			# Explicit class because ToolbarTk calls _Button.
			NavigationToolbar2Tk._set_image_for_button(self, b)
		else:
			b.configure(font=self._label_font)
		b.pack(side=tk.LEFT)
		return b

	#https://matplotlib.org/stable/api/toolkits/mplot3d/view_angles.html
	def orientXY(self):
		self.axes_.view_init(0,-90,0)
		self.canvas_.draw()

	def orientNXY(self):
		self.axes_.view_init(0,90,0)
		self.canvas_.draw()

	def orientXZ(self):
		self.axes_.view_init(90,-90,0)
		self.canvas_.draw()

	def orientNXZ(self):
		self.axes_.view_init(-90,90,0)
		self.canvas_.draw()

	def orientZY(self):
		self.axes_.view_init(0,0,0)
		self.canvas_.draw()

	def orientNZY(self):
		self.axes_.view_init(0,180,0)
		self.canvas_.draw()

	def displayGrid(self):
		if self.showGrid:
			self.showGrid = False
			self.axes_.set_axis_off()
		else:
			self.showGrid = True
			self.axes_.set_axis_on()
			self.axes_.set_xlabel('X-Axis')
			self.axes_.set_zlabel('Y-Axis')
			self.axes_.set_ylabel('Z-Axis')

		self.canvas.draw()

	def isometric(self):
		self.axes_.view_init(azim=-60, elev=30)
		self.canvas_.draw()


class plotFrame(tk.Frame):
	def __init__(self, parent):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		# define plotting variables
		self.nodes = {}
		self.nodeLabels = {}
		self.restraints = {}

		self.members = {}
		self.memberLabels = {}
		self.memberiPins = {}
		self.memberjPins = {}

		self.pointLoads = {}
		self.pointLoadLabels = {}
		self.distLoads = {}
		self.startLoads = {}
		self.startLoadLabels = {}
		self.endLoads = {}
		self.endLoadLabels = {}

		self.xReactions = {}
		self.yReactions = {}
		self.zReactions = {}
		self.MxReactions = {}
		self.MyReactions = {}
		self.MzReactions = {}

		self.xReactionLabels = {}
		self.yReactionLabels = {}
		self.zReactionLabels = {}
		self.MxReactionLabels = {}
		self.MyReactionLabels = {}
		self.MzReactionLabels = {}

		self.deflection = {}
		self.Vy = {}
		self.Vz = {}
		self.Mzz = {}
		self.Myy = {}
		self.axial = {}
		self.torque = {}

		self.deflectionLabels = {}
		self.VyLabels = {}
		self.VzLabels = {}
		self.MzzLabels = {}
		self.MyyLabels = {}
		self.axialLabels = {}
		self.torqueLabels = {}

		# plotting scales
		self.reactionScale = 5

		# define plot components
		self.displayNodes = False
		self.displayNodeLabels = False
		self.displayMembers = False
		self.displayMemberLabels = False
		self.displayRestraints = False
		self.displayMemberPins = False
		self.displayPointLoads = False
		self.displayDistLoads = False
		self.displayReactions = False

		# define default graph view properties
		self.label_offset = 0.002
		self.forceScale = 4
		self.deflectionScale = 5

		# instantiate the 3D plot from the matplotlib library
		self.fig = Figure(frameon=False, constrained_layout=False, rasterized=True)
		self.axes = self.fig.add_subplot(projection='3d')
		self.axes.set_aspect(aspect='auto')
		self.axes.autoscale(enable=True, axis='both', tight=1)

		# turn off the 3d axis
		self.axes.set_axis_off()

		# define the plot limits 
		self.axes.set_xlim([-20,20])
		self.axes.set_ylim([-20,20])
		self.axes.set_zlim([-20,20])

		self.canvas = FigureCanvasTkAgg(self.fig, self)
		self.toolbar = customToolbar(self.canvas, self.axes, self)
		self.toolbar.update()
		self.canvas.draw()
		self.canvas.get_tk_widget().pack(
			side='top',
			fill='both',
			expand=True
			)
		self.toolbar.pack()

		# adjust the subplot parameters
		self.fig.subplots_adjust(left=0,bottom=0,right=1,top=1)

	def addNode(self, node):
		if self.displayNodes:
			self.nodes[node] = self.axes.plot3D(
				node.x,
				node.z,
				node.y,
				'go',
				ms = 3,
				rasterized = True
			)

			# update the plot
			self.canvas.draw()

	def removeNode(self, node):
		# remove the matplotlib object from the figure
		self.nodes[node][0].remove()
		self.nodes.pop(node)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def updateNode(self, node):
		if self.displayNodes:
			# update the x, y, and z coordinates of the node
			self.nodes[node][0].set_data_3d(([node.x],[node.z],[node.y]))
			
			# update the plot
			self.canvas.draw_idle()
			self.canvas.flush_events()

	def showNodes(self, model):
		if self.displayNodes:
			# Turn the nodes off if previously turned on
			self.displayNodes = False
			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# Remove the nodes from the display
				self.removeNode(node)
		else:
			# Turn the nodes on if previously turned off
			self.displayNodes = True
			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# Add the node to the display
				self.addNode(node)			

	def addNodeLabel(self, node):
		if self.displayNodeLabels:
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			self.nodeLabels[node] = self.axes.text(
				node.x+dx,
				node.z+dz,
				node.y+dy,
				node.label,
				fontsize = 10,
				color = 'green',
				rasterized = True
			)

			# update the plot
			self.canvas.draw()

	def removeNodeLabel(self, node):
		# remove the matplotlib object from the figure
		self.nodeLabels[node].remove()
		self.nodeLabels.pop(node)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def updateNodeLabel(self, node):
		if self.displayNodeLabels:
			# define offset distance for the node labels from the nodes
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			# update the x, y, and z coordinates of the node label
			self.nodeLabels[node]._x = node.x + dx
			self.nodeLabels[node]._y = node.z + dz
			self.nodeLabels[node]._z = node.y + dy

			# update the plot
			self.canvas.draw_idle()
			self.canvas.flush_events()

	def showNodeLabels(self, model):
		if self.displayNodeLabels:
			# Turn the node labels off if previously turned on			
			self.displayNodeLabels = False
			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# Remove the node label from the display
				self.removeNodeLabel(node)
		else:
			# Turn the node labels on if previously turned off
			self.displayNodeLabels = True
			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# Add the Node Label to the Display
				self.addNodeLabel(node)

	def addRestraint(self, node):
		if self.displayRestraints:
		
			def align_marker(marker, valign='top'):
				"""
				https://stackoverflow.com/questions/26686722/align-matplotlib-scatter-marker-left-and-or-right
				"""
				if isinstance(valign, str):
					valign = {'top': -1.,
						'middle': 0.,
						'center': 0.,
						'bottom': 1.,
						}[valign]

				# Define the base marker
				bm = markers.MarkerStyle(marker)

				# Get the marker path and apply the marker transform to get the
				# actual marker vertices (they should all be in a unit-square
				# centered at (0, 0))
				m_arr = bm.get_path().transformed(bm.get_transform()).vertices

				# Shift the marker vertices for the specified alignment.
				m_arr[:, 1] += valign / 2

				return Path(m_arr, bm.get_path().codes)

			# unrestrained node
			if node.restraint == [0,0,0,0,0,0]:
				return

			# node with pinned restraint
			elif node.restraint == [1,1,1,0,0,0]:
				self.restraints[node] = self.axes.plot3D(
					node.x,
					node.z,
					node.y,
					'r',
					marker = align_marker('^', valign = 'top'),
					alpha = 0.25,
					markersize = 20
				)

			# node with roller restraint
			elif node.restraint in [[0,1,1,0,0,0],[1,1,0,0,0,0],[1,0,1,0,0,0]]:
				self.restraints[node] = self.axes.plot3D(
					node.x,
					node.z,
					node.y,
					'r',
					marker = align_marker('o', valign = 'top'),
					alpha = 0.25,
					markersize = 20
				)

			# node with fixed restraint
			elif node.restraint == [1,1,1,1,1,1]:
				self.restraints[node] = self.axes.plot3D(
					node.x,
					node.z,
					node.y,
					'r',
					marker = align_marker('s', valign = 'top'),
					alpha = 0.25,
					markersize = 20
				)

			# node with custom restraint
			else:
				self.restraints[node] = self.axes.plot3D(
					node.x,
					node.z,
					node.y,
					'r',
					marker = align_marker('x', valign = 'top'),
					alpha = 0.25,
					markersize = 20
				)

			# update the plot
			self.canvas.draw()

	def updateRestraint(self, node):
		if self.showRestraints:
			# remove and replot nodal restraint if already plotted
			try:
				# identify the matplotlib object associated w/ the restraint
				restraint = self.restraints[node][0]

				# remove the matplotlib object from the figure

				restraint.remove()
				#self.axes.lines.remove(restraint)
				self.restraints.pop(node)

				# update the plot
				self.canvas.draw_idle()
				self.canvas.flush_events()

				# plot the nodal restraint
				self.addRestraint(node)

			# plot the nodal restraint if not already plotted
			except KeyError:
				self.addRestraint(node)

	def removeRestraint(self, node):
		# remove the matplotlib object from the figure
		self.restraints[node][0].remove()
		self.restraints.pop(node)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showRestraints(self, model):
		if self.displayRestraints:
			# Turn the nodal restraints off id previously turned on
			self.displayRestraints = False

			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# remove the restraint from the display
				try:
					self.removeRestraint(node)
				except KeyError:
					continue
		else:
			# Turn the node restraints on if previously turned off
			self.displayRestraints = True

			# Iterate through the user defined nodes
			for node in model.nodes.nodes.values():
				# Add the Nodal Restraints to the Display
				self.addRestraint(node)

	def addMember(self, mbr):
		if self.displayMembers:
			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z
			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z
			# add the members to the axes
			self.members[mbr] = self.axes.plot3D(
				[ix, jx],
				[iz, jz],
				[iy, jy],
				'grey',
				lw=0.75
			)
			# update the plot
			self.canvas.draw()

	def removeMember(self, mbr):
		# remove the matplotlib object from the figure
		self.members[mbr][0].remove()
		self.members.pop(mbr)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def updateMember(self, mbr):
		if self.displayMembers:
			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z
			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z
			# update the x, y, and z coordinates of the member
			self.members[mbr][0].set_data_3d(
				[ix, jx],
				[iz, jz],
				[iy, jy]
			)
			# update the plot
			self.canvas.draw()
		
	def showMembers(self, model):
		if self.displayMembers:
			self.displayMembers = False

			for mbr in model.members.members.values():
				try:
					self.removeMember(mbr)
				except KeyError:
					continue
		else:
			self.displayMembers = True

			for mbr in model.members.members.values():
				self.addMember(mbr)

	def addMemberLabel(self, mbr):
		if self.displayMemberLabels:
			# define offset distance of member labels from the members
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z

			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z

			# calculate the midpoint coordinates of the member
			x = (jx + ix) / 2 + dx
			y = (jy + iy) / 2 + dy
			z = (jz + iz) / 2 + dz

			# add the member label to the axes
			self.memberLabels[mbr] = self.axes.text(
				x,
				z,
				y,
				mbr.label,
				fontsize = 10,
				color = 'grey',
				rasterized = True
			)

			# update the plot
			self.canvas.draw()

	def removeMemberLabel(self, mbr):
		# remove the matplotlib object from the figure
		self.memberLabels[mbr].remove()
		self.memberLabels.pop(mbr)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def updateMemberLabel(self, mbr):
		if self.displayMemberLabels:
			# define offset distance of member labels from the members
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z

			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z

			# calculate the midpoint coordinates of the member
			x = (jx + ix) / 2 + dx
			y = (jy + iy) / 2 + dy
			z = (jz + iz) / 2 + dz

			# update the x, y, and z coordinates of the member label
			self.memberLabels[mbr]._x = x
			self.memberLabels[mbr]._y = z
			self.memberLabels[mbr]._z = y

			# update the plot
			self.canvas.draw_idle()
			self.canvas.flush_events()

	def showMemberLabels(self, model):
		if self.displayMemberLabels:
			self.displayMemberLabels = False

			for mbr in model.members.members.values():
				try:
					self.removeMemberLabel(mbr)
				except KeyError:
					continue
		else:
			self.displayMemberLabels = True
			for mbr in model.members.members.values():
				self.addMemberLabel(mbr)

	def addMemberiPin(self, mbr):
		if self.displayMemberPins:
			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z

			# build a point vector for the i coordinate
			i = np.array([ix,iy,iz])

			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z

			# build a point vector for the i coordinate
			j = np.array([jx, jy, jz])

			# calculate the location of the pin
			p = i + (j-i) / np.linalg.norm(j-i)

			x = p[0]
			y = p[1]
			z = p[2]

			self.memberiPins[mbr] = self.axes.plot3D(
				x,
				z,
				y,
				marker='o',
				color = 'purple',
				mfc = 'none',
				alpha = 0.75,
				ms = 6,
				rasterized = True
				)

			# update the plot
			self.canvas.draw()

	def removeMemberiPin(self, mbr):
		# remove the matplotlib object from the figure
		self.memberiPins[mbr][0].remove()

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def addMemberjPin(self, mbr):
		if self.displayMemberPins:
			# node i coordinates
			ix = mbr.node_i.x
			iy = mbr.node_i.y
			iz = mbr.node_i.z

			# build a point vector for the i coordinate
			i = np.array([ix,iy,iz])

			# node j coordinates
			jx = mbr.node_j.x
			jy = mbr.node_j.y
			jz = mbr.node_j.z

			# build a point vector for the i coordinate
			j = np.array([jx, jy, jz])

			# calculate the location of the pin
			p = j + (i-j) / np.linalg.norm(j-i)

			x = p[0]
			y = p[1]
			z = p[2]

			self.memberjPins[mbr] = self.axes.plot3D(
				x,
				z,
				y,
				marker='o',
				color = 'purple',
				mfc = 'none',
				alpha = 0.75,
				ms = 6,
				rasterized = True
				)

			# update the plot
			self.canvas.draw()
	
	def removeMemberjPin(self, mbr):
		# remove the matplotlib object from the figure
		self.memberjPins[mbr][0].remove()

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showMemberPins(self, model):
		if self.displayMemberPins:
			self.displayMemberPins = False

			for mbr in model.members.members.values():
				try:
					if mbr.i_release == True:
						self.removeMemberiPin(mbr)
					if mbr.j_release ==True:
						self.removeMemberjPin(mbr)
				except KeyError:
					continue
		else:
			self.displayMemberPins = True
			for mbr in model.members.members.values():
				if mbr.i_release == True:
					self.addMemberiPin(mbr)
				if mbr.j_release == True:
					self.addMemberjPin(mbr)

	def addPointLoad(self, load, Pi, Pj):
		self.pointLoads[load] = self.axes.quiver(
			Pi[0],
			Pi[2],
			Pi[1],
			Pj[0],
			Pj[2],
			Pj[1],
			color='r',
			alpha=0.2,
			lw=1
		)

		self.canvas.draw()
	
	def addPointLoadLabel(self, load, magnitude, Pi):
		if self.displayPointLoads:
			if abs(magnitude) > 1*10**-6:
				# define offset distance of member labels from the members
				dx = self.label_offset
				dy = self.label_offset
				dz = self.label_offset

				self.pointLoadLabels[load] = self.axes.text(
					Pi[0]+dx,
					Pi[2]+dz,
					Pi[1]+dy,
					'{load} K'.format(load=round(magnitude,3)),
					fontsize = 8,
					color = 'red',
					rasterized = True
				)

				# update the plot
				self.canvas.draw()		

	def removePointLoad(self, load):
		# identify the matplotlib object associated with the load
		load_id = self.pointLoads[load]
		label = self.pointLoadLabels[load]

		# remove the matplotlib object from the figure
		load_id.remove()
		self.pointLoads.pop(load)

		label.remove()
		self.pointLoadLabels.pop(load)

		# update the plot
		self.canvas.draw_idle()
		self.canvas.flush_events()

	def updatePointLoads(self, model, loadCombination):
		if self.displayPointLoads:
			for load in model.loads.pointLoads.values():
				load.calculateASD()

			for load in model.loads.pointLoads.values():
				# Determine the user defined load to display
				P = self.normalizePointLoad(model, load, loadCombination)

				# Calculate the member rotation matrix and local unit vector
				axis, RM = self.rotationMatrix(load.member)

				# calculate the local x, y and z coordinates of the point load
				try:
					location = float(load.location)/100
				except ValueError:
					location = 0

				Pi = axis*float(location) + np.array(
					[
						load.member.node_i.x,
						load.member.node_i.y,
						load.member.node_i.z
					]
				)

				Pi, Pj = self.translate(Pi, load.direction, P, RM)

				P = load.loadCombinations[loadCombination] 

				# remove the matplotlib object associatred with the old load from
				# the figure before replotting the new point load
				try:
					self.removePointLoad(load)
					self.addPointLoad(load, Pi, Pj)
					self.addPointLoadLabel(load, P, Pi)
				except KeyError:
					self.addPointLoad(load, Pi, Pj)
					self.addPointLoadLabel(load, P, Pi)

	def showPointLoads(self, model, loadCombination):
		if self.displayPointLoads:
			self.displayPointLoads = False

			for load in model.loads.pointLoads.values():
				self.removePointLoad(load)

		else:
			self.displayPointLoads = True
			for load in model.loads.pointLoads.values():
				self.updatePointLoads(model, loadCombination)

	def addDistLoad(self, load, W1i, W1j, W2i, W2j):
		if self.displayDistLoads:
			x = np.array([W1i[0], W1j[0], W2j[0], W2i[0]])
			y = np.array([W1i[1], W1j[1], W2j[1], W2i[1]])
			z = np.array([W1i[2], W1j[2], W2j[2], W2i[2]])

			self.distLoads[load] = self.axes.add_collection3d(
				Poly3DCollection(
					[list(zip(x,z,y))],
					lw = 1,
					alpha = 0.2,
					facecolor = 'lavender',
					edgecolor = 'purple'
				)
			)

			W1j = W1j - W1i

			self.startLoads[load] = self.axes.quiver(
				W1i[0],
				W1i[2],
				W1i[1],
				W1j[0],
				W1j[2],
				W1j[1],
				color='purple',
				alpha=0.25,
				lw=1
			)

			W2j = W2j - W2i

			self.endLoads[load] = self.axes.quiver(
				W2i[0],
				W2i[2],
				W2i[1],
				W2j[0],
				W2j[2],
				W2j[1],
				color='purple',
				alpha=0.25,
				lw=1
			)

	def removeStartLoad(self, load):
		self.startLoads[load].remove()
		self.startLoads.pop(load)

	def removeEndLoad(self, load):
		self.endLoads[load].remove()
		self.endLoads.pop(load)

	def removeDistLoad(self, load):
		# remove the matplotlib object from the figure
		try:
			self.distLoads[load].remove()
			self.distLoads.pop(load)
		except KeyError:
			pass
		try:
			self.removeStartLoad(load)
		except KeyError:
			pass
		try:
			self.removeStartLoadLabel(load)
		except KeyError:
			pass
		try:
			self.removeEndLoad(load)
		except KeyError:
			pass
		try:
			self.removeEndLoadLabel(load)
		except KeyError:
			pass
	
	def addStartLoadLabel(self, load, magnitude, W1i):
		if self.displayDistLoads:
			if abs(magnitude) >1*10**-6:
				# define offset distance of member labels from the members
				dx = self.label_offset
				dy = self.label_offset
				dz = self.label_offset

				self.startLoadLabels[load] = self.axes.text(
					W1i[0]+dx,
					W1i[2]+dz,
					W1i[1]+dy,
					'{load} K'.format(load=round(magnitude,3)),
					fontsize = 8,
					color = 'purple',
					rasterized = True
				)

	def removeStartLoadLabel(self, load):
		self.startLoadLabels[load].remove()
		self.startLoadLabels.pop(load)

	def addEndLoadLabel(self, load, magnitude, W2i):
		if self.displayDistLoads:
			if abs(magnitude) >1*10**-6:
				# define offset distance of member labels from the members
				dx = self.label_offset
				dy = self.label_offset
				dz = self.label_offset

				self.endLoadLabels[load] = self.axes.text(
					W2i[0]+dx,
					W2i[2]+dz,
					W2i[1]+dy,
					'{load} K'.format(load=round(magnitude,3)),
					fontsize = 8,
					color = 'purple',
					rasterized = True
				)

	def removeEndLoadLabel(self, load):
		self.endLoadLabels[load].remove()
		self.endLoadLabels.pop(load)

	def updateDistLoads(self, model, loadCombination):
		if self.displayDistLoads:
			for load in model.loads.distLoads.values():
				load.calculateASD()

			for load in model.loads.distLoads.values():
				# determine the user defined load to display
				W1, W2 = self.normalizeDistLoad(model, load, loadCombination)

				# calculate the member rotation matrix and local unit vector
				axis, RM = self.rotationMatrix(load.member)

				# calculate the local x, y, and z coordinates of the 
				# distributed load start and end points
				try:
					startLocation = float(load.location[0])/100
				except ValueError:
					startLocation = 0

				try:
					endLocation = float(load.location[1])/100
				except ValueError:
					endLocation = 1

				W1i = axis*float(startLocation) + np.array(
					[
						load.member.node_i.x,
						load.member.node_i.y,
						load.member.node_i.z
					]
				)

				W1i, W1j = self.translate(W1i, load.direction, W1, RM)

				W1j = W1i + W1j

				W2i = axis*float(endLocation) + np.array(
					[
						load.member.node_i.x,
						load.member.node_i.y,
						load.member.node_i.z
					]
				)

				W2i, W2j = self.translate(W2i, load.direction, W2, RM)

				W2j = W2i + W2j

				W1 = load.loadCombinations_S[loadCombination]
				W2 = load.loadCombinations_E[loadCombination]

				# remove the matplotlib object associatred with the old load
				# from the figure before replotting the new point load
				self.removeDistLoad(load)
				self.addDistLoad(load, W1i, W1j, W2i, W2j)
				self.addStartLoadLabel(load, W1, W1i)
				self.addEndLoadLabel(load, W2, W2i)

			self.canvas.draw_idle()
			self.canvas.flush_events()

	def showDistLoads(self, model, loadCombination):
		if self.displayDistLoads:
			self.displayDistLoads = False
			for load in model.loads.distLoads.values():
				self.removeDistLoad(load)
			
			# update the plot
			self.canvas.draw_idle()
			self.canvas.flush_events()

		else:
			self.displayDistLoads = True
			self.updateDistLoads(model, loadCombination)

	def normalizePointLoad(self, model, load, loadCombination):

		# determine the user defined load to display
		P = load.loadCombinations[loadCombination]

		pointLoads = []

		for load in model.loads.pointLoads.values():
			pointLoads.append(load.loadCombinations[loadCombination])

		maxPointLoad = abs(max(pointLoads, key=lambda x: abs(x)))
		
		try:
			P = (P / maxPointLoad)*5
		except ZeroDivisionError:
			return(P)

		return(P)

	def normalizeDistLoad(self, model, load, loadCombination):
		# determine the user defined load to display
		W1i = load.loadCombinations_S[loadCombination]
		W2i = load.loadCombinations_E[loadCombination]

		distLoads = []

		for load in model.loads.distLoads.values():
			distLoads.append(load.loadCombinations_S[loadCombination])
			distLoads.append(load.loadCombinations_E[loadCombination])

		maxDistLoad = abs(max(distLoads, key=lambda x: abs(x)))

		try:
			W1i = (W1i / maxDistLoad)*3
		except ZeroDivisionError:
			W1i = W1i

		try:
			W2i = (W2i / maxDistLoad)*3
		except ZeroDivisionError:
			W2i = W2i

		return (W1i, W2i)

	def translate(self, Pi, direction, magnitude, TM):

		if direction == 'X':
			Pi = Pi - np.array([magnitude,0,0])
			Pj = [magnitude,0,0]
		elif direction == 'Y':
			Pi = Pi - np.array([0,magnitude,0])
			Pj = [0,magnitude,0]
		elif direction == 'Z':
			Pi = Pi - np.array([0,0,magnitude])
			Pj = [0,0,magnitude]
		elif direction == 'x':
			# convert the load application point to local coordinates
			Pi = np.matmul(Pi,TM)
			# calculate the vector origin and magnitude
			Pi = Pi - np.array([magnitude,0,0])
			Pj = (magnitude,0,0)
			# convert the vector origin and magnitude to global coordinates
			Pi = np.matmul(TM,Pi)
			Pj = np.matmul(TM,Pj)
		elif direction == 'y':
			# convert the load application point to local coordinates
			Pi = np.matmul(Pi,TM)
			# calculate the vector origin and magnitude
			Pi = Pi - np.array([0,magnitude,0])
			Pj = (0,magnitude,0)
			# convert the vector origin and magnitude to global coordinates
			Pi = np.matmul(TM,Pi)
			Pj = np.matmul(TM,Pj)
		elif direction == 'z':
			# convert the load application point to local coordinates
			Pi = np.matmul(Pi,TM)
			# calculate the vector origin and magnitude
			Pi = Pi - np.array([0,0,magnitude])
			Pj = (0,0,magnitude)
			# convert the vector origin and magnitude to global coordinates
			Pi = np.matmul(TM,Pi)
			Pj = np.matmul(TM,Pj)

		return(Pi, Pj)

	def rotationMatrix(self, mbr):
		# assign nodal coordinates to a local variable for readability
		ix = mbr.node_i.x
		iy = mbr.node_i.y
		iz = mbr.node_i.z
		jx = mbr.node_j.x
		jy = mbr.node_j.y
		jz = mbr.node_j.z

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
		local_x_vector = np.array([jx,jy,jz]) - np.array([ix,iy,iz])
		local_x_unit = local_x_vector / np.linalg.norm(local_x_vector)

		# determine the local y-vector and unit y-vector of the member
		# in the global reference frame. This calculation requires the
		# definition of a reference point that lies in the local x-y
		# plane in order to utilize the Gram-Schmidt process vector.
		node_k = i_offset + 0.5*(j_offset-i_offset)
		vector_in_plane = node_k-np.array([ix,iy,iz])
		#local y-vector in global RF (Gram-Schmidt)
		local_y_vector = vector_in_plane - np.dot(vector_in_plane,local_x_unit)*local_x_unit
		#Length of local y-vector
		magY = np.sqrt(local_y_vector[0]**2 + local_y_vector[1]**2 + local_y_vector[2]**2)
		#Local unit vector defining the local y-axis
		local_y_unit = local_y_vector/magY

		#Local z-vector in global RF using matrix cross product
		#Local unit vector defining the local z-axis
		local_z_unit = np.cross(local_x_unit, local_y_unit) 
		# combine reference frame into a standard rotation matrix for 
		# the element x,y,z => columns 1,2,3
		RM = np.array([local_x_unit, local_y_unit, local_z_unit]).T

		return(local_x_vector, RM)

	def show_xReaction(self, node, coordinates, Rx_max):
		Pi = np.array([
				coordinates.x - node.Rx/Rx_max*self.reactionScale,
				coordinates.y,
				coordinates.z
		])

		Pj = np.array([
			coordinates.x,
			coordinates.y,
			coordinates.z
		])

		Pj = Pj - Pi

		self.xReactions[node] = self.axes.quiver(
					Pi[0],
					Pi[2],
					Pi[1],
					Pj[0],
					Pj[2],
					Pj[1],
					color = 'g',
					alpha = 0.5,
					lw = 1
				)

		self.show_xReactionLabel(node, Pi)

	def show_xReactionLabel(self, node, Pi):
		if abs(node.Rx) > 1*10**-6:
			# define offset distance of member labels from the members
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			self.xReactionLabels[node] = self.axes.text(
				Pi[0]+dx,
				Pi[2]+dz,
				Pi[1]+dy,
				'{rxn} K'.format(rxn=round(node.Rx,1)),
				fontsize = 8,
				color = 'g',
				rasterized = True
			)

	def remove_xReaction(self, node):
		# identify the matplotlib object associated with the load		
		reaction_id = self.xReactions[node]
		reactionLabel_id = self.xReactionLabels[node]

		# remove the matplotlib object from the figure
		reaction_id.remove()
		self.xReactions.pop(node)

		reactionLabel_id.remove()
		self.xReactionLabels.pop(node)	

	def show_MxReaction(self, node, coordinates, Mx_max):
		if abs(node.Rmx) > 1*10**-6:
			if node.Rmx:
				marker = r"$\circlearrowright$"
			else:
				marker = r"$\circlearrowleft$"

			# node with pinned restraint
			self.MxReactions[node] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.y,
				node.coordinates.z,

				color = 'g',
				marker = marker,
				alpha = 0.25,
				markersize = 25,
				linewidth = node.Rmx/Mx_max*self.reactionScale,	
			)

			self.show_MxReactionLabel(node)

	def show_MxReactionLabel(self, node):
		if abs(node.Rmx) > 1*10**-6:
			# define offset distance of label from the patch
			dx = -1*self.label_offset
			dy = -1*self.label_offset
			dz = -1*self.label_offset

			self.MxReactionLabels[node] = self.axes.text(
				node.coordinates.x+dx,
				node.coordinates.z+dz,
				node.coordinates.y+dy,
				'{rxn} K'.format(rxn=round(node.Rmx,1)),
				fontsize = 8,
				color = 'g',
				rasterized = True
			)

	def remove_MxReaction(self, node):
		# identify the matplotlib object associated with the load		
		reaction_id = self.MxReactions[node][0]
		reactionLabel_id = self.MxReactionLabels[node]

		# remove the matplotlib object from the figure
		reaction_id.remove()
		self.MxReactions.pop(node)

		reactionLabel_id.remove()
		self.MxReactionLabels.pop(node)

	def show_yReaction(self, node, coordinates, Ry_max):
		Pi = np.array([
				coordinates.x,
				coordinates.y - node.Ry/Ry_max*self.reactionScale,
				coordinates.z
		])

		Pj = np.array([
			coordinates.x,
			coordinates.y,
			coordinates.z
		])

		Pj = Pj - Pi

		self.yReactions[node] = self.axes.quiver(
					Pi[0],
					Pi[2],
					Pi[1],
					Pj[0],
					Pj[2],
					Pj[1],
					color = 'g',
					alpha = 0.5,
					lw = 1
				)

		self.show_yReactionLabel(node, Pi)

	def show_yReactionLabel(self, node, Pi):
		if abs(node.Ry) > 1*10**-6:
			# define offset distance of member labels from the members
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			self.yReactionLabels[node] = self.axes.text(
				Pi[0]+dx,
				Pi[2]+dz,
				Pi[1]+dy,
				'{rxn} K'.format(rxn=round(node.Ry,1)),
				fontsize = 8,
				color = 'g',
				rasterized = True
			)

	def remove_yReaction(self, node):
		# identify the matplotlib object associated with the load		
		reaction_id = self.yReactions[node]
		reactionLabel_id = self.yReactionLabels[node]

		# remove the matplotlib object from the figure
		reaction_id.remove()
		self.yReactions.pop(node)		

		reactionLabel_id.remove()
		self.yReactionLabels.pop(node)

	def show_MyReaction(self, node, coordinates, My_max):
		if abs(node.Rmy) > 1*10**-6:
			if node.Rmy > 0:
				marker = r"$\circlearrowright$"
			else:
				marker = r"$\circlearrowleft$"

			# node with pinned restraint
			self.MyReactions[node] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.y,
				node.coordinates.z,
				color = 'g',
				marker = marker,
				alpha = 0.25,
				markersize = 25,
				linewidth = node.Rmy/My_max*self.reactionScale,	
			)

	def remove_MyReaction(self, node):
		self.MyReactions[node][0].remove()
		self.MxReactionLabels[node].remove()
		self.MxReactions.pop(node)
		self.MxReactionLabels.pop(node)

	def show_zReaction(self, node, coordinates, Rz_max):
		Pi = np.array([
				coordinates.x,
				coordinates.y,
				coordinates.z - node.Rz/Rz_max*self.reactionScale
		])

		Pj = np.array([
			coordinates.x,
			coordinates.y,
			coordinates.z
		])

		Pj = Pj - Pi

		self.zReactions[node] = self.axes.quiver(
					Pi[0],
					Pi[2],
					Pi[1],
					Pj[0],
					Pj[2],
					Pj[1],
					color = 'g',
					alpha = 0.5,
					lw = 1
				)

		self.show_zReactionLabel(node, Pi)

	def show_zReactionLabel(self, node, Pi):
		if abs(node.Rz) > 1*10**-6:
			# define offset distance of member labels from the members
			dx = self.label_offset
			dy = self.label_offset
			dz = self.label_offset

			self.zReactionLabels[node] = self.axes.text(
				Pi[0]+dx,
				Pi[2]+dz,
				Pi[1]+dy,
				'{rxn} K'.format(rxn=round(node.Rz,1)),
				fontsize = 8,
				color = 'g',
				rasterized = True
			)

	def remove_zReaction(self, node):
		# identify the matplotlib object associated with the load		
		reaction_id = self.zReactions[node]
		reactionLabel_id = self.zReactionLabels[node]

		# remove the matplotlib object from the figure
		reaction_id.remove()
		self.zReactions.pop(node)		

		reactionLabel_id.remove()
		self.zReactionLabels.pop(node)

	def show_MzReaction(self, node, coordinates, Mz_max):
		if abs(node.Rmz) > 1*10**-6:
			if node.Rmz > 0:
				marker = r"$\circlearrowright$"
			else:
				marker = r"$\circlearrowleft$"

			# node with pinned restraint
			self.MyReactions[node] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.y,
				node.coordinates.z,
				color = 'g',
				marker = marker,
				alpha = 0.25,
				markersize = 25,
				linewidth = node.Rmz/Mz_max*self.reactionScale,	
			)

	def remove_MzReaction(self, node):
		self.MzReactions[node][0].remove()
		self.MzReactionLabels[node].remove()
		self.MzReactions.pop(node)
		self.MzReactionLabels.pop(node)

	def showReactions(self, femModel, reaction=None):
		if reaction == None:
			return
		for coordinates, node in femModel.nodes.nodes.items():
			if node.meshNode == True or node.restraint == [0,0,0,0,0,0]:
				continue
			else:
				if reaction == 'Fx':
					self.show_xReaction(node, coordinates, femModel.Rx_max)
				if reaction == 'Fy':
					self.show_yReaction(node, coordinates, femModel.Ry_max)
				if reaction == 'Fz':
					self.show_zReaction(node, coordinates, femModel.Rz_max)
				if reaction == 'Mx':
					self.show_MxReaction(node, coordinates, femModel.Rmx_max)
				if reaction == 'My':
					self.show_MyReaction(node, coordinates, femModel.Rmy_max)
				if reaction == 'Mz':
					print('Plotting Rmz')
					self.show_MzReaction(node, coordinates, femModel.Rmz_max)

		self.canvas.draw_idle()
		self.canvas.flush_events()
 
	def removeReactions(self, femModel, reaction=None):
		for node in femModel.nodes.nodes.values():
			if node.meshNode == True:
				continue
			else:
				if reaction == None:
					try:
						self.remove_xReaction(node)
					except KeyError:
						pass
					try:
						self.remove_yReaction(node)
					except KeyError:
						pass
					try:	
						self.remove_zReaction(node)
					except KeyError:
						pass
					try:
						self.remove_MxReaction(node)
					except KeyError:
						pass
					try:
						self.remove_MyReaction(node)
					except KeyError:
						pass
					try:
						self.remove_MzReaction(node)
					except KeyError:
						pass
				if reaction == 'Fx':
					try:
						self.remove_xReaction(node)
					except KeyError:
						pass
				if reaction == 'Fy':
					try:
						self.remove_yReaction(node)
					except KeyError:
						pass
				if reaction == 'Fz':
					try:
						self.remove_zReaction(node)
					except KeyError:
						pass
				if reaction == 'Mx':
					try:
						self.remove_MxReaction(node)
					except KeyError:
						pass
				if reaction == 'My':
					try:
						self.remove_MyReaction(node)
					except KeyError:
						pass
				if reaction == 'Mz':
					try:
						self.remove_MzReaction(node)
					except KeyError:
						pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showDeformation(self, femModel):
		scaleFactor = self.deflectionScale

		UG = femModel.solver.UG

		for mbr in femModel.members.members.values():
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

				self.deflection[submbr] = self.axes.plot3D(
					[
						ix + UG[ia,0]*scaleFactor,
						jx + UG[ja,0]*scaleFactor
					],
					[
						iz + UG[ib,0]*scaleFactor,
						jz + UG[jb,0]*scaleFactor
					],
					[
						iy + UG[ia+1,0]*scaleFactor,
						jy + UG[ja+1,0]*scaleFactor
					],
					color = 'purple',
					lw=0.5,
					rasterized = True
				)

		self.canvas.draw()

	def removeDeformation(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.deflection[submbr][0].remove()

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showVy(self, femModel):
		# define the scale factor for the shear diagram
		scale = self.forceScale
		shearScale = femModel.Vy_max
		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
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
				si = submbr.results['shear'][0]/shearScale*scale
				sj = submbr.results['shear'][1]/shearScale*scale

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

				# add label if current force is local minima or maxima
				if femModel.Vy_maxima[i] or femModel.Vy_minima[i]:
					self.addVyLabel(submbr, submbr.node_i, si)
				if femModel.Vy_maxima[j] or femModel.Vy_minima[j]:
					self.addVyLabel(submbr, submbr.node_j, sj)

				# plot the shear force diagram
				self.Vy[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[
							list(zip(xr,zr,yr))
						],
						lw=0.0,
						alpha=0.1,
						facecolor='green'
					)
				)

		self.canvas.draw()

	def addVyLabel(self, submbr, node, shear):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,shear,0]
		)))		

		self.VyLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{Vy} K'.format(Vy=round(
				max(
					abs(submbr.results['shear'][0]),
					abs(submbr.results['shear'][1])
				),1
			)),
			fontsize = 8,
			color = 'green',
			rasterized = True
		)		

	def removeVy(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.Vy[submbr].remove()
				self.Vy.pop(submbr)

				try:
					self.VyLabels[submbr].remove()
					self.VyLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showVz(self, femModel):
		# define the scale factor for the shear diagram
		scale = self.forceScale
		shearScale = femModel.Vz_max
		

		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
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
				si = submbr.results['transverse shear'][0]/shearScale*scale
				sj = submbr.results['transverse shear'][1]/shearScale*scale 

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
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,si])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,sj])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment SFD
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# add label if current force is local minima or maxima
				if femModel.Vz_maxima[i] or femModel.Vz_minima[i]:
					self.addVzLabel(submbr, submbr.node_i, si)
				if femModel.Vz_maxima[j] or femModel.Vz_minima[j]:
					self.addVzLabel(submbr, submbr.node_j, sj)

				# plot the shear force diagram
				self.Vz[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[
							list(zip(xr,zr,yr))
						],
						lw=0.0,
						alpha=0.1,
						facecolor='green'
					)
				)

		self.canvas.draw()

	def addVzLabel(self, submbr, node, shear):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,0,shear]
		)))		

		self.VzLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{Vz} K'.format(Vz=round(
				max(
					abs(submbr.results['transverse shear'][0]),
					abs(submbr.results['transverse shear'][1])
				),1
			)),
			fontsize = 8,
			color = 'green',
			rasterized = True
		)		

	def removeVz(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.Vz[submbr].remove()
				self.Vz.pop(submbr)

				try:
					self.VzLabels[submbr].remove()
					self.VzLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showMzz(self, femModel):
		# define the scale factor for the moment diagram
		scale = self.forceScale
		momentScale = femModel.Mzz_max

		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
				# node i coordinates
				ix = submbr.node_i.coordinates.x
				iy = submbr.node_i.coordinates.y
				iz = submbr.node_i.coordinates.z
				# node j coordinates
				jx = submbr.node_j.coordinates.x
				jy = submbr.node_j.coordinates.y
				jz = submbr.node_j.coordinates.z
				# member moments
				mi = submbr.results['major axis moments'][0]/momentScale*scale
				mj = submbr.results['major axis moments'][1]/momentScale*scale

				# correct the shape of the segment moment diagram
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

				# rotate diagram to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,mi,0])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,mj,0])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment moment diagram
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# add label if current force is local minima or maxima
				if femModel.Mzz_maxima[i] or femModel.Mzz_minima[i]:
					self.addMzzLabel(submbr, submbr.node_i, mi)
				if femModel.Mzz_maxima[j] or femModel.Mzz_minima[j]:
					self.addMzzLabel(submbr, submbr.node_j, mj)

				# plot the segment moment diagram
				self.Mzz[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[
							list(zip(xr,zr,yr))
						],
						lw=0.0,
						alpha=0.1,
						facecolor='blue',
						edgecolor='blue'
					)
				)

		self.canvas.draw()

	def addMzzLabel(self, submbr, node, moment):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,moment,0]
		)))		

		self.MzzLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{Mzz} k-ft'.format(Mzz=round(
				max(
					abs(submbr.results['major axis moments'][0]),
					abs(submbr.results['major axis moments'][1])
				)/12,1
			)),
			fontsize = 8,
			color = 'blue',
			rasterized = True
		)		
	
	def removeMzz(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.Mzz[submbr].remove()
				self.Mzz.pop(submbr)

				try:
					self.MzzLabels[submbr].remove()
					self.MzzLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showMyy(self, femModel):
		# define the scale factor for the moment diagram
		scale = self.forceScale
		momentScale = femModel.Myy_max

		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
				# node i coordinates
				ix = submbr.node_i.coordinates.x
				iy = submbr.node_i.coordinates.y
				iz = submbr.node_i.coordinates.z
				# node j coordinates
				jx = submbr.node_j.coordinates.x
				jy = submbr.node_j.coordinates.y
				jz = submbr.node_j.coordinates.z
				# member moments
				mi = submbr.results['minor axis moments'][0]/momentScale*scale
				mj = submbr.results['minor axis moments'][1]/momentScale*scale

				# correct the shape of the segment moment diagram
				if(mi<0 and mj>0):
					mi = abs(mi)
					mj = abs(mj)
				elif(mi<0 and mj<0):
					mi = abs(mi)
					mj = -abs(mj)
				elif(mi>0 and mj>0):
					mi = -abs(mi)
					mj = abs(mj)
				elif(mi>0 and mj<0):
					mi = -abs(mi)
					mj = -abs(mj)
				elif(mi>0 and mj==0): # probably need this to be something close to zero
					mi = -abs(mi)
				elif(mi<0 and mj==0): # probably need this to be something close to zero
					mi = abs(mi)

				# rotate diagram to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,mi])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,mj])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment moment diagram
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# add label if current force is local minima or maxima
				if femModel.Myy_maxima[i] or femModel.Myy_minima[i]:
					self.addMyyLabel(submbr, submbr.node_i, mi)
				if femModel.Myy_maxima[j] or femModel.Myy_minima[j]:
					self.addMyyLabel(submbr, submbr.node_j, mj)

				# plot the segment moment diagram
				self.Myy[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[
							list(zip(xr,zr,yr))
						],
						lw=0.0,
						alpha=0.1,
						facecolor='blue',
						edgecolor='blue'
					)
				)

		self.canvas.draw()

	def addMyyLabel(self, submbr, node, moment):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,0,moment]
		)))		

		self.MyyLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{Myy} k-ft'.format(Myy=round(
				max(
					abs(submbr.results['minor axis moments'][0]),
					abs(submbr.results['minor axis moments'][1])
				)/12,1
			)),
			fontsize = 8,
			color = 'blue',
			rasterized = True
		)

	def removeMyy(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.Myy[submbr].remove()
				self.Myy.pop(submbr)

				try:
					self.MyyLabels[submbr].remove()
					self.MyyLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showAxial(self, femModel):
		# define the scale factor for the shear diagram
		scale = self.forceScale
		axialScale = femModel.axial_max

		# plot the axial force diagram
		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
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
				# member axial forces
				ai = submbr.results['axial'][0]/axialScale*scale
				aj = submbr.results['axial'][1]/axialScale*scale

				# correct the shape of the segment axial force diagram
				if(ai<0 and aj>0):
					ai = -abs(ai)
					aj = -abs(aj)
				elif(ai<0 and aj<0):
					ai = -abs(ai)
					aj = abs(aj)
				elif(ai>0 and aj>0):
					ai = abs(ai)
					aj = -abs(aj)
				elif(ai>0 and aj<0):
					ai = abs(ai)
					aj = abs(aj)
				elif(ai>0 and aj==0): # probably need this to be something close to zero
					ai = abs(ai)
				elif(ai<0 and aj==0): # probably need this to be something close to zero
					ai = -abs(ai)
				elif(ai==0 and aj>0):
					aj = -abs(aj)
				elif(ai==0 and aj<0):
					aj = abs(aj)

				# rotate SFD to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,ai,0])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,aj,0])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment SFD
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# add label if current force is local minima or maxima
				if femModel.axial_maxima[i] or femModel.axial_minima[i]:
					self.addAxialLabel(submbr, submbr.node_i, ai)
				if femModel.axial_maxima[j] or femModel.axial_minima[j]:
					self.addAxialLabel(submbr, submbr.node_j, aj)

				# plot the shear force diagram
				self.axial[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[list(zip(xr,zr,yr))],
						lw=0.0,
						alpha=0.1,
						facecolor='green'
					)
				)

		# update the plot
		self.canvas.draw()

	def addAxialLabel(self, submbr, node, axial):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,axial,0]
		)))		

		self.axialLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{axial} k'.format(axial=round(
				max(
					abs(submbr.results['axial'][0]),
					abs(submbr.results['axial'][1])
				)/12,1
			)),
			fontsize = 8,
			color = 'green',
			rasterized = True
		)

	def removeAxial(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.axial[submbr].remove()
				self.axial.pop(submbr)

				try:
					self.axialLabels[submbr].remove()
					self.axialLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

	def showTorque(self, femModel):
		# define the scale factor for the shear diagram
		scale = self.forceScale
		torqueScale = femModel.torque_max

		# plot the torque force diagram
		for mbr in femModel.members.members.values():
			for i, submbr in enumerate(mbr.submembers.values()):
				i = i*2
				j = i+1
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
				# member axial forces
				ti = submbr.results['torsional moments'][0]/torqueScale*scale
				tj = submbr.results['torsional moments'][1]/torqueScale*scale

				# correct the shape of the segment axial force diagram
				if(ti<0 and tj>0):
					ti = -abs(ti)
					tj = -abs(tj)
				elif(ti<0 and tj<0):
					ti = -abs(ti)
					tj = abs(tj)
				elif(ti>0 and tj>0):
					ti = abs(ti)
					tj = -abs(tj)
				elif(ti>0 and tj<0):
					ti = abs(ti)
					tj = abs(tj)
				elif(ti>0 and tj==0): # probably need this to be something close to zero
					ti = abs(ti)
				elif(ti<0 and tj==0): # probably need this to be something close to zero
					ti = -abs(ti)
				elif(ti==0 and tj>0):
					tj = -abs(tj)
				elif(ti==0 and tj<0):
					tj = abs(tj)

				# rotate SFD to match orientation of segment in structure
				pt1 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,0])) #Bottom left
				pt2 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([0,0,ti])) #Top left
				pt3 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,tj])) #Top right
				pt4 = np.matmul(submbr.rotationMatrix[0:3,0:3],np.array([submbr.length,0,0])) #Bottom right

				# final shifted and rotated segment SFD
				xr = ix + np.array([pt1[0], pt2[0], pt3[0], pt4[0]]) #Rotated and translated x-coords
				yr = iy + np.array([pt1[1], pt2[1], pt3[1], pt4[1]]) #Rotated and translated y-coords
				zr = iz + np.array([pt1[2], pt2[2], pt3[2], pt4[2]]) #Rotated and translated z-coords

				# add label if current force is local minima or maxima
				if femModel.torque_maxima[i] or femModel.torque_minima[i]:
					self.addTorqueLabel(submbr, submbr.node_i, ti)
				if femModel.torque_maxima[j] or femModel.torque_minima[j]:
					self.addTorqueLabel(submbr, submbr.node_j, tj)

				# plot the shear force diagram
				self.torque[submbr] = self.axes.add_collection3d(
					Poly3DCollection(
						[list(zip(xr,zr,yr))],
						lw=0.0,
						alpha=0.1,
						facecolor='blue'
					)
				)

		# update the plot
		self.canvas.draw()

	def addTorqueLabel(self, submbr, node, torque):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		ix = node.coordinates.x
		iy = node.coordinates.y
		iz = node.coordinates.z

		point = (np.matmul(
			submbr.rotationMatrix[0:3,0:3],
			np.array([0,0,torque]
		)))		

		self.torqueLabels[submbr] = self.axes.text(
			point[0]+ix+dx,
			point[2]+iz+dz,
			point[1]+iy+dy,
			'{axial} k'.format(axial=round(
				max(
					abs(submbr.results['torsional moments'][0]),
					abs(submbr.results['torsional moments'][1])
				)/12,1
			)),
			fontsize = 8,
			color = 'blue',
			rasterized = True
		)

	def removeTorque(self, femModel):
		for mbr in femModel.members.members.values():
			for submbr in mbr.submembers.values():
				self.torque[submbr].remove()
				self.torque.pop(submbr)

				try:
					self.torqueLabels[submbr].remove()
					self.torqueLabels.pop(submbr)
				except KeyError:
					pass

		self.canvas.draw_idle()
		self.canvas.flush_events()

def showAxes(self):
	for axis in ['x','y','z']:
		rectangle = Rectangle((-10, 10),1,1,fill=False, ec=(86/255,90/255,92/255))
		self.axes.add_patch(rectangle)
		art3d.pathpatch_2d_to_3d(rectangle, z=1, zdir=axis)

		rectangle = Rectangle((-10, 10),1,1,fill=True, lw=None, fc=(207/255,184/255,124/255), alpha=0.5)
		self.axes.add_patch(rectangle)
		art3d.pathpatch_2d_to_3d(rectangle, z=1, zdir=axis)

	a1 = Arrow3D([0,1.75],[0,0],[0,0], lw=1, mutation_scale=10, arrowstyle='->', color=(162/255,164/255,163/255))
	a2 = Arrow3D([0,0],[0,1.75],[0,0], lw=1, mutation_scale=10, arrowstyle='->', color=(162/255,164/255,163/255))
	a3 = Arrow3D([0,0],[0,0],[0,1.75], lw=1, mutation_scale=10, arrowstyle='->', color=(162/255,164/255,163/255))
	self.axes.add_artist(a1)
	self.axes.add_artist(a2)
	self.axes.add_artist(a3)

	self.axes.text(1.75,0,0,'X',fontsize=10,color=(86/255,90/255,92/255))
	self.axes.text(0,1.75,0,'Z',fontsize=10,color=(86/255,90/255,92/255))
	self.axes.text(0,0,1.75,'Y',fontsize=10,color=(86/255,90/255,92/255))

	# update the plot
	self.canvas.draw()

