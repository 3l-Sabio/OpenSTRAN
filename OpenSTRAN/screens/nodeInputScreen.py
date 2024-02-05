"""
https://stackoverflow.com/questions/18985260/gui-to-input-and-output-matrices
"""

import sys
import os

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

class Table(ttk.Treeview):
	def __init__(self, parent, model):
		ttk.Treeview.__init__(self, parent)

		self.parent = parent
		self.model = model

		#instantiate variable to track of the number of table entries
		self.i = 0 

		# turn off the tree column (default is tree headings)
		self['show'] = 'headings'

		# set the number of rows to display to 10
		self['height'] = 18

		# define the columns
		self['columns'] = ('node','x','y','z')

		# define the column headings
		self.heading('node',text='Node ID')
		self.heading('x',text='X  Coordinate')
		self.heading('y',text='Y Coordinate')
		self.heading('z',text='Z Coordinate')

		# center the columns and set the width
		self.column('node', anchor='center', minwidth=100, width=150)
		self.column('x', anchor='center', minwidth=100, width=150)
		self.column('y', anchor='center', minwidth=100, width=150)
		self.column('z', anchor='center', minwidth=100, width=150)

		# fill in coordinate values
		for node in model.nodes.nodes.values():
			
			self.i = self.i+1
			
			label = node.label
			x = node.x
			y = node.y
			z = node.z
			values = (label, x, y, z)

			self.insert('','end',self.i,values=values)

		# set the table entry to the last node
		try:
			child_id = self.get_children()[-1]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass

		self.i = self.model.nodes.count

	def addNode(self):
		# update the number of table entires
		self.i = self.i+1

		# auto populate a node label based on the number of table entries
		label = 'N{i}'.format(i=self.i)

		# set the default coordinates to 0.0
		x = 0.0
		y = 0.0
		z = 0.0
		values = (label, x, y, z)

		# add the node to the table
		self.insert('','end',self.i,values=values)

		# add the node to the model
		self.model.nodes.addNode(x, y, z, label)

	def deleteNode(self):
		self.delete(self.selection()[0])

