
import sys
sys.path.append('..')
import os

from ..fem.Model import Model

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

class Table(ttk.Treeview):
	def __init__(self, parent, femModel):
		ttk.Treeview.__init__(self, parent)

		self.parent = parent
		self.femModel = femModel
		self.nodes = []

		# turn off the tree column (default is tree headings)
		self['show'] = 'headings'

		# set the number of rows to display to 15
		self['height'] = 15

		# define the columns
		self['columns'] = ('node','Fx','Mx','Ux','φx','Fy','My','Uy','φy','Fz','Mz','Uz','φz')

		# define the column headings
		self.heading('node',text='Node ID')
		self.heading('Fx',text='Fx [kips]')
		self.heading('Mx',text='Mx [kip-ft]')
		self.heading('Ux',text='X Disp. [in]')
		self.heading('φx',text='X Rot. [rad]')
		self.heading('Fy',text='Fy [kips]')
		self.heading('My',text='My [kip-ft]')
		self.heading('Uy',text='Y Disp. [in]')
		self.heading('φy',text='Y Rot. [rad]')
		self.heading('Fz',text='Fz [kips]')
		self.heading('Mz',text='Mz [kip-ft]')
		self.heading('Uz',text='Z Disp. [in]')
		self.heading('φz',text='Z Rot. [rad]')

		# center the columns and set the width
		minwidth=50
		width=100
		self.column('node', anchor='center', minwidth=minwidth, width=width)
		self.column('Fx', anchor='center', minwidth=minwidth, width=width)
		self.column('Mx', anchor='center', minwidth=minwidth, width=width)
		self.column('Ux', anchor='center', minwidth=minwidth, width=width)
		self.column('φx', anchor='center', minwidth=minwidth, width=width)
		self.column('Fy', anchor='center', minwidth=minwidth, width=width)
		self.column('My', anchor='center', minwidth=minwidth, width=width)
		self.column('Uy', anchor='center', minwidth=minwidth, width=width)
		self.column('φy', anchor='center', minwidth=minwidth, width=width)
		self.column('Fz', anchor='center', minwidth=minwidth, width=width)
		self.column('Mz', anchor='center', minwidth=minwidth, width=width)
		self.column('Uz', anchor='center', minwidth=minwidth, width=width)
		self.column('φz', anchor='center', minwidth=minwidth, width=width)

		# fill in coordinate values
		i = 0
		for node in femModel.nodes.nodes.values():
			if node.meshNode == False:
				i+=1
				ia = node.nodeID*6-6
				label = 'N{_ID}'.format(_ID=node.nodeID)
				Fx = round(node.Rx,2)
				Mx = round(node.Rmx,2)
				Ux = round((femModel.solver.UG[ia,0])*12,2)
				φx = f'{femModel.solver.UG[ia+3,0]:.2E}'
				Fy = round(node.Ry,2)
				My = round(node.Rmy,2)
				Uy = round((femModel.solver.UG[ia+1,0])*12,2)
				φy = f'{femModel.solver.UG[ia+4,0]:.2E}'
				Fz = round(node.Rz,2)
				Mz = round(node.Rmx,2)
				Uz = round((femModel.solver.UG[ia+2,0])*12,2)
				φz = f'{femModel.solver.UG[ia+5,0]:.2E}'
				values = (label,Fx,Mx,Ux,φx,Fy,My,Uy,φy,Fz,Mz,Uz,φz)
				self.insert('','end',i,values=values)
				self.nodes.append(node)
			
			else:
				continue

		# set the table entry to the first node
		try:
			child_id = self.get_children()[0]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass


class nodeOutputWindow(ttk.Frame):
	def __init__(self, parent, femModel):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.femModel = femModel

		# Set the title for the Node Input Window
		self.parent.title('Nodal Reactions and Displacements')

		# Set the default geometry for the Node Input Window
		self.parent.geometry('1335x380')

		# Disable User Adjustment
		self.parent.resizable(width=False, height=False)

		# Automatically Set the Node Input Window to Active State
		self.parent.focus_force()

		# Allow One Instance of the Node Input Window
		self.parent.grab_set()

		# Define the Coordinates Table
		self.table = Table(self.parent, self.femModel)
		
		# Display the Coordinates Table
		self.table.grid(
			column = 0,
			columnspan=8,
			row = 0,
			rowspan = 2,
			sticky = ['N','W'],
			padx = [15,0],
			pady = [10,10]
		)

		# Add OK Button
		self.OK = ttk.Button(
			self.parent,
			text = 'OK',
			command = self.close
			)

		# Bind Escape Key to OK Button
		self.parent.bind('<Key-Escape>', lambda e: self.OK.invoke())

		# Bind the user table selection to the updateSelection method
		self.table.bind(
			'<<TreeviewSelect>>',
			lambda e: self.updateSelection()
		)

		# Display OK Button
		self.OK.grid(
			column = 7,
			row = 2,
			sticky = ['n','s','e','w'],
			padx = [0,0]
			)

		# Display Coordinates Label Frame
		"""
		self.coordinatesFrame = coordinatesFrame(self.parent,text='Nodal Coordinates')
		self.reactionsFrame = reactionsFrame(self.parent,text='Nodal Reactions')
		self.displacementsFrame = displacementsFrame(self.parent,text='Nodal Displacements')

		self.coordinatesFrame.grid(column=0,row=10)
		self.reactionsFrame.grid(column=1,row=10)
		self.displacementsFrame.grid(column=,row=10)
		"""

	def updateSelection(self):
		try:
			int(self.table.focus())
		except ValueError:
			return

		node = self.table.nodes[int(self.table.focus())-1]

		"""
		self.coordinatesFrame.update(node)
		self.reactionsFrame.update(node)
		self.displacementsFrame.update(node, self.femModel)
		"""

	def close(self):
		self.parent.destroy()

