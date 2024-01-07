import sys
import os

# import third party packages
import matplotlib
import matplotlib.style
import numpy as np

from matplotlib import markers
from matplotlib.path import Path
from matplotlib.figure import Figure

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

# Configure Matplotlib for backend use
matplotlib.use('TkAgg')

# enable line segment simplification to reduce rendering time
#https://matplotlib.org/stable/users/explain/performance.html
matplotlib.style.use('fast')
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0

# matplotlib backend imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backend_tools import ToolBase

class Plotter():
	def __init__(self, model):
		self.root = tk.Tk()
		self.model = model

		# Set the default Main Screen Properties
		self.default(self.root)

		self.plotFrame = PlotFrame(self.root, model)

		self.menu = Menu(self.root, model, self.plotFrame)

		# Display the UI manu and plotter
		self.menu.grid(column=0, row=0, sticky=['N','S','E','W'])
		self.plotFrame.grid(column=0, row=1, sticky=['N','S','E','W'])

		# Set the plotFrame to expand with the window as it is resized
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(1, weight=1)

	def default(self, root):
		# define the Main Screen title
		title = 'OpenStruct - Open Source Structural Analysis'

		# define the path to icon assets
		#icon = os.path.join('projectFiles','Icons','3DFrame.ico')

		# define the default main screen dimensions
		screenSize = '1080x720'

		# set the Main Screen title, icon, and geometry
		root.title(title)
		#root.iconbitmap(icon)
		root.geometry(screenSize)

	def on_resize(self, event):
		self.plotFrame.canvas.get_tk_widget().pack_forget()
		self.plotFrame.fig.set_size_inches(event.width/100, event.height/100)
		self.plotFrame.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)



class Menu(ttk.Notebook):
	def __init__(self, parent, model, plotFrame, *args, **kwargs):
		ttk.Notebook.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.resultsFrame = ResultsFrame(self)
		self.inputFrame = InputFrame(self, model, plotFrame)

		self.add(self.inputFrame, text = 'Input')
		self.add(self.resultsFrame, text = 'Results')

		self.grid(row=0, column=0, sticky='NSEW')

		self.select(self.resultsFrame)