class nodeInputWindow(ttk.Frame):
	def __init__(self, parent, model, plotter):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.model = model
		self.plotter = plotter

		# Set the title for the Node Input Window
		self.parent.title('Node Definition')

		# Set the default geometry for the Node Input Window
		self.parent.geometry('895x430')

		# Disable User Adjustment
		self.parent.resizable(width=False, height=False)

		# Automatically Set the Node Input Window to Active State
		self.parent.focus_force()

		# Allow One Instance of the Node Input Window
		self.parent.grab_set()

		# Define the Coordinates Table
		self.table = Table(self.parent, self.model)
		
		# Display the Coordinates Table
		self.table.grid(
			column = 0,
			columnspan=3,
			row = 0,
			rowspan = 2,
			sticky = ['N','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Add Add Node, Delete Node, and OK Buttons
		self.AddNode = ttk.Button(
			self.parent,
			text = 'Add Node',
			command = self.addNode,
			default = 'active'
			)

		self.DeleteNode = ttk.Button(
			self.parent,
			text = 'Delete Node',
			command = self.deleteNode
			)

		self.OK = ttk.Button(
			self.parent,
			text = 'OK',
			command = self.close
			)

		# Bind Enter and Delete Keys to Add Node and Delete Node Buttons
		self.parent.bind('<Key-Return>', lambda e: self.AddNode.invoke())
		self.parent.bind('<Key-Delete>', lambda e: self.DeleteNode.invoke())

		# Bind Escape Key to OK Button
		self.parent.bind('<Key-Escape>', lambda e: self.OK.invoke())


		# Bind the user table selection to the updateSelection method
		self.table.bind(
			'<<TreeviewSelect>>',
			lambda e: self.updateSelection()
		)

		# Display OK, Add & Delete Node Buttons
		self.AddNode.grid(
			column = 0,
			row = 2,
			sticky = ['n','s','e','w'],
			padx = [15,5]
			)

		self.DeleteNode.grid(
			column = 1,
			row = 2,
			sticky = ['n','s','e','w'],
			padx = [15,5]
			)

		self.OK.grid(
			column = 2,
			row = 2,
			sticky = ['n','s','e','w'],
			padx = [15,5]
			)

		###############################################################	
		### --------------------- COORDINATES --------------------- ###
		###############################################################


		# Define Node Properties Label Frame
		nodeFrame = ttk.Labelframe(self.parent, text='Node Properties')

		# Display the Node Properties Label Frame
		nodeFrame.grid(
			column = 4,
			row = 0,
			sticky = ['N','E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Register a command to use for node input validation
		vcmd = (self.register(self.validateNode), '%P')

		### ----------------------- NODE ID ----------------------- ###

		# Define the Node ID Variable
		self.nodeID_Var = tk.StringVar()

		# Watch for changes to the Node ID Variable
		self.nodeID_Trace = self.nodeID_Var.trace_add('write',self.updateNode)

		# Define the Node ID Label
		self.nodeID_Label = ttk.Label(
			nodeFrame,
			text = 'Node ID:'
		)

		# Display the Node ID Label
		self.nodeID_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Node ID Label Entry Box
		self.nodeID_Entry = ttk.Entry(
			nodeFrame,
			textvariable = self.nodeID_Var,
			state = 'disabled'
		)

		# Display the Node ID Label Entry Box
		self.nodeID_Entry.grid(
			column = 1,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)
		
		### --------------------- X Coordinate --------------------- ###

		# Define the X Coordinate Variable
		self.xCoord_Var = tk.StringVar()

		# Watch for changes to the X Coordinate Variable
		self.xCoord_Trace = self.xCoord_Var.trace_add('write',self.updateNode)

		# Define the X Coordinate Label
		self.xCoord_Label = ttk.Label(
			nodeFrame,
			text = 'X Coordinate:'
		)

		# Display the X Coordinate Label
		self.xCoord_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the X Coordinate Label Entry Box
		self.xCoord_Entry = ttk.Entry(
			nodeFrame,
			textvariable = self.xCoord_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the X Coordinate Label Entry Box
		self.xCoord_Entry.grid(
			column = 1,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### --------------------- Y Coordinate --------------------- ###

		# Define the Y Coordinate Variable
		self.yCoord_Var = tk.StringVar()

		# Watch for changes to the Y Coordinate Variable
		self.yCoord_Trace = self.yCoord_Var.trace_add('write',self.updateNode)

		# Define the Y Coordinate Label
		self.yCoord_Label = ttk.Label(
			nodeFrame,
			text = 'Y Coordinate:'
		)

		# Display the Y Coordinate Label
		self.yCoord_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Y Coordinate Label Entry Box
		self.yCoord_Entry = ttk.Entry(
			nodeFrame,
			textvariable = self.yCoord_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Y Coordinate Label Entry Box
		self.yCoord_Entry.grid(
			column = 1,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### --------------------- Z Coordinate --------------------- ###

		# Define the Z Coordinate Variable
		self.zCoord_Var = tk.StringVar()

		# Watch for changes to the Z Coordinate Variable
		self.zCoord_Trace = self.zCoord_Var.trace_add('write',self.updateNode)

		# Define the Z Coordinate Label
		self.zCoord_Label = ttk.Label(
			nodeFrame,
			text = 'Z Coordinate:'
		)

		# Display the Z Coordinate Label
		self.zCoord_Label.grid(
			column = 0,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Z Coordinate Label Entry Box
		self.zCoord_Entry = ttk.Entry(
			nodeFrame,
			textvariable = self.zCoord_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Z Coordinate Label Entry Box
		self.zCoord_Entry.grid(
			column = 1,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)



		################################################################
		### ---------------------- RESTRAINTS ---------------------- ###
		################################################################

		# Define Node Properties Label Frame
		restraintFrame = ttk.Labelframe(self.parent, text='Boundary Conditions')

		# Display the Node Properties Label Frame
		restraintFrame.grid(
			column = 4,
			row = 1,
			sticky = ['N','E'],
			padx = [15,0],
			pady = [10,0]
		)
	
		### -------------------- RESTRAINT TYPE -------------------- ###
		
		# Define the Nodal Restraint Type Variable
		self.Restraint_Var = tk.StringVar()

		# Define the Nodal Restraint Type Combobox
		self.Restraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.Restraint_Var,
			values = ('Fixed','Free','Pinned','Roller'),
			state = 'readonly'
		)

		# Display the Nodal Restraint Combobox
		self.Restraint.grid(
			column = 0,
			row = 0,
			columnspan = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Bind the Nodal Restraint Combobox to the updateRestraints Method

		self.Restraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraints()
		)

		### -------------------- X Translation -------------------- ###


		# Define the X Tranaslation DOF Restraint Variable
		self.UxRestraint_Var = tk.StringVar()

		# Define the X Translation DOF Restraint Label
		self.UxRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'X Translation:'
		)

		# Display the X Translation DOF Restraint Label
		self.UxRestraint_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the X Translation DOF Combobox
		self.UxRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.UxRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the X Translation DOF Combobox to the updateRestraints Method
		self.UxRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the X Translation DOF Combobox
		self.UxRestraint.grid(
			column = 1,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

		### -------------------- Y Translation -------------------- ###


		# Define the Y Tranaslation DOF Restraint Variable
		self.UyRestraint_Var = tk.StringVar()

		# Define the Y Translation DOF Restraint Label
		self.UyRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'Y Translation:'
		)

		# Display the Y Translation DOF Restraint Label
		self.UyRestraint_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the Y Translation DOF Combobox
		self.UyRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.UyRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the Y Translation DOF Combobox to the updateRestraints Method
		self.UyRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the Y Translation DOF Combobox
		self.UyRestraint.grid(
			column = 1,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

		### -------------------- Z Translation -------------------- ###


		# Define the Z Tranaslation DOF Restraint Variable
		self.UzRestraint_Var = tk.StringVar()

		# Define the Z Translation DOF Restraint Label
		self.UzRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'Z Translation:'
		)

		# Display the Z Translation DOF Restraint Label
		self.UzRestraint_Label.grid(
			column = 0,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the Z Translation DOF Combobox
		self.UzRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.UzRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the Z Translation DOF Combobox to the updateRestraint Method
		self.UzRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the Z Translation DOF Combobox
		self.UzRestraint.grid(
			column = 1,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

		### --------------------- X Rotations --------------------- ###

		# Define the X Rotation DOF Restraint Variable
		self.φxRestraint_Var = tk.StringVar()

		# Define the X Rotation DOF Restraint Label
		self.φxRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'X Rotation:'
		)

		# Display the X Rotation DOF Restraint Label
		self.φxRestraint_Label.grid(
			column = 0,
			row = 4,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the X Rotation DOF Combobox
		self.φxRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.φxRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the X Rotation DOF Combobox to the updateRestraint Method
		self.φxRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the X Rotation DOF Combobox
		self.φxRestraint.grid(
			column = 1,
			row = 4,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

		### --------------------- Y Rotations --------------------- ###

		# Define the Y Rotation DOF Restraint Variable
		self.φyRestraint_Var = tk.StringVar()

		# Define the Y Rotation DOF Restraint Label
		self.φyRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'Y Rotation:'
		)

		# Display the Y Rotation DOF Restraint Label
		self.φyRestraint_Label.grid(
			column = 0,
			row = 5,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the Y Rotation DOF Combobox
		self.φyRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.φyRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the Υ Rotation DOF Combobox to the updateRestraint Method
		self.φyRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the Y Rotation DOF Combobox
		self.φyRestraint.grid(
			column = 1,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

		### --------------------- Z Rotations --------------------- ###

		# Define the Z Rotation DOF Restraint Variable
		self.φzRestraint_Var = tk.StringVar()

		# Define the Z Rotation DOF Restraint Label
		self.φzRestraint_Label = ttk.Label(
			restraintFrame,
			text = 'Z Rotation:'
		)

		# Display the Z Rotation DOF Restraint Label
		self.φzRestraint_Label.grid(
			column = 0,
			row = 6,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)		

		# Define the Z Rotation DOF Combobox
		self.φzRestraint = ttk.Combobox(
			restraintFrame,
			textvariable = self.φzRestraint_Var,
			values = ('Free','Restrained'),
			state = 'readonly',
			width = 18
		)

		# Bind the Z Rotation DOF Combobox to the updateRestraints Method
		self.φzRestraint.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateRestraint()
		)

		# Display the Z Rotation DOF Combobox
		self.φzRestraint.grid(
			column = 1,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0],
		)

	def returnNode(self):
		index = int(self.table.focus())
		node_id = int(self.table.item(index)['values'][0][1:])
		node = self.model.nodes.nodes[node_id]
		return(index, node)

	def addNode(self):
		# add a node to the table
		self.table.addNode()

		# set the table entry to the added node
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass

		# identify the added node
		index, node = self.returnNode()

		# plot the added node
		self.plotter.addNode(node)

		# plot the added node label
		self.plotter.addNodeLabel(node)

	def updateNode(self, *args):
		# instantiate an empty array for later use
		coordinates = []

		# collect the user defined nodal coordinates (UDNC)
		coordinates.append(self.xCoord_Var.get())
		coordinates.append(self.yCoord_Var.get())
		coordinates.append(self.zCoord_Var.get())

		# convert the UDNC to floating point values
		for i, coordinate in enumerate(coordinates):
			if coordinate == '':
				coordinates[i] = 0.0
			else:
				coordinates[i] = float(coordinate)

		# collect the user defined node name
		coordinates.append(self.nodeID_Var.get())

		# store the user selected node as a variable
		index, node = self.returnNode()

		# update the nodal coordinates
		node.update(coordinates[0], coordinates[1], coordinates[2])

		# update the table
		self.table.item(
			index,
			values=(
				coordinates[3],
				coordinates[0],
				coordinates[1],
				coordinates[2]
			)
		)
		
		# replot the node
		self.plotter.updateNode(node)

		# replot the node label
		self.plotter.updateNodeLabel(node)

		# replot the nodal restraint
		self.plotter.updateRestraint(node)

		### UPDATE THIS FUNCTION WHEN POSSIBLE ###
		#self.plotter.updateMembers(self.model)

	def deleteNode(self):
		# store the user selected node as a variable
		index, node = self.returnNode()

		# remove the node from the model
		self.model.nodes.removeNode(node)

		# remove the node from the table
		self.table.deleteNode()

		# remove the node from the plot
		self.plotter.removeNode(node)

		# remove the node label from the plot
		self.plotter.removeNodeLabel(node)

		# remove the nodal restraint from the plot
		try:
			self.plotter.removeRestraint(node)
		except KeyError:
			pass

		# set the table entry to the last node
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass

	def updateSelection(self):
		try:
			int(self.table.focus())
		
		except ValueError:
			return

		# temporarily remove object traces
		# not doing this unnecessarily calls multiple updateNode executions
		self.nodeID_Var.trace_remove('write',self.nodeID_Trace)
		self.xCoord_Var.trace_remove('write',self.xCoord_Trace)
		self.yCoord_Var.trace_remove('write',self.yCoord_Trace)
		self.zCoord_Var.trace_remove('write',self.zCoord_Trace)

		# store the user selected node as a variable
		index = self.table.focus()
		node = self.table.item(index)

		# collect the relevant node properties
		index, node = self.returnNode()
		label = node.label
		x = node.x
		y = node.y
		z = node.z

		# Update Values
		self.nodeID_Var.set(label)

		# Update Coordinates
		self.xCoord_Var.set(x)
		self.yCoord_Var.set(y)
		self.zCoord_Var.set(z)

		# add object traces
		self.nodeID_Trace = self.nodeID_Var.trace_add('write',self.updateNode)
		self.xCoord_Trace = self.xCoord_Var.trace_add('write',self.updateNode)
		self.yCoord_Trace = self.yCoord_Var.trace_add('write',self.updateNode)
		self.zCoord_Trace = self.zCoord_Var.trace_add('write',self.updateNode)

		# Update Nodal Boundary Conditions		
		if node.restraint[0] == 0:
			self.UxRestraint_Var.set('Free')
		else:
			self.UxRestraint_Var.set('Restrained')

		if node.restraint[1] == 0:
			self.UyRestraint_Var.set('Free')
		else:
			self.UyRestraint_Var.set('Restrained')

		if node.restraint[2] == 0:
			self.UzRestraint_Var.set('Free')
		else:
			self.UzRestraint_Var.set('Restrained')

		if node.restraint[3] == 0:
			self.φxRestraint_Var.set('Free')
		else:
			self.φxRestraint_Var.set('Restrained')

		if node.restraint[4] == 0:
			self.φyRestraint_Var.set('Free')
		else:
			self.φyRestraint_Var.set('Restrained')

		if node.restraint[5] == 0:
			self.φzRestraint_Var.set('Free')
		else:
			self.φzRestraint_Var.set('Restrained')

		# Update Boundry Condition Identifier
		if node.restraint == [0,0,0,0,0,0]:
			self.Restraint_Var.set('Free')

		elif node.restraint == [1,1,1,0,0,0]:
			self.Restraint_Var.set('Pinned')

		elif node.restraint == [1,1,1,1,1,1]:
			self.Restraint_Var.set('Fixed')

		elif node.restraint == [0,1,1,0,0,0]:
			self.Restraint_Var.set('Roller')

		else:
			self.Restraint_Var.set('Custom')

	def updateRestraint(self):
		# define a list to hold the user defined restraints
		restraints = []

		# collect the user defined restraints
		restraints.append(self.UxRestraint_Var.get())
		restraints.append(self.UyRestraint_Var.get())
		restraints.append(self.UzRestraint_Var.get())
		restraints.append(self.φxRestraint_Var.get())
		restraints.append(self.φyRestraint_Var.get())
		restraints.append(self.φzRestraint_Var.get())

		# redefine the restraints as a boolean value
		for i, restraint in enumerate(restraints):
			if restraint == 'Free':
				restraints[i] = 0 # free
			else:
				restraints[i] = 1 # restrained

		# store the user selected node as a variable
		index, node = self.returnNode()

		# update the nodal restraints
		node.restraint = restraints

		# plot the restraint
		self.plotter.updateRestraint(node)

		self.updateSelection()

	def updateRestraints(self):
		restraint = (self.Restraint_Var.get())

		if restraint == 'Free':
			self.UxRestraint_Var.set('Free')
			self.UyRestraint_Var.set('Free')
			self.UzRestraint_Var.set('Free')
			self.φxRestraint_Var.set('Free')
			self.φyRestraint_Var.set('Free')
			self.φzRestraint_Var.set('Free')

		elif restraint == 'Pinned':
			self.UxRestraint_Var.set('Restrained')
			self.UyRestraint_Var.set('Restrained')
			self.UzRestraint_Var.set('Restrained')
			self.φxRestraint_Var.set('Free')
			self.φyRestraint_Var.set('Free')
			self.φzRestraint_Var.set('Free')

		elif restraint == 'Fixed':
			self.UxRestraint_Var.set('Restrained')
			self.UyRestraint_Var.set('Restrained')
			self.UzRestraint_Var.set('Restrained')
			self.φxRestraint_Var.set('Restrained')
			self.φyRestraint_Var.set('Restrained')
			self.φzRestraint_Var.set('Restrained')		

		elif restraint == 'Roller':
			self.UxRestraint_Var.set('Free')
			self.UyRestraint_Var.set('Restrained')
			self.UzRestraint_Var.set('Restrained')
			self.φxRestraint_Var.set('Free')
			self.φyRestraint_Var.set('Free')
			self.φzRestraint_Var.set('Free')

		self.updateRestraint()
	
	def validateNode(self, P):
		'''
		allow only an empty value, or a value that can be converted to a float
		'''

		if P.strip() == '':
			return True

		try:
			f = float(P)
		except ValueError:
			self.bell()
			return False
		
		return True

	def close(self):
		self.parent.destroy()

if __name__ == '__main__':
	tableScreen = tk.Tk()

	sub = tk.Toplevel()

	nodeInputWindow(sub).grid()

	tableScreen.mainloop()