class coordinatesFrame(ttk.Labelframe):
	def __init__(self, parent, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.xLabel = tk.StringVar()
		self.yLabel = tk.StringVar()
		self.zLabel = tk.StringVar()

		self.xCoord_Label = ttk.Label(self, textvariable=self.xLabel)
		self.yCoord_Label = ttk.Label(self, textvariable=self.yLabel)
		self.zCoord_Label = ttk.Label(self, textvariable=self.zLabel)

		self.xCoord_Label.grid()
		self.yCoord_Label.grid()
		self.zCoord_Label.grid()

	def update(self, node):
		self.xLabel.set('X Coordinate: {x} ft'.format(x=node.coordinates.x))
		self.yLabel.set('Y Coordinate: {y} ft'.format(y=node.coordinates.y))
		self.zLabel.set('Z Coordinate: {z} ft'.format(z=node.coordinates.z))

class reactionsFrame(ttk.Labelframe):
	def __init__(self, parent, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, *args, **kwargs)

		self.parent = parent
		
		self.FxVar = tk.StringVar()
		self.FyVar = tk.StringVar()
		self.FzVar = tk.StringVar()
		self.MxVar = tk.StringVar()
		self.MyVar = tk.StringVar()
		self.MzVar = tk.StringVar()

		self.Fx_Label = ttk.Label(self, textvariable= self.FxVar)
		self.Fy_Label = ttk.Label(self, textvariable= self.FyVar)
		self.Fz_Label = ttk.Label(self, textvariable= self.FzVar)
		self.Mx_Label = ttk.Label(self, textvariable= self.MxVar)
		self.My_Label = ttk.Label(self, textvariable= self.MyVar)
		self.Mz_Label = ttk.Label(self, textvariable= self.MzVar)

		self.Fx_Label.grid()
		self.Fy_Label.grid()
		self.Fz_Label.grid()
		self.Mx_Label.grid()
		self.My_Label.grid()
		self.Mz_Label.grid()

	def update(self, node):
		self.FxVar.set('Fx = {Fx} kips'.format(Fx=round(node.Rx,3)))
		self.FyVar.set('Fy = {Fy} kips'.format(Fy=round(node.Ry,3)))
		self.FzVar.set('Fz = {Fz} kips'.format(Fz=round(node.Rz,3)))
		self.MxVar.set('Mx = {Mx} kips'.format(Mx=round(node.Rmx,3)))
		self.MyVar.set('My = {My} kips'.format(My=round(node.Rmy,3)))
		self.MzVar.set('Mz = {Mz} kips'.format(Mz=round(node.Rmz,3)))

class displacementsFrame(ttk.Labelframe):
	def __init__(self, parent, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.UxVar = tk.StringVar()
		self.UyVar = tk.StringVar()
		self.UzVar = tk.StringVar()
		self.φxVar = tk.StringVar()
		self.φyVar = tk.StringVar()
		self.φzVar = tk.StringVar()

		self.Ux_Label = ttk.Label(self, textvariable= self.UxVar)
		self.Uy_Label = ttk.Label(self, textvariable= self.UyVar)
		self.Uz_Label = ttk.Label(self, textvariable= self.UzVar)
		self.φx_Label = ttk.Label(self, textvariable= self.φxVar)
		self.φy_Label = ttk.Label(self, textvariable= self.φyVar)
		self.φz_Label = ttk.Label(self, textvariable= self.φzVar)

		self.Ux_Label.grid()
		self.Uy_Label.grid()
		self.Uz_Label.grid()
		self.φx_Label.grid()
		self.φy_Label.grid()
		self.φz_Label.grid()

	def update(self, node, femModel):
		ia = node.nodeID*6-6
		Ux = round((femModel.solver.UG[ia,0])*12,2)
		φx = f'{femModel.solver.UG[ia+3,0]:.2E}'
		Uy = round((femModel.solver.UG[ia+1,0])*12,2)
		φy = f'{femModel.solver.UG[ia+4,0]:.2E}'
		Uz = round((femModel.solver.UG[ia+2,0])*12,2)
		φz = f'{femModel.solver.UG[ia+5,0]:.2E}'

		self.UxVar.set('Ux = {Ux} in'.format(Ux=Ux))
		self.UyVar.set('Uy = {Uy} in'.format(Uy=Uy))
		self.UzVar.set('Uz = {Uz} in'.format(Uz=Uz))
		self.φxVar.set('φx = {φx} in'.format(φx=φx))
		self.φyVar.set('φy = {φy} in'.format(φy=φy))
		self.φzVar.set('φz = {φz} in'.format(φz=φy))
