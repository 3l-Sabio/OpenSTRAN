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
		for n, mbr in model.members.members.items():
			
			self.i = self.i+1
			
			member = 'M{i}'.format(i=n)
			node_i = mbr.node_i.label
			i_release = mbr.i_release
			node_j = mbr.node_j.label
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

			self.insert('','end',self.i,values=values)

		# set the table entry to the last member
		try:
			child_id = self.get_children()[-1]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass

		self.i = self.model.members.count

	def addMember(self, properties):
		# determine the total number of user defined nodes
		n = 0
		for node in self.model.nodes.nodes.values():
				n = n + 1

		# check to make sure at least two nodes are defined
		if n < 2:
			tk.messagebox.showinfo(
				'Not Enough Nodes Defined!',
				'At least two nodes must be defined!'
			)
			return

		# check to make sure there are enough nodes to add another member
		m = int(n*(n-1)/2)

		if len(self.get_children()) >= m:
			tk.messagebox.showinfo(
				'Not Enough Nodes Defined!',
				'There are only {n} nodes defined. A maximum of {m} members can be defined for this number of nodes. To define more members, first add more nodes to the model.'.format(n=n,m=m)
			)
			return
		
		# update the number of table entries
		self.i = self.i + 1

		# set the new member default properties to the last member 
		# defined by the user if any
		if properties == None:
			node_i = list(self.model.nodes.nodes.values())[0]
			node_j = list(self.model.nodes.nodes.values())[1]

			self.model.members.addMember(
				node_i = node_i,
				node_j = node_j
			)

		else:
			node_i = self.model.nodes.returnNode(properties[1])
			node_j = self.model.nodes.returnNode(properties[3])
			i_release = True if properties[2] == 'True' else False
			j_release = True if properties[4] == 'True' else False
			shape = properties[5]
			E = int(properties[6])
			Ixx = float(properties[7])
			Iyy = float(properties[8])
			A = float(properties[9])
			G = int(properties[10])
			J = float(properties[11])
			mesh = int(properties[12])
			bracing = properties[13]

			self.model.members.addMember(
				node_i = node_i,
				node_j = node_j,
				shape = shape,
				i_release = i_release,
				j_release = j_release,
				E = E,
				Ixx = Ixx,
				Iyy = Iyy,
				A = A,
				G = G,
				J = J,
				mesh = mesh,
				bracing = bracing
			)

		mbr = list(self.model.members.members.values())[-1]
		
		member = 'M{i}'.format(
			i=list(self.model.members.members.keys())[-1]
		)
		node_i = mbr.node_i.label
		i_release = mbr.i_release
		node_j = mbr.node_j.label
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

		values = (
			member,
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
		
		self.insert('','end',self.i,values=values)

	def deleteMember(self):
		self.delete(self.selection()[0])

class memberNodes(ttk.Labelframe):
	def __init__(self, parent, model):
		ttk.Labelframe.__init__(self, parent, text='Member Nodes')
		self.parent = parent
		self.model = model	

		### ---------------------- MEMBER ID ---------------------- ###
		
		# Define Member ID Variable
		self.memberID_Var = tk.StringVar()

		# Define Member ID Label
		self.memberID_Label = ttk.Label(
			self,
			text = 'Member ID:'
		)

		# Display the Member ID Label
		self.memberID_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Member ID Entry Box
		self.memberID_Entry = ttk.Entry(
			self,
			textvariable = self.memberID_Var,
			state = 'disabled'
		)

		# Display the Member ID Entry Box
		self.memberID_Entry.grid(
			column = 1,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### ------------------------ i NODE ------------------------ ###

		# Define the i Node Label
		self.iNode_Label = ttk.Label(
			self,
			text = 'i Node:'
		)

		# Display the i Node Label
		self.iNode_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the i Node Variable
		self.iNode_Var = tk.StringVar()

		# Define i Node Combobox
		self.iNode_Cbox = ttk.Combobox(
			self,
			textvariable = self.iNode_Var,
			values = self.get_nodes(),
			state = 'readonly'
		)

		# Display the i Node Combobox
		self.iNode_Cbox.grid(
			column = 1,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### -------------------- i NODE RELEASE -------------------- ###

		# Define the i Node Release Label
		self.iNodeRelease_Label = ttk.Label(
			self,
			text = 'i Release:'
		)

		# Display the i Node Label
		self.iNodeRelease_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the i Node Release Variable
		self.iNodeRelease_Var = tk.StringVar()

		# Define i Node Release Combobox
		self.iNodeRelease_Cbox = ttk.Combobox(
			self,
			textvariable = self.iNodeRelease_Var,
			values = ['True','False'],
			state = 'readonly'
		)

		# Display the i Node Release Combobox
		self.iNodeRelease_Cbox.grid(
			column = 1,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)

		### ------------------------ j NODE ------------------------ ###

		# Define the j Node Label
		self.jNode_Label = ttk.Label(
			self,
			text = 'j Node:'
		)

		# Display the j Node Label
		self.jNode_Label.grid(
			column = 2,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the j Node Variable
		self.jNode_Var = tk.StringVar()

		# Define j Node Combobox
		self.jNode_Cbox = ttk.Combobox(
			self,
			textvariable = self.jNode_Var,
			values = self.get_nodes(),
			state = 'readonly'
		)

		# Display the j Node Combobox
		self.jNode_Cbox.grid(
			column = 3,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### -------------------- j NODE RELEASE -------------------- ###

		# Define the j Node Release Label
		self.jNodeRelease_Label = ttk.Label(
			self,
			text = 'j Release:'
		)

		# Display the j Node Label
		self.jNodeRelease_Label.grid(
			column = 2,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the j Node Release Variable
		self.jNodeRelease_Var = tk.StringVar()

		# Define j Node Release Combobox
		self.jNodeRelease_Cbox = ttk.Combobox(
			self,
			textvariable = self.jNodeRelease_Var,
			values = ['True','False'],
			state = 'readonly'
		)

		# Display the j Node Release Combobox
		self.jNodeRelease_Cbox.grid(
			column = 3,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)


	### ---------------------- CLASS METHODS ----------------------- ###

	def get_nodes(self):
		# instantiate an array to hold the nodes
		nodes = []
		# iterate through the model nodes
		for node in self.model.nodes.nodes.values():
			nodes.append(node.label)
		# return the nodes
		return(nodes)

class memberProperties(ttk.Labelframe):
	def __init__(self, parent, model, shapeSelector, query):
		ttk.Labelframe.__init__(
			self,
			parent, 
			text = 'Member Properties'
		)

		self.parent = parent
		self.model = model
		self.shapeSelector = shapeSelector
		self.query = query

		# Register a command to use for property input validation
		vcmd = (self.register(self.validateProperty), '%P')

		### --------------------- MEMBER SHAPE --------------------- ###

		# Define Member Shape Variable
		self.memberShape_Var = tk.StringVar()

		# Define Member Shape Label
		self.memberShape_Label = ttk.Label(
			self,
			text = 'Member Shape:'
		)

		# Display the Member Shape Label
		self.memberShape_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Member Shape Entry Box
		self.memberShape_Entry = ttk.Entry(
			self,
			textvariable = self.memberShape_Var,
			state = 'disabled'
		)

		# Display the Member Shape Entry Box
		self.memberShape_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Define the Member Selection Button
		self.shapeSelection_Btn = ttk.Button(
			self,
			text = 'Select Shape',
			command = self.openWindow
		)

		# Display the Member Selection Button
		self.shapeSelection_Btn.grid(
			column = 0,
			columnspan = 3,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### ----------------- MODULUS OF ELASTICITY ---------------- ###

		# Define Member Modulus of Elasticity Variable
		self.memberE_Var = tk.StringVar()

		# Define Member Modulus of Elasticity Label
		self.memberE_Label = ttk.Label(
			self,
			text = 'Modulus of Elasticity:'
		)

		# Display the Member Modulus of Elasticity Label
		self.memberE_Label.grid(
			column = 3,
			row = 0,
			sticky = ['E'],
			padx = [75,0],
			pady = [10,0]
		)

		# Define the Member Modulus of Elasticity Entry Box
		self.memberE_Entry = ttk.Entry(
			self,
			textvariable = self.memberE_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Modulus of Elasticity Entry Box
		self.memberE_Entry.grid(
			column = 4,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Member Modulus of Elasticity Units
		ttk.Label(self, text = 'ksi').grid(
			column = 5,
			row = 0,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### --------------------- SHEAR MODULUS -------------------- ###

		# Define Member Shear Modulus Variable
		self.memberG_Var = tk.StringVar()

		# Define Member Shear Modulus Label
		self.memberG_Label = ttk.Label(
			self,
			text = 'Shear Modulus:'
		)

		# Display the Member Shear Modulus Label
		self.memberG_Label.grid(
			column = 3,
			row = 1,
			sticky = ['E'],
			padx = [75,0],
			pady = [10,0]
		)

		# Define the Member Shear Modulus Entry Box
		self.memberG_Entry = ttk.Entry(
			self,
			textvariable = self.memberG_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Shear Modulus Entry Box
		self.memberG_Entry.grid(
			column = 4,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [12,2]
		)

		# Display the Member Modulus of Elasticity Units
		ttk.Label(self, text = 'ksi').grid(
			column = 5,
			row = 1,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ------------- MAJOR AXIS MOMENT OF INERTIA ------------- ###

		# Define Member Major Axis Moment of Inertia Variable
		self.memberIxx_Var = tk.StringVar()

		# Define Member ID Label
		self.memberIxx_Label = ttk.Label(
			self,
			text = 'Major Axis Moment of Interia:'
		)

		# Display the Member Major Axis Moment of Interia Label
		self.memberIxx_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Member Major Axis Moment of Inertia Entry Box
		self.memberIxx_Entry = ttk.Entry(
			self,
			textvariable = self.memberIxx_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Major Axis Moment of Interia Entry Box
		self.memberIxx_Entry.grid(
			column = 1,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Member Major Axis Moment of Interia Units
		ttk.Label(self, text = 'in^4').grid(
			column = 2,
			row = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ------------- MINOR AXIS MOMENT OF INERTIA ------------- ###

		# Define Member Minor Axis Moment of Inertia Variable
		self.memberIyy_Var = tk.StringVar()

		# Define Member Minor Axis Moment of Inertia Label
		self.memberIyy_Label = ttk.Label(
			self,
			text = 'Minor Axis Moment of Interia:'
		)

		# Display the Member Minor Axis Moment of Interia Label
		self.memberIyy_Label.grid(
			column = 3,
			row = 2,
			sticky = ['E'],
			padx = [75,0],
			pady = [10,0]
		)

		# Define the Member Minor Axis Moment of Inertia Entry Box
		self.memberIyy_Entry = ttk.Entry(
			self,
			textvariable = self.memberIyy_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Minor Axis Moment of Interia Entry Box
		self.memberIyy_Entry.grid(
			column = 4,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Member Minor Axis Moment of Interia Units
		ttk.Label(self, text = 'in^4').grid(
			column = 5,
			row = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### --------------------- SECTION AREA --------------------- ###

		# Define Member Section Area Variable
		self.memberA_Var = tk.StringVar()

		# Define Member Section Area Label
		self.memberA_Label = ttk.Label(
			self,
			text = 'Section Area:'
		)

		# Display the Member Section Area Label
		self.memberA_Label.grid(
			column = 0,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the Member Section Area Entry Box
		self.memberA_Entry = ttk.Entry(
			self,
			textvariable = self.memberA_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Section Area Entry Box
		self.memberA_Entry.grid(
			column = 1,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)

		# Display the Member Area Units
		ttk.Label(self, text = 'in^2').grid(
			column = 2,
			row = 3,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,10]
		)
 
		### --------------- POLAR MOMENT OF INERTIA ---------------- ###

		# Define Member Polar Moment of Inertia Variable
		self.memberJ_Var = tk.StringVar()

		# Define Member Polar Moment of Inertia Label
		self.memberJ_Label = ttk.Label(
			self,
			text = 'Polar Moment of Inertia:'
		)

		# Display the Member Polar Moment of Inertia Label
		self.memberJ_Label.grid(
			column = 3,
			row = 3,
			sticky = ['E'],
			padx = [75,0],
			pady = [10,10]
		)

		# Define the Member Polar Moment of Inertia Entry Box
		self.memberJ_Entry = ttk.Entry(
			self,
			textvariable = self.memberJ_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Polar Moment of Inertia Entry Box
		self.memberJ_Entry.grid(
			column = 4,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)

		# Display the Member Major Axis Moment of Interia Units
		ttk.Label(self, text = 'in^4').grid(
			column = 5,
			row = 3,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,10]
		)

	### ---------------------- CLASS METHODS ----------------------- ###

	def validateProperty(self, P):
		if P.strip() == '':
			return True

		try:
			f = float(P)
		except ValueError:
			self.bell()
			return False

		return True

	def openWindow(self):
		sub = tk.Toplevel()
		self.shapeSelector(sub, self.query, self.memberShape_Var).grid()

class memberDesign(ttk.Labelframe):
	def __init__(self, parent, model):
		ttk.Labelframe.__init__(
			self,
			parent,
			text = 'Design Parameters'
		)

		self.parent = parent
		self.model = model


		### -------------- MEMBER COMPRESSION BRACING -------------- ###

		# Define Member Compression Bracing Variable
		self.memberCb_Var = tk.StringVar()

		# Define Member Compression Bracing Label
		self.memberCb_Label = ttk.Label(
			self,
			text = 'Compression Bracing:'
		)

		# Display the Member Compression Bracing Label
		self.memberCb_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the Member Compression Bracing Entry Box
		self.memberCb_Combobox = ttk.Combobox(
			self,
			textvariable = self.memberCb_Var,
			values = ('midspan','quarter','third','continuous','none'),
			state = 'readonly'
		)

		# Display the Member Compression Bracing Entry Box
		self.memberCb_Combobox.grid(
			column = 1,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)

class memberMesh(ttk.Labelframe):
	def __init__(self, parent, model):
		ttk.Labelframe.__init__(
			self,
			parent,
			text = 'Finite Element Properties'
		)

		self.parent = parent
		self.model = model
		
		### ------------------ MEMBER FINITE MESH ------------------ ###

		# Define Member Finite Mesh Variable
		self.memberMesh_Var = tk.StringVar()

		# Define Member Finite Mesh Label
		self.memberMesh_Label = ttk.Label(
			self,
			text = 'Mesh:'
		)

		# Display the Member Finite Mesh Label
		self.memberMesh_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Register a command to use for mesh input validation
		vcmd = (self.register(self.validateMesh), '%P')

		# Define the Member Finite Mesh Entry Box
		self.memberMesh_Entry = ttk.Entry(
			self,
			textvariable = self.memberMesh_Var,
			validate = 'key',
			validatecommand = vcmd
		)

		# Display the Member Finite Mesh Entry Box
		self.memberMesh_Entry.grid(
			column = 1,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

	def validateMesh(self, P):
		'''

		'''
		if P.strip() == '':
			return True

		try:
			f = float(P)

		except ValueError:
			self.bell()
			return False

		if len(P) > 4:
			self.bell()
			return False

		return True

class memberInputWindow(ttk.Frame):
	def __init__(self, parent, model, plotter, shapeSelector, query):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.model = model
		self.plotter = plotter
		self.shapeSelector = shapeSelector
		self.query = query

		# Set the title for the Member Definition Window
		self.parent.title('Member Definition')

		# Set the default geometry for the Member Definition Window
		self.parent.geometry('1080x680')

		# Disable User Adjustment
		self.parent.resizable(width=False, height=False)

		# Automatically set the Member Definition Window to Active State
		self.parent.focus_force()

		# Allow One Instance of the Member Definition Window
		self.parent.grab_set()

		### ------------------ MODEL MEMBER TABLE ------------------ ###

		# Define the Member Definition Table
		self.table = Table(
			self.parent,
			self.model
		)

		# Display the Member Definition Table
		self.table.grid(
			column = 0,
			columnspan = 6,
			row = 0,
			rowspan = 11,
			sticky = ['N','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the user table selection to the updateSelection method
		self.table.bind(
			'<<TreeviewSelect>>',
			lambda e: self.updateSelection()
		)
		
		### ---------------- ADD DELETE & OK BUTTONS --------------- ###

		# Define the Add Member Button
		self.addMember_Button  = ttk.Button(
			self.parent,
			text = 'Add Member',
			command = self.addMember,
			default = 'active'
		)


		# Display the Add Member Button
		self.addMember_Button.grid(
			column = 0,
			columnspan = 2,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Enter Key to the Add Member Button
		self.parent.bind(
			'<Key-Return>',
			lambda e: self.addMember_Button.invoke()
		)

		# Define the Delete Member Button
		self.deleteMember_Button = ttk.Button(
			self.parent,
			text = 'Delete Member',
			command = self.deleteMember,
		)

		# Display the Delete Member Button
		self.deleteMember_Button.grid(
			column = 2,
			columnspan = 2,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Delete Key to the Delete Member Button
		self.parent.bind(
			'<Key-Delete>',
			lambda e: self.deleteMember_Button.invoke()
		)

		# Define the OK Button
		self.OK_Button = ttk.Button(
			self.parent,
			text = 'OK',
			command = self.close
		)

		# Display the OK Button
		self.OK_Button.grid(
			column = 4,
			columnspan = 2,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Binde the Escape Key to the OK Button
		self.parent.bind(
			'<Key-Escape>',
			lambda e: self.OK_Button.invoke()
		)

		### ------------------- NODE LABEL FRAME ------------------- ###

		# Define the Member Nodes Label Frame
		self.memberNodes = memberNodes(
			self.parent,
			self.model,
		)

		# Display the Member Nodes label Frame
		self.memberNodes.grid(
			column = 0,
			columnspan = 3,
			row = 13,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
			)

		# Bind the i Node Combobox to the update_iNode Method
		self.memberNodes.iNode_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.update_iNode()
		)

		# Bind the j Node Combobox to the update_jNode Method
		self.memberNodes.jNode_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.update_jNode()
		)

		# Bind the i Node Release Combobox to the update_NodeRelease Method
		self.memberNodes.iNodeRelease_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.update_iRelease()
		)

		# Bind the j Node Release Combobox to the update_jNodeRelease Method
		self.memberNodes.jNodeRelease_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.update_jRelease()
		)

		### ------------------- MESH LABEL FRAME ------------------- ###

		#Define the Member Mesh Label Frame
		self.memberMesh = memberMesh(
			self.parent,
			self.model
		)

		# Display the Member Mesh Label Frame
		self.memberMesh.grid(
			column = 3,
			columnspan = 3,
			row = 13,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# watch for changes to the Member Mesh Variable
		self.mbrMesh_Trace = \
		self.memberMesh.memberMesh_Var.trace_add(
			'write',
			self.updateMesh
		)

		### ------------- DESIGN PARAMETERS LABEL FRAME ------------ ###

		# Define the Member Design Paremeters Label Frame
		self.memberDesign = memberDesign(
			self.parent,
			self.model
		)

		# Display the Member Design Parameters Label Frame
		self.memberDesign.grid(
			column = 0,
			columnspan = 3,
			row = 14,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Member Bracing Combobox to the Update Bracing Method
		self.memberDesign.memberCb_Combobox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateBracing()
		)

		### ------------- MEMBER PROPERTIES LABEL FRAME ------------ ###

		# Define the Member Properties Label Frame
		self.memberProperties = memberProperties(
			self.parent,
			self.model,
			self.shapeSelector,
			self.query
		)

		# Display the Member Properties Label Frame
		self.memberProperties.grid(
			column = 0,
			columnspan = 6,
			row = 15,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# watch for changes to the Member Shape Variable
		self.mbrShape_Trace = \
		self.memberProperties.memberShape_Var.trace_add(
			'write',
			self.updateSection
		)

		# watch for changes to the Member Property Variables
		self.mbrIxx_Trace = \
		self.memberProperties.memberIxx_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrIyy_Trace = \
		self.memberProperties.memberIyy_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrA_Trace = \
		self.memberProperties.memberA_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrJ_Trace = \
		self.memberProperties.memberJ_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrE_Trace = \
		self.memberProperties.memberE_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrG_Trace = \
		self.memberProperties.memberG_Var.trace_add(
			'write',
			self.updateProperties
		)

	### ---------------------- CLASS METHODS ----------------------- ###

	def addMember(self):
		try:
			# collect all entries in the table
			entries = self.table.get_children()
			# select the last entry in the table if any
			self.table.focus(entries[-1])
			# identify the user defined properties for the last table entry
			index = int(self.table.focus())
			properties = self.table.item(index)['values']
		except IndexError:
			properties = None

		# add the member to the table
		self.table.addMember(properties)

		# set the table entry to the added member
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass
		
		# identify the added member
		index, mbr = self.returnMember()
		
		# plot the added member
		self.plotter.addMember(mbr)
		self.plotter.addMemberLabel(mbr)

	def deleteMember(self):
		# store the user selected member as a variable
		index, mbr = self.returnMember()

		# remove the member from the model
		self.model.members.removeMember(mbr)

		# remove the member from the table
		self.table.deleteMember()

		# remove the node from the plot
		self.plotter.removeMember(mbr)
		self.plotter.removeMemberLabel(mbr)

		# set the table entry to the last member
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass

	def returnMember(self):
		# identify and return the user selected member
		index = int(self.table.focus())
		member_id = int(self.table.item(index)['values'][0][1:])
		mbr = self.model.members.members[member_id]
		return(index, mbr)

	def update_iNode(self):
		# identify the user selected member
		index, mbr = self.returnMember()		

		# identify the user defined i node
		nodeName = self.memberNodes.iNode_Var.get()
		node = self.model.nodes.returnNode(nodeName)

		# update the member i node
		mbr.node_i = node

		# update the table
		values = self.table.item(index)['values']
		values[1] = nodeName
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updateMember(mbr)
		self.plotter.updateMemberLabel(mbr)

	def update_jNode(self):
		# identify the user selected member
		index, mbr = self.returnMember()		

		# identify the user defined j node
		nodeName = self.memberNodes.jNode_Var.get()
		node = self.model.nodes.returnNode(nodeName)

		# update the member i node
		mbr.node_j = node

		# update the table
		values = self.table.item(index)['values']
		values[3] = nodeName
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updateMember(mbr)
		self.plotter.updateMemberLabel(mbr)

	def update_iRelease(self):
		# identify the user selected member
		index, mbr = self.returnMember()

		# identify the user defined i release
		i_release = self.memberNodes.iNodeRelease_Var.get()

		if i_release == 'True':
			i_release = True
		else:
			i_release = False

		# check that the user changed the value
		if i_release == mbr.i_release:
			return

		else:		
			# update the member i release
			mbr.i_release = i_release

			# update the table
			values = self.table.item(index)['values']
			values[2] = i_release
			self.table.item(index, values = values)

			# update the plot
			if i_release == True:
				self.plotter.addMemberiPin(mbr)
			else:
				self.plotter.removeMemberiPin(mbr)

	def update_jRelease(self):
		# identify the user selected member
		index, mbr = self.returnMember()

		# identify the user defined i release
		j_release = self.memberNodes.jNodeRelease_Var.get()

		if j_release == 'True':
			j_release = True
		else:
			j_release = False

		# check that the user changed the value
		if j_release == mbr.j_release:
			return

		else:		
			# update the member i release
			mbr.j_release = j_release

			# update the table
			values = self.table.item(index)['values']
			values[2] = j_release
			self.table.item(index, values = values)

			# update the plot
			if j_release == True:
				self.plotter.addMemberjPin(mbr)
			else:
				self.plotter.removeMemberjPin(mbr)

	def updateMesh(self, *args):
		# identify the user selected member
		index, mbr = self.returnMember()

		# indetify the user defined model mesh
		mesh = self.memberMesh.memberMesh_Var.get()

		# update the member mesh
		mbr.mesh = int(mesh)

	def updateBracing(self):
		# identify the user selected member
		index, mbr = self.returnMember()

		# identify the user defined mesh
		bracing = self.memberDesign.memberCb_Var.get()

		# update the member bracing variable
		mbr.bracing = bracing

		# update the table
		values = self.table.item(index)['values']
		values[13] = bracing
		self.table.item(index, values = values)

	def updateSection(self, *args):
		# identify the user selected member
		index, mbr = self.returnMember()

		# retrieve the values stored in the table
		values = self.table.item(index)['values']

		# identify the user selected shape
		shape = self.memberProperties.memberShape_Var.get()

		# query the shape database for the selected shape properties
		properties = self.query.Get_Section_Properties(shape)

		# update the variables
		values[5] = shape
		values[7] = properties['Ix'][0]
		values[8] = properties['Iy'][0]
		values[9] = properties['A'][0]
		values[11] = properties['J'][0]

		self.memberProperties.memberIxx_Var.set(properties['Ix'][0])
		self.memberProperties.memberIyy_Var.set(properties['Iy'][0])
		self.memberProperties.memberA_Var.set(properties['A'][0])
		self.memberProperties.memberJ_Var.set(properties['J'][0])

		# update the member properties
		mbr.Izz = properties['Ix'][0]
		mbr.Iyy = properties['Iy'][0]
		mbr.A = properties['A'][0]
		mbr.J = properties['J'][0]
		mbr.shape = shape

		# update the table
		self.table.item(index, values = values)

	def updateProperties(self, *args):
		# identify the user selected member
		index, mbr = self.returnMember()

		# retrieve the values stored in the table
		values = self.table.item(index)['values']

		# update the variables
		values[5] = self.memberProperties.memberShape_Var.get()
		values[6] = self.memberProperties.memberE_Var.get()
		values[7] = self.memberProperties.memberIxx_Var.get()
		values[8] = self.memberProperties.memberIyy_Var.get()
		values[9] = self.memberProperties.memberA_Var.get()
		values[10] = self.memberProperties.memberG_Var.get()
		values[11] = self.memberProperties.memberJ_Var.get()

		# update the table
		self.table.item(index, values = values)

		# update the member
		mbr.shape = values[5]
		mbr.E = float(values[6])
		mbr.Izz = float(values[7])
		mbr.Iyy = float(values[8])
		mbr.A = float(values[9])
		mbr.G = float(values[10])
		mbr.J = float(values[11])

	def updateSelection(self):
		try:
			int(self.table.focus())
		except ValueError:
			return

		# temporarily remove object traces
		self.memberProperties.memberShape_Var.trace_remove(
			'write',
			self.mbrShape_Trace
		)

		self.memberProperties.memberIxx_Var.trace_remove(
			'write',
			self.mbrIxx_Trace
		)

		self.memberProperties.memberIyy_Var.trace_remove(
			'write',
			self.mbrIyy_Trace
		)

		self.memberProperties.memberA_Var.trace_remove(
			'write',
			self.mbrA_Trace
		)

		self.memberProperties.memberJ_Var.trace_remove(
			'write',
			self.mbrJ_Trace
		)

		self.memberProperties.memberE_Var.trace_remove(
			'write',
			self.mbrE_Trace
		)

		self.memberProperties.memberG_Var.trace_remove(
			'write',
			self.mbrG_Trace
		)

		self.memberMesh.memberMesh_Var.trace_remove(
			'write',
			self.mbrMesh_Trace
		)

		# store the user selected member as a variable
		index = self.table.focus()
		member = self.table.item(index)

		# collect the relevant member properties
		mbrID = member['values'][0]
		mbr_iNode = member['values'][1]
		mbr_iRelease = member['values'][2]
		mbr_jNode = member['values'][3]
		mbr_jRelease = member['values'][4]
		mbr_shape = member['values'][5]
		mbr_E = float(member['values'][6])
		mbr_Ixx = float(member['values'][7])
		mbr_Iyy = float(member['values'][8])
		mbr_A = float(member['values'][9])
		mbr_G = float(member['values'][10])
		mbr_J = float(member['values'][11])
		mbr_mesh = int(member['values'][12])
		mbr_Cb = member['values'][13]

		# update the Member Node values
		self.memberNodes.memberID_Var.set(mbrID)
		self.memberNodes.iNode_Var.set(mbr_iNode)
		self.memberNodes.jNode_Var.set(mbr_jNode)
		self.memberNodes.iNodeRelease_Var.set(mbr_iRelease)
		self.memberNodes.jNodeRelease_Var.set(mbr_jRelease)

		# update the Member Property Values
		self.memberProperties.memberShape_Var.set(mbr_shape)
		self.memberProperties.memberE_Var.set(mbr_E)
		self.memberProperties.memberIxx_Var.set(mbr_Ixx)
		self.memberProperties.memberIyy_Var.set(mbr_Iyy)
		self.memberProperties.memberA_Var.set(mbr_A)
		self.memberProperties.memberG_Var.set(mbr_G)
		self.memberProperties.memberJ_Var.set(mbr_J)

		# update the Member Design Parameter Values
		self.memberDesign.memberCb_Var.set(mbr_Cb)

		# Update the Member Finite Element Properties
		self.memberMesh.memberMesh_Var.set(mbr_mesh)

		# add object traces
		self.mbrShape_Trace = \
		self.memberProperties.memberShape_Var.trace_add(
			'write',
			self.updateSection
		)

		self.mbrIxx_Trace = \
		self.memberProperties.memberIxx_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrIyy_Trace = \
		self.memberProperties.memberIyy_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrA_Trace = \
		self.memberProperties.memberA_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrJ_Trace = \
		self.memberProperties.memberJ_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrE_Trace = \
		self.memberProperties.memberE_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrG_Trace = \
		self.memberProperties.memberG_Var.trace_add(
			'write',
			self.updateProperties
		)

		self.mbrMesh_Trace = \
		self.memberMesh.memberMesh_Var.trace_add(
			'write',
			self.updateMesh
		)

	def close(self):
		self.parent.destroy()