class PlotFrame(tk.Frame):
	def __init__(self, parent, model):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		# define plotting variables
		self.nodes = {}
		self.nodeLabels = {}
		self.restraints = {}
		self.members = {}
		self.mbrLabels = {}

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
		self.toolbar = CustomToolbar(self.canvas, self.axes, self)
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

	def displayNodes(self, model, displayFlag):
		for node in model.nodes.nodes.values():
			if node.meshNode:
				continue
			else:
				if displayFlag:
					self.addNode(node) 
				else:
					self.removeNode(node)

		self.update()

	def addNode(self, node):
		self.nodes[node.nodeID] = self.axes.plot3D(
			node.coordinates.x,
			node.coordinates.z,
			node.coordinates.y,
			'go',
			ms = 3,
			rasterized = True
			)

	def removeNode(self, node):
		self.nodes[node.nodeID][0].remove()
		self.nodes.pop(node.nodeID)

	def displayNodeLabels(self, model, displayFlag):
		for node in model.nodes.nodes.values():
			if node.meshNode:
				continue
			else:
				if displayFlag:
					self.addNodeLabel(node)
				else:
					self.removeNodeLabel(node)

		self.update()

	def addNodeLabel(self, node):
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		self.nodeLabels[node.nodeID] = self.axes.text(
			node.coordinates.x+dx,
			node.coordinates.z+dz,
			node.coordinates.y+dy,
			'N{i}'.format(i=node.nodeID),
			fontsize = 10,
			color = 'green',
			rasterized = True
		)

	def removeNodeLabel(self, node):
		# remove the matplotlib object from the figure
		self.nodeLabels[node.nodeID].remove()
		self.nodeLabels.pop(node.nodeID)

	def displayRestraints(self, model, displayFlag):
		for node in model.nodes.nodes.values():
			if node.meshNode:
				continue
			else:
				if displayFlag:
					self.addRestraint(node)
				else:
					self.removeRestraint(node)

		self.update()

	def addRestraint(self, node):
		# unrestrained node
		if node.restraint == [0,0,0,0,0,0]:
			return

		# node with pinned restraint
		elif node.restraint == [1,1,1,0,0,0]:
			self.restraints[node.nodeID] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.z,
				node.coordinates.y,
				'r',
				marker = self.alignMarker('^', valign='top'),
				alpha = 0.25,
				markersize = 20
			)

		# node with roller restraint
		elif node.restraint in [[0,1,1,0,0,0],[1,1,0,0,0,0],[1,0,1,0,0,0]]:
			self.restraints[node.nodeID] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.z,
				node.coordinates.y,
				'r',
				marker = self.alignMarker('o', valign = 'top'),
				alpha = 0.25,
				markersize = 20
			)

		# node with fixed restraint
		elif node.restraint == [1,1,1,1,1,1]:
			self.restraints[node.nodeID] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.z,
				node.coordinates.y,
				'r',
				marker = self.alignMarker('s', valign = 'top'),
				alpha = 0.25,
				markersize = 20
			)

		# node with custom restraint
		else:
			self.restraints[node] = self.axes.plot3D(
				node.coordinates.x,
				node.coordinates.z,
				node.coordinates.y,
				'r',
				marker = align_marker('x', valign = 'top'),
				alpha = 0.25,
				markersize = 20
			)

	def removeRestraint(self, node):
		self.restraints[node.nodeID][0].remove()
		self.restraints.pop(node.nodeID)
	
	def displayMbrs(self, model, displayFlag):
		for mbr in model.members.members.values():
			if displayFlag:
				self.addMbr(mbr)
			else:
				self.removeMbr(mbr)

		self.update()

	def addMbr(self, mbr):
		# node i coordinates
		ix = mbr.node_i.coordinates.x
		iy = mbr.node_i.coordinates.y
		iz = mbr.node_i.coordinates.z
		# node j coordinates
		jx = mbr.node_j.coordinates.x
		jy = mbr.node_j.coordinates.y
		jz = mbr.node_j.coordinates.z
		# add the members to the axes
		self.members[mbr] = self.axes.plot3D(
			[ix, jx],
			[iz, jz],
			[iy, jy],
			'grey',
			lw=0.75
		)

	def removeMbr(self, mbr):
		self.members[mbr][0].remove()
		self.members.pop(mbr)

	def displayMbrLabels(self, model, displayFlag):
		for mbr in model.members.members.values():
			if displayFlag:
				self.addMbrLabel(mbr)
			else:
				self.removeMbrLabel(mbr)

		self.update()

	def addMbrLabel(self, mbr):
		# define offset distance of member labels from the members
		dx = self.label_offset
		dy = self.label_offset
		dz = self.label_offset

		# node i coordinates
		ix = mbr.node_i.coordinates.x
		iy = mbr.node_i.coordinates.y
		iz = mbr.node_i.coordinates.z

		# node j coordinates
		jx = mbr.node_j.coordinates.x
		jy = mbr.node_j.coordinates.y
		jz = mbr.node_j.coordinates.z

		# calculate the midpoint coordinates of the member
		x = (jx + ix) / 2 + dx
		y = (jy + iy) / 2 + dy
		z = (jz + iz) / 2 + dz

		# add the member label to the axes
		self.mbrLabels[mbr] = self.axes.text(
			x,
			z,
			y,
			'M{i}'.format(i=mbr.mbrID),
			fontsize = 10,
			color = 'grey',
			rasterized = True
		)

	def removeMbrLabel(self, mbr):
		self.mbrLabels[mbr].remove()
		self.mbrLabels.pop(mbr)

	def displayMbrPins(self, model, displayFlag):
		pass


	def alignMarker(self, marker, valign='top'):
		# https://stackoverflow.com/questions/26686722/align-matplotlib-scatter-marker-left-and-or-right
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

	def update(self):
		self.canvas.draw_idle()
		self.canvas.flush_events()


