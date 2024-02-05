import sys
import os

# import third party packages
import matplotlib
import numpy as np

from matplotlib import collections

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

# configure Matplotlib for backend use
matplotlib.use('TkAgg')

# enable line segment simplification to reduce rendering time
#https://matplotlib.org/stable/users/explain/performance.html
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0
matplotlib.style.use('fast')

# Matplotlib backend imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure

class Table(ttk.Treeview):
	def __init__(self, parent, femModel):
		ttk.Treeview.__init__(self, parent)

		self.parent = parent
		self.femModel = femModel
		self.members = []

		# turn off the tree column (default is tree headings)
		self['show'] = 'headings'

		# set the number of rows to display to 10
		self['height'] = 10

		# define the columns
		self['columns'] = (
			'member',
			'node_i',
			'i_release',
			'node_j',
			'j_release',
			'shape',
			'E',
			'Ixx',
			'Iyy',
			'A',
			'G',
			'J',
			'mesh',
			'bracing'
		)

		# define the column headings
		self.heading('member',text='Member')
		self.heading('node_i',text='i Node')
		self.heading('i_release',text='i Release')
		self.heading('node_j',text='j Node')
		self.heading('j_release',text='j Release')
		self.heading('shape',text='shape')
		self.heading('E',text='E (ksi)')
		self.heading('Ixx',text='Ixx (in^4)')
		self.heading('Iyy',text='Iyy (in^4)')
		self.heading('A',text='A (in^2)')
		self.heading('G',text='G (ksi)')
		self.heading('J',text='J (in^4)')
		self.heading('mesh',text='mesh')
		self.heading('bracing',text='bracing')

		# center the columns and set the width
		self.column('member', anchor='center', minwidth=50, width=75)
		self.column('node_i', anchor='center', minwidth=50, width=75)
		self.column('i_release', anchor='center', minwidth=50, width=75)
		self.column('node_j', anchor='center', minwidth=50, width=75)
		self.column('j_release', anchor='center', minwidth=50, width=75)
		self.column('shape', anchor='center', minwidth=50, width=75)
		self.column('E', anchor='center', minwidth=50, width=75)
		self.column('Ixx', anchor='center', minwidth=50, width=75)
		self.column('Iyy', anchor='center', minwidth=50, width=75)
		self.column('A', anchor='center', minwidth=50, width=75)
		self.column('G', anchor='center', minwidth=50, width=75)
		self.column('J', anchor='center', minwidth=50, width=75)
		self.column('mesh', anchor='center', minwidth=50, width=75)
		self.column('bracing', anchor='center', minwidth=50, width=75)

		# fill in coordinate values
		i = 0
		for n, mbr in femModel.members.members.items():
			i+=1
			member = 'M{i}'.format(i=n)
			node_i = 'N{i}'.format(i=mbr.node_i.nodeID)
			i_release = mbr.i_release
			node_j = 'N{i}'.format(i=mbr.node_j.nodeID)
			j_release = mbr.j_release
			shape = mbr.shape
			E = mbr.E
			Ixx = mbr.Izz
			Iyy = mbr.Iyy
			A = mbr.A
			G = mbr.G
			J = mbr.J
			mesh = mbr.mesh
			bracing = mbr.bracing

			values = (member,
				node_i,
				i_release,
				node_j,
				j_release,
				shape,
				E,
				Ixx,
				Iyy,
				A,
				G,
				J,
				mesh,
				bracing
			)

			self.insert('','end',i,values=values)
			self.members.append(mbr)

		# set the table entry to the first member
		try:
			child_id = self.get_children()[0]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass

class memberResultsWindow(ttk.Frame):
	def __init__(self, parent, femModels):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.femModels = femModels

		# Set the title for the Node Input Window
		self.parent.title('Detailed Member Results')

		# Set the default geometry for the Node Input Window
		self.parent.geometry('1085x430')

		# Disable User Adjustment
		#self.parent.resizable(width=False, height=False)

		# Automatically Set the Node Input Window to Active State
		self.parent.focus_force()

		# Allow One Instance of the Node Input Window
		self.parent.grab_set()

		# Define the load combination variable
		self.loadCombination_Var = tk.StringVar()
		self.loadCombination_Var.set('Dead Load Only (D)')

		# set the user selected FEM model
		self.femModel = self.femModels[self.loadCombination_Var.get()]

		# Define the Coordinates Table
		self.table = Table(self.parent, self.femModel)

		# Define the load combination Combobox
		self.loadCombination_Cbox = ttk.Combobox(
			self.parent,
			textvariable = self.loadCombination_Var,
			state='readonly',
			values = [
				'Dead Load Only (D)',
				'Live Load Only (L)',
				'Roof Live Load Only (Lr)',
				'Snow Load Only (S)',
				'Rain Load Only (R)',
				'Wind Load Only (W)',
				'Earthquake Load Only (E)',
				'ASD 2-4a D',
				'ASD 2-4b D + L',
				'ASD 2-4c D + (Lr or S or R)',
				'ASD 2-4d D + 0.75L + 0.75(Lr or S or R)',
				'ASD 2-4e D + 0.6W or 0.7E',
				'ASD 2-4f D + 0.75L + 0.75(0.6W) + 0.75(Lr or S or R)',
				'ASD 2-4g D + 0.75L + 0.75(0.6E) + 0.75S',
				'ASD 2-4h 0.6D + 0.6W',
				'ASD 2-4i 0.6D + 0.7E'
			]
		)

		# Bind the Load Combination Combobox to the Update Combination Method
		self.loadCombination_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateLoads(self.loadCombination_Var.get())
		)

		# Bind the user table selection to the updateSelection method
		self.table.bind(
			'<<TreeviewSelect>>',
			lambda e: self.updateSelection()
		)

		# Display the Load Combination Combobox
		self.loadCombination_Cbox.grid(
			column = 0,
			columnspan = 2,
			row = 0,
			sticky = ['E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Display the Coordinates Table
		self.table.grid(
			column = 0,
			columnspan=6,
			row = 1,
			sticky = ['N','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Display the Plot Frame
		self.plots = plotFrame(self.parent, self.femModel)
		self.plots.grid(
			column = 0,
			columnspan = 6,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

	def updateLoads(self, loadCombination):
		print(loadCombination)

	def updateSelection(self):
		try:
			int(self.table.focus())
		except ValueError:
			return

		mbr = self.table.members[int(self.table.focus())-1]

		self.plots.update(mbr)
		
class plotFrame(ttk.Frame):
	def __init__(self, parent, femModel):
		ttk.Frame.__init__(self, parent)

		self.parent = parent
		self.femModel = femModel

		# instantiate a 2D plot from the Matplotlib library
		self.fig = Figure()
		self.yShear = self.fig.add_subplot(331)
		self.zShear = self.fig.add_subplot(332)
		self.axial = self.fig.add_subplot(333)
		self.zzMoment = self.fig.add_subplot(334)
		self.yyMoment = self.fig.add_subplot(335)
		self.torque = self.fig.add_subplot(336)
		self.zzDeflection = self.fig.add_subplot(337)
		self.yyDeflection = self.fig.add_subplot(338)
		self.canvas = FigureCanvasTkAgg(self.fig, self)
		self.canvas.draw()
		self.canvas.get_tk_widget().pack(
			side = 'top',
			fill = 'both',
			expand = True
		)
		self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=True)
		self.fig.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)

		# set the titles
		self.yShear.set_title('y shear force (kips)')
		self.zShear.set_title('z shear force (kips)')
		self.axial.set_title('axial force (kips)')
		self.zzMoment.set_title('z-z moment (kip-ft)')
		self.yyMoment.set_title('y-y moment (kip-ft)')
		self.torque.set_title('torsional moment (kip-ft)')
		self.zzDeflection.set_title('z deflection (in)')
		self.yyDeflection.set_title('y deflection (in)')


	def update(self, mbr):
		self.display(self.yShear, mbr, 'shear', 'green')
		self.display(self.zShear, mbr, 'transverse shear', 'green')
		self.display(self.axial, mbr, 'axial','green')
		self.display(self.zzMoment, mbr, 'major axis moments','blue')
		self.display(self.yyMoment, mbr, 'minor axis moments','blue')
		self.display(self.torque, mbr, 'torsional moments','blue')
		self.deflection(self.zzDeflection, mbr, 'z')
		self.deflection(self.yyDeflection, mbr, 'y')

	def deflection(self, subplot, mbr, axis):
		# clear the subplot before proceeding
		subplot.cla()
		
		# member unit vector
		i = mbr.node_i.coordinates.vector
		j = mbr.node_j.coordinates.vector
		v = (j-i)/np.linalg.norm(j-i)

		# determine DOFs associated with axis
		if axis == 'y':
			a = 1
			b = 7

		elif axis == 'z':
			a = 2
			b = 8

		# instantiate an empty array to hold member deflections
		deflections = []

		# iterate through the submembers and plot the member deflections
		for n, submbr in enumerate(mbr.submembers.values()):
			# member deflections
			ui_y = submbr.results['displacements'][a]
			uj_y = submbr.results['displacements'][b]

			deflections.append(ui_y)
			deflections.append(uj_y)

			xs = n*submbr.length + np.array([0, submbr.length])
			ys = np.array([ui_y, uj_y])

			# plot the deflection diagram segment
			subplot.plot(
				xs,
				ys,
				lw=0.5,
				color='purple'
			)

			# plot the member segment
			subplot.plot(
				[0,mbr.length],
				[0,0],
				lw=2.0,
				color='grey',
				linestyle='-'
			)

		subplot.grid(visible=True)
		self.canvas.draw()

	def display(self, subplot, mbr, force, color):
		subplot.cla()
		# member unit vector
		i = mbr.node_i.coordinates.vector
		j = mbr.node_j.coordinates.vector
		v = (j-i)/np.linalg.norm(j-i)

		# instantiate an empty array to hold member forces
		forces = []

		# iterate through the submembers and plot the member forces
		for n, submbr in enumerate(mbr.submembers.values()):
			# member forces
			fi = submbr.results[force][0]
			fj = submbr.results[force][1]

			# correct the shape of the force diagram segment
			if(fi<0 and fj>0):
				fi = -abs(fi)
				fj = -abs(fj)
			elif(fi<0 and fj<0):
				fi = -abs(fi)
				fj = abs(fj)
			elif(fi>0 and fj>0):
				fi = abs(fi)
				fj = -abs(fj)
			elif(fi>0 and fj<0):
				fi = abs(fi)
				fj = abs(fj)
			elif(fi>0 and np.isclose(fj,0)):
				fi = abs(fi)
			elif(fi<0 and np.isclose(fj,0)):
				fi = -abs(fi)
			elif(np.isclose(fi,0) and fj>0):
				fj = -abs(fj)
			elif(np.isclose(fi,0) and fj<0):
				fj = abs(fj)
			if np.isclose(fi, 0):
				fi = 0
			if np.isclose(fj, 0):
				fj = 0

			forces.append(fi)
			forces.append(fj)

			pt1 = np.array([0,0])
			pt2 = np.array([0,fi])
			pt3 = np.array([submbr.length,fj])
			pt4 = np.array([submbr.length,0])

			xs = n*submbr.length + np.array([pt1[0], pt2[0], pt3[0], pt4[0]])
			ys = np.array([pt1[1], pt2[1], pt3[1], pt4[1]])

			# plot the force diagram segment
			subplot.add_collection(collections.PolyCollection(
				[list(zip(xs,ys))],
				lw=0.0,alpha=0.1,
				facecolor=color,
				rasterized=True
			))
			
			# plot the member segment
			subplot.plot(
				[0,mbr.length],
				[0,0],
				lw=2.0,
				color='grey',
				linestyle='-',
				rasterized=True
			)
		
		subplot.grid(visible=True)
		self.canvas.draw()



			