class ResultsFrame(ttk.Frame):
	def __init__(self, parent, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)
		self.parent = parent

class InputFrame(ttk.Frame):
	def __init__(self, parent, model, plotFrame, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)
		self.parent = parent

		self.nodes = NodeFrame(self, model, plotFrame)
		self.members = memberFrame(self, model, plotFrame)

		self.nodes.grid(column=0, row=0)
		ttk.Separator(self,orient='vertical').grid(column=1,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.members.grid(column=2, row=0)

class NodeFrame(ttk.Frame):
	def __init__(self, parent, model, plotFrame, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)
		self.parent = parent

		buttonWidth = 30
		
		self.displayNodesFlag = True
		plotFrame.displayNodes(model, True)

		self.displayNodeLabelsFlag = True
		plotFrame.displayNodeLabels(model, True)

		self.displayRestraintsFlag = True
		plotFrame.displayRestraints(model, True)

		self.displayNodes_Var = tk.StringVar()
		self.displayNodes_Var.set('1')

		self.displayNodes = ttk.Checkbutton(
			self,
			text = 'Display Nodes',
			variable = self.displayNodes_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: self.showNodes(model, plotFrame)
		)

		self.displayNodeLabels_Var = tk.StringVar()
		self.displayNodeLabels_Var.set('1')

		self.displayNodeLabels = ttk.Checkbutton(
			self,
			text = 'Display Node Labels',
			variable = self.displayNodeLabels_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: self.showNodeLabels(model, plotFrame),
			width = buttonWidth
		)

		self.displayRestraints_Var = tk.StringVar()
		self.displayRestraints_Var.set('1')
		
		self.displayRestraints = ttk.Checkbutton(
			self,
			text = 'Display Nodal Restraints',
			variable = self.displayRestraints_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: self.showRestraints(model, plotFrame),
			width = buttonWidth
		)

		self.nodeLabel = ttk.Label(
			self,
			text = 'Nodes',
			anchor = 'center',
			font = 10
		)

		self.displayNodes.grid(column=0, row=0, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.displayNodeLabels.grid(column=0, row=1, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.displayRestraints.grid(column=0, row=2, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.nodeLabel.grid(column=0, row=3, sticky=['E','W'], padx=[5,5], pady=[5,5])

	def showNodes(self, model, plotFrame):
		if self.displayNodesFlag:
			self.displayNodesFlag = False
			self.displayNodeLabelsFlag = False
			self.displayRestraintsFlag = False

			plotFrame.displayNodes(model, False)

			if self.displayNodeLabels_Var.get() == '1':
				self.displayNodeLabels_Var.set('0')
				plotFrame.displayNodeLabels(model, False)

			if self.displayRestraints_Var.get() == '1':
				self.displayRestraints_Var.set('0')
				plotFrame.displayRestraints(model, False)

			self.displayNodeLabels['state'] = 'disabled'
			self.displayRestraints['state'] = 'disabled'

		else:
			self.displayNodesFlag = True
			self.displayNodeLabelsFlag = True
			self.displayRestraintsFlag = True

			plotFrame.displayNodes(model, True)
			plotFrame.displayNodeLabels(model, True)
			plotFrame.displayRestraints(model, True)

			self.displayNodeLabels_Var.set('1')
			self.displayNodeLabels['state'] = 'enabled'

			self.displayRestraints_Var.set('1')
			self.displayRestraints['state'] = 'enabled'

	def showNodeLabels(self, model, plotFrame):
		if self.displayNodeLabelsFlag:
			self.displayNodeLabelsFlag = False
			plotFrame.displayNodeLabels(model, False)
		else:
			self.displayNodeLabelsFlag = True
			plotFrame.displayNodeLabels(model, True)

	def showRestraints(self, model, plotFrame):
		if self.displayRestraintsFlag:
			self.displayRestraintsFlag = False
			plotFrame.displayRestraints(model, False)
		else:
			self.displayRestraintsFlag = True
			plotFrame.displayRestraints(model, True)

class memberFrame(ttk.Frame):
	def __init__(self, parent, model, plotFrame, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)
		self.parent = parent

		buttonWidth = 30

		self.displayMbrsFlag = True		
		self.displayMbrLabelsFlag = True
		self.displayMbrPinsFlag = True

		plotFrame.displayMbrs(model, True)
		plotFrame.displayMbrLabels(model, True)
		plotFrame.displayMbrPins(model, True)

		
		self.displayMembers_Var = tk.StringVar()
		self.displayMembers_Var.set('1')

		self.displayMembers = ttk.Checkbutton(
			self,
			text = 'Display Members',
			variable = self.displayMembers_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: self.showMembers(model, plotFrame)
		)

		self.displayMemberLabels_Var = tk.StringVar()
		self.displayMemberLabels_Var.set('1')

		self.displayMemberLabels = ttk.Checkbutton(
			self,
			text = 'Display Member Labels',
			variable = self.displayMemberLabels_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: self.showMbrLabels(model, plotFrame),
			width = buttonWidth
		)

		self.displayMemberPins_Var = tk.StringVar()
		self.displayMemberPins_Var.set('1')
		
		self.displayMemberPins = ttk.Checkbutton(
			self,
			text = 'Display Member Pins',
			variable = self.displayMemberPins_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: self.showMbrPins(model, plotFrame),
			width = buttonWidth
		)	

		self.memberLabel = ttk.Label(
			self,
			text = 'Members',
			anchor = 'center',
			font = 10
		) 

		self.displayMembers.grid(column=0, row=0, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.displayMemberLabels.grid(column=0, row=1, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.displayMemberPins.grid(column=0, row=2, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.memberLabel.grid(column=0, row=3, sticky=['S','E','W'], padx=[5,5], pady=[5,5])

	def showMembers(self, model, plotFrame):
		if self.displayMbrsFlag:
			self.displayMbrsFlag = False
			self.displayMbrLabelsFlag = False
			self.displayMbrPinsFlag = False

			plotFrame.displayMbrs(model, False)

			if self.displayMemberLabels_Var.get() == '1':
				self.displayMemberLabels_Var.set('0')
				plotFrame.displayMbrLabels(model, False)
			
			if self.displayMemberPins_Var.get() == '1':
				self.displayMemberPins_Var.set('0')
				plotFrame.displayMbrPins(model, False)

			self.displayMemberLabels['state'] = 'disabled'
			self.displayMemberPins['state'] = 'disabled'

		else:
			self.displayMbrsFlag = True
			self.displayMbrLabelsFlag = True
			self.displayMbrPinsFlag = True

			plotFrame.displayMbrs(model, True)
			plotFrame.displayMbrLabels(model, True)
			plotFrame.displayMbrPins(model, True)

			self.displayMemberLabels_Var.set('1')
			self.displayMemberLabels['state'] = 'enabled'

			self.displayMemberPins_Var.set('1')
			self.displayMemberPins['state'] = 'enabled'

	def showMbrLabels(self, model, plotFrame):
		if self.displayMbrLabelsFlag:
			self.displayMbrLabelsFlag = False
			plotFrame.displayMbrLabels(model, False)
		else:
			self.displayMbrLabelsFlag = True
			plotFrame.displayMbrLabels(model, True)

	def showMbrPins(self, model, plotFrame):
		if self.displayMbrPinsFlag:
			self.displayMbrPinsFlag = False
			plotFrame.displayMbrPins(model, False)
		else:
			self.displayMbrPinsFlag = True
			plotFrame.displayMbrPins(model, True)


class CustomToolbar(NavigationToolbar2Tk):
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