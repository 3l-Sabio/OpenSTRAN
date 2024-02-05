import sys
import os
import numpy as np

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

class Table(ttk.Treeview):
	def __init__(self, parent, model, *args, **kwargs):
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
			'load',
			'member',
			'direction',
			'deadLoad',
			'liveLoad',
			'roofLiveLoad',
			'snowLoad',
			'rainLoad',
			'windLoad',
			'seismicLoad',
			'location'
		)

		# define the column headings
		self.heading('load',text='Load')
		self.heading('member',text='Member')
		self.heading('direction',text='Direction')
		self.heading('deadLoad',text='D [k, k-ft]')
		self.heading('liveLoad',text='L [k, k-ft]')
		self.heading('roofLiveLoad',text='Lr [k, k-ft]')
		self.heading('snowLoad',text='S [k, k-ft]')
		self.heading('rainLoad',text='R [k, k-ft]')
		self.heading('windLoad',text='W [k, k-ft]')
		self.heading('seismicLoad',text='E [k, k-ft]')
		self.heading('location',text='Location [ft]')

		# center the columns and set the width
		self.column('load', anchor='center', minwidth=50, width=75)
		self.column('member', anchor='center', minwidth=50, width=75)
		self.column('direction', anchor='center', minwidth=50, width=75)
		self.column('deadLoad', anchor='center', minwidth=50, width=75)
		self.column('liveLoad', anchor='center', minwidth=50, width=75)
		self.column('roofLiveLoad', anchor='center', minwidth=50, width=75)
		self.column('snowLoad', anchor='center', minwidth=50, width=75)
		self.column('rainLoad', anchor='center', minwidth=50, width=75)
		self.column('windLoad', anchor='center', minwidth=50, width=75)
		self.column('seismicLoad', anchor='center', minwidth=50, width=75)
		self.column('location', anchor='center', minwidth=50, width=75)

		# fill in the load values
		for n, pointLoad in model.loads.pointLoads.items():
			values = []
			self.i += 1
			load = 'P{i}'.format(i=n)
			member = pointLoad.member.label
			values.append(load)
			values.append(pointLoad.member.label)
			values.append(pointLoad.direction)
			values.append(pointLoad.D)
			values.append(pointLoad.L)
			values.append(pointLoad.Lr)
			values.append(pointLoad.S)
			values.append(pointLoad.R)
			values.append(pointLoad.W)
			values.append(pointLoad.E)
			values.append(pointLoad.location)

			self.insert('','end',self.i,values=values)

		# set the table entry to the last point load
		try:
			child_id = self.get_children()[-1]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass

		self.i = self.model.loads.pointLoadCount

	def addLoad(self, properties):
		# determine the total number of user defined members
		m = 0
		for mbr in self.model.members.members.values():
				m += 1

		# check to make sure at least one member is defined
		if m < 1:
			tk.messagebox.showinfo(
				'No Members Defined!',
				'At least one member must be defined!'
			)
			return

		# update the number of table entries
		self.i += 1

		# set the new load default properties to the last load 
		# defined by the user if any
		if properties == None:
			member = list(self.model.members.members.values())[0]
			direction = 'Y'
			D = 0.0
			L = 0.0
			S = 0.0
			Lr = 0.0
			R = 0.0
			W = 0.0
			E = 0.0
			location = 0.0

			self.model.loads.addPointLoad(
				mbr = member,
				direction = direction,
				D = D,
				L = L,
				S = S,
				Lr = Lr,
				R = R,
				W = W,
				E = E,
				location = location
			)

		else:
			member = list(self.model.members.members.values())[0]
			self.model.loads.addPointLoad(
				mbr = member,
				direction = properties[2],
				D = properties[3],
				L = properties[4],
				S = properties[5],
				Lr = properties[6],
				R = properties[7],
				W = properties[8],
				E = properties[9],
				location = properties[10],
			)

		load = list(self.model.loads.pointLoads.values())[-1]
		label = 'P{i}'.format(i=list(self.model.loads.pointLoads.keys())[-1])

		values = []
		values.append(label)
		values.append(load.member.label)
		values.append(load.direction)
		values.append(load.D)
		values.append(load.L)
		values.append(load.Lr)
		values.append(load.S)
		values.append(load.R)
		values.append(load.W)
		values.append(load.E)
		values.append(load.location)

		self.insert('','end',self.i,values=values)

	def deleteLoad(self):
		self.delete(self.selection()[0])

class Members(ttk.Labelframe):
	def __init__(self, parent, model, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, text='Member')
		self.parent = parent
		self.model = model

		# Register a command to use for Member Length Input Validation
		vcmd = (self.register(self.validateLength), '%P')

		### -------------------- POINT LOAD ID -------------------- ###
		
		# Define Point Load ID Variable
		self.loadID_Var = tk.StringVar()

		# Define Point Load ID Label
		self.loadID_Label = ttk.Label(
			self,
			text = 'Point Load ID:'
		)

		# Display the Point Load ID Label
		self.loadID_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Point Load ID Entry Box
		self.loadID_Entry = ttk.Entry(
			self,
			textvariable = self.loadID_Var,
			state = 'disabled'
		)

		# Display the Point Load ID Entry Box
		self.loadID_Entry.grid(
			column = 1,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### ------------------------ MEMBER ------------------------ ###

		# Define the Member Label
		self.member_Label = ttk.Label(
			self,
			text = 'Member:'
		)

		# Display the Member Label
		self.member_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Member Variable
		self.member_Var = tk.StringVar()

		# Define Member Combobox
		self.member_Cbox = ttk.Combobox(
			self,
			textvariable = self.member_Var,
			values = self.getMembers(),
			state = 'readonly'
		)

		# Display the Member Combobox
		self.member_Cbox.grid(
			column = 1,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### -------------------- LOAD DIRECTION -------------------- ###

		# Define the Load Direction Label
		self.loadDirection_Label = ttk.Label(
			self,
			text = 'Load Direction:'
		)

		# Display the i Node Label
		self.loadDirection_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Load Direction Variable
		self.loadDirection_Var = tk.StringVar()

		# Define Load Direction Combobox
		self.loadDirection_Cbox = ttk.Combobox(
			self,
			textvariable = self.loadDirection_Var,
			values = ['X','Y','Z','x','y','z','Mx','My','Mz'],
			state = 'readonly'
		)

		# Display the Load Direction Combobox
		self.loadDirection_Cbox.grid(
			column = 1,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		### -------------------- MEMBER LENGTH -------------------- ###

		# Define Member Length Variable
		self.mbrLength_Var = tk.StringVar()

		# Define Member Length Label
		self.mbrLength_Label = ttk.Label(
			self,
			text = 'Member Length:'
		)

		# Display the Member Length Label
		self.mbrLength_Label.grid(
			column = 0,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Member Length Entry Box
		self.mbrLength_Entry = ttk.Entry(
			self,
			textvariable = self.mbrLength_Var,
			state = 'disabled'
		)

		# Display the Member Length Entry Box
		self.mbrLength_Entry.grid(
			column = 1,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = 'feet').grid(
			column = 2,
			row = 3,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### -------------------- LOAD LOCATION -------------------- ###

		# Define Load Location Variable
		self.loadLocation_Var = tk.StringVar()
		self.loadLocation_Var2 = tk.StringVar()

		# Define Load Location Labels
		self.loadLocation_Label = ttk.Label(
			self,
			text = 'Span Location:'
		)

		self.loadLocation_Label2 = ttk.Label(
			self,
			text = 'Span Location:'
		)

		# Display the Load Location Label
		self.loadLocation_Label.grid(
			column = 0,
			row = 4,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)


		# Define the Load Location Entry Box
		self.loadLocation_Entry = ttk.Entry(
			self,
			textvariable = self.loadLocation_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Load Location Entry Box
		self.loadLocation_Entry.grid(
			column = 1,
			row = 4,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = '%').grid(
			column = 2,
			row = 4,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		self.loadLocation_Label2.grid(
			column = 0,
			row = 5,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Load Location Entry Box
		self.loadLocation_Entry2 = ttk.Entry(
			self,
			textvariable = self.loadLocation_Var2,
			validate = 'key',
			validatecommand = vcmd,
			state = 'disabled'
		)

		# Display the Load Location Entry Box
		self.loadLocation_Entry2.grid(
			column = 1,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = 'feet').grid(
			column = 2,
			row = 5,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

	### ---------------------- CLASS METHODS ----------------------- ###

	def getMembers(self):
		# instantiate an array to hold the members
		members = []
		# iterate through the model members
		for mbr in self.model.members.members.values():
			members.append(mbr.label)
		# return the members
		return(members)

	def validateLength(self, P):
		if P.strip() == '':
			return True

		try:
			f = float(P)
		except ValueError:
			self.bell()
			return False

		if f <= float(100):
			return True
		else:
			self.bell()
			return False

class Loads(ttk.Labelframe):
	def __init__(self, parent, model, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, text = 'Loads')
		self.parent = parent
		self.model = model

		# register a command to use for load input validation
		vcmd = (self.register(self.validateLoad), '%P')

		### -------------------- UNITS VARIABLE -------------------- ###

		# Define a units Variable
		self.units_Var = tk.StringVar()

		# Set the default units variable to kips
		self.units_Var.set('kips')

		### ---------------------- DEAD LOAD ---------------------- ###

		# Define Dead Load Variable
		self.deadLoad_Var = tk.StringVar()

		# Define Dead Load Label
		self.deadLoad_Label = ttk.Label(
			self,
			text = 'Dead Load (D):'
		)

		# Display the Dead Load Label
		self.deadLoad_Label.grid(
			column = 0,
			row = 0,
			sticky = ['E'],
			padx = [15,0],
			pady = [0,0]
		)

		# Define the Dead Load Entry Box
		self.deadLoad_Entry = ttk.Entry(
			self,
			textvariable = self.deadLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Dead Load Entry Box
		self.deadLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [0,0]
		)

		# Display the Dead Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 0,
			sticky = ['W'],
			padx = [0,0],
			pady = [0,0]
		)

		### ---------------------- LIVE LOAD ---------------------- ###

		# Define Live Load Variable
		self.liveLoad_Var = tk.StringVar()

		# Define Live Load Label
		self.liveLoad_Label = ttk.Label(
			self,
			text = 'Live Load (L):'
		)

		# Display the Live Load Label
		self.liveLoad_Label.grid(
			column = 0,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Live Load Entry Box
		self.liveLoad_Entry = ttk.Entry(
			self,
			textvariable = self.liveLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Live Load Entry Box
		self.liveLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Live Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 1,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### -------------------- ROOF LIVE LOAD -------------------- ###

		# Define Roof Live Load Variable
		self.roofLiveLoad_Var = tk.StringVar()

		# Define Roof Live Load Label
		self.roofLiveLoad_Label = ttk.Label(
			self,
			text = 'Roof Live Load (Lr):'
		)

		# Display the Roof Live Load Label
		self.roofLiveLoad_Label.grid(
			column = 0,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Roof Live Load Entry Box
		self.roofLiveLoad_Entry = ttk.Entry(
			self,
			textvariable = self.roofLiveLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Roof Live Load Entry Box
		self.roofLiveLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Roof Live Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ---------------------- SNOW LOAD ---------------------- ###

		# Define Snow Load Variable
		self.snowLoad_Var = tk.StringVar()

		# Define Snow Load Label
		self.snowLoad_Label = ttk.Label(
			self,
			text = 'Snow Load (S):'
		)

		# Display the Snow Load Label
		self.snowLoad_Label.grid(
			column = 0,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Snow Load Entry Box
		self.snowLoad_Entry = ttk.Entry(
			self,
			textvariable = self.snowLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Snow Load Entry Box
		self.snowLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Snow Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 3,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ---------------------- RAIN LOAD ---------------------- ###

		# Define Rain Load Variable
		self.rainLoad_Var = tk.StringVar()

		# Define Rain Load Label
		self.rainLoad_Label = ttk.Label(
			self,
			text = 'Rain Load (R):'
		)

		# Display the Rain Load Label
		self.rainLoad_Label.grid(
			column = 0,
			row = 4,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Rain Load Entry Box
		self.rainLoad_Entry = ttk.Entry(
			self,
			textvariable = self.rainLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Rain Load Entry Box
		self.rainLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 4,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Rain Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 4,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ---------------------- WIND LOAD ---------------------- ###

		# Define Wind Load Variable
		self.windLoad_Var = tk.StringVar()

		# Define Wind Load Label
		self.windLoad_Label = ttk.Label(
			self,
			text = 'Wind Load (W):'
		)

		# Display the Wind Load Label
		self.windLoad_Label.grid(
			column = 0,
			row = 5,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Wind Load Entry Box
		self.windLoad_Entry = ttk.Entry(
			self,
			textvariable = self.windLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Wind Load Entry Box
		self.windLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,0]
		)

		# Display the Wind Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 5,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
		)

		### ------------------- EARTHQUAKE LOAD ------------------- ###

		# Define Earthquake Load Variable
		self.earthquakeLoad_Var = tk.StringVar()

		# Define Earthquake Load Label
		self.earthquakeLoad_Label = ttk.Label(
			self,
			text = 'Earthquake Load (E):'
		)

		# Display the Earthquake Load Label
		self.earthquakeLoad_Label.grid(
			column = 0,
			row = 6,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the Earthquake Load Entry Box
		self.earthquakeLoad_Entry = ttk.Entry(
			self,
			textvariable = self.earthquakeLoad_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Earthquake Load Entry Box
		self.earthquakeLoad_Entry.grid(
			column = 1,
			columnspan = 2,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [15,15],
			pady = [10,10]
		)

		# Display the Earthquake Load Units
		ttk.Label(self, textvariable=self.units_Var).grid(
			column = 5,
			row = 6,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,10]
		)

	### ---------------------- CLASS METHODS ----------------------- ###

	def validateLoad(self, P):
		if P.strip() == '':
			return True

		try:
			f = float(P)
		except ValueError:
			if P[0] == '-' and P[1:].strip() == '':
				return True
			try:
				f = float(P[1:])
			except ValueError:
				self.bell()
				return False

		return True

class pointLoadInputWindow(ttk.Frame):
	def __init__(self, parent, model, plotter, loadCombination, *args, **kwargs):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.model = model
		self.plotter = plotter
		self.loadCombination = loadCombination

		# Set the title for the Member Definition Window
		self.parent.title('Member Point Load Definition')

		# Set the default geometry for the Member Definition Window
		self.parent.geometry('855x530')

		# Disable User Adjustment
		self.parent.resizable(width=False, height=False)

		# Automatically set the Member Definition Window to Active State
		self.parent.focus_force()

		# Allow One Instance of the Member Definition Window
		self.parent.grab_set()

		### ---------------- MODEL POINT LOAD TABLE ---------------- ###

		# Define the Member Point Load Definition Table
		self.table = Table(
			self.parent,
			self.model
		)

		# Display the Member Point Load Definition Table
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

		# Define the Add Point Load Button
		self.addPointLoad_Button  = ttk.Button(
			self.parent,
			text = 'Add Load',
			command = self.addPointLoad,
			default = 'active'
		)


		# Display the Add Poit Load Button
		self.addPointLoad_Button.grid(
			column = 0,
			columnspan = 2,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Enter Key to the Add Point Load Button
		self.parent.bind(
			'<Key-Return>',
			lambda e: self.addPointLoad_Button.invoke()
		)

		# Define the Delete Point Load Button
		self.deletePointLoad_Button = ttk.Button(
			self.parent,
			text = 'Delete Load',
			command = self.deletePointLoad,
		)

		# Display the Delete Point Load Button
		self.deletePointLoad_Button.grid(
			column = 2,
			columnspan = 2,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Delete Key to the Delete Point Load Button
		self.parent.bind(
			'<Key-Delete>',
			lambda e: self.deletePointLoad_Button.invoke()
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

		# Bind the Escape Key to the OK Button
		self.parent.bind(
			'<Key-Escape>',
			lambda e: self.OK_Button.invoke()
		)

		### ------------------ MEMBER LABEL FRAME ------------------ ###

		# Define the Member Label Frame
		self.members = Members(
			self.parent,
			self.model
		)

		# Display the Member Label Frame
		self.members.grid(
			column = 0,
			columnspan = 3,
			row = 13,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Member Combobox to the Update Member Method
		self.members.member_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateMember()
		)

		# Bind the Load Direction Combobox to the Update Load Diection Method
		self.members.loadDirection_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateLoadDirection()
		)

		# watch for changes to the Span Location Variables
		self.location_Trace = \
		self.members.loadLocation_Var.trace_add(
			'write',
			self.updateLoadLocation
		)

		### ---------- MEMBER POINT LOAD DEFINITION FRAME ---------- ###

		# Define the Member Point Load Label Frame
		self.memberLoads = Loads(
			self.parent,
			self.model
		)

		# Display the Member Point Load label Frame
		self.memberLoads.grid(
			column = 3,
			columnspan = 3,
			row = 13,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# watch for changes to the Dead Load Variable
		self.deadLoad_Trace = \
		self.memberLoads.deadLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Live Load Variable
		self.liveLoad_Trace = \
		self.memberLoads.liveLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Roof Live Load Variable
		self.roofLiveLoad_Trace = \
		self.memberLoads.roofLiveLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Snow Load Variable
		self.snowLoad_Trace = \
		self.memberLoads.snowLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Rain Load Variable
		self.rainLoad_Trace = \
		self.memberLoads.rainLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Wind Load Variable
		self.windLoad_Trace = \
		self.memberLoads.windLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Earthquake Load Variable
		self.earthquakeLoad_Trace = \
		self.memberLoads.earthquakeLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

	### ---------------------- CLASS METHODS ----------------------- ###

	def updateSelection(self):
		try:
			int(self.table.focus())
		except ValueError:
			return

		# temporarily remove object traces
		self.members.loadLocation_Var.trace_remove(
			'write',
			self.location_Trace
		)

		self.memberLoads.deadLoad_Var.trace_remove(
			'write',
			self.deadLoad_Trace
		)

		self.memberLoads.liveLoad_Var.trace_remove(
			'write',
			self.liveLoad_Trace
		)

		self.memberLoads.roofLiveLoad_Var.trace_remove(
			'write',
			self.roofLiveLoad_Trace
		)

		self.memberLoads.snowLoad_Var.trace_remove(
			'write',
			self.snowLoad_Trace
		)

		self.memberLoads.windLoad_Var.trace_remove(
			'write',
			self.windLoad_Trace
		)

		self.memberLoads.earthquakeLoad_Var.trace_remove(
			'write',
			self.earthquakeLoad_Trace
		)

		self.memberLoads.rainLoad_Var.trace_remove(
			'write',
			self.rainLoad_Trace
		)

		# store the user selected load as a variable
		index = self.table.focus()
		load = self.table.item(index)

		# collect the relevant load properties
		load_id = load['values'][0]
		mbr = load['values'][1]
		direction = load['values'][2]
		location = load['values'][10]
		D = load['values'][3]
		L = load['values'][4]
		Lr = load['values'][5]
		S = load['values'][6]
		R = load['values'][7]
		W = load['values'][8]
		E = load['values'][9]

		# update the member values
		self.members.loadID_Var.set(load_id)
		self.members.member_Var.set(mbr)
		self.members.loadDirection_Var.set(direction)
		self.members.loadLocation_Var.set(location)

		# update the load values
		self.memberLoads.deadLoad_Var.set(D)
		self.memberLoads.liveLoad_Var.set(L)
		self.memberLoads.roofLiveLoad_Var.set(Lr)
		self.memberLoads.snowLoad_Var.set(S)
		self.memberLoads.rainLoad_Var.set(R)
		self.memberLoads.windLoad_Var.set(W)
		self.memberLoads.earthquakeLoad_Var.set(E)

		# update the reported member length
		self.updateLength()

		# add object traces
		self.location_Trace = \
		self.members.loadLocation_Var.trace_add(
			'write',
			self.updateLoadLocation
		)

		self.deadLoad_Trace = \
		self.memberLoads.deadLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.liveLoad_Trace = \
		self.memberLoads.liveLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.roofLiveLoad_Trace = \
		self.memberLoads.roofLiveLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.snowLoad_Trace = \
		self.memberLoads.snowLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.rainLoad_Trace = \
		self.memberLoads.rainLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.windLoad_Trace = \
		self.memberLoads.windLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.earthquakeLoad_Trace = \
		self.memberLoads.earthquakeLoad_Var.trace_add(
			'write',
			self.updateLoads
		)

	def addPointLoad(self):
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
		self.table.addLoad(properties)

		# set the table entry to the added member
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass

		#identify the user added point load
		index, load = self.returnLoad()

		# plot the added point load
		self.plotter.updatePointLoads(
			self.model,
			self.loadCombination.get()
		)

	def deletePointLoad(self):
		# store the user selected member as a variable
		index, load = self.returnLoad()

		# remove the point load from the model
		self.model.loads.removePointLoad(load)

		# remove the point load from the table
		self.table.deleteLoad()

		# remove the point load from the plot
		self.plotter.removePointLoad(load)
		#self.plotter.removeMemberLabel(mbr)

		# set the table entry to the last member
		try:
			child_id = self.table.get_children()[-1]
			self.table.focus(child_id)
			self.table.selection_set(child_id)
		except IndexError:
			pass

	def returnLoad(self):
		# identify and return the user selected point load
		index = int(self.table.focus())
		load_id = int(self.table.item(index)['values'][0][1:])
		load = self.model.loads.pointLoads[load_id]
		return(index, load)

	def updateLoads(self, *args):
		# identify the user selected load
		index, load = self.returnLoad()

		# retrieve the values stored in the table
		values = self.table.item(index)['values']

		# update the variables
		values[3] = self.memberLoads.deadLoad_Var.get()
		values[4] = self.memberLoads.liveLoad_Var.get()
		values[5] = self.memberLoads.roofLiveLoad_Var.get()
		values[6] = self.memberLoads.snowLoad_Var.get()
		values[7] = self.memberLoads.rainLoad_Var.get()
		values[8] = self.memberLoads.windLoad_Var.get()
		values[9] = self.memberLoads.earthquakeLoad_Var.get()

		# update the table
		self.table.item(index, values=values)

		# update the load
		try:
			load.D = float(values[3])
		except ValueError:
			load.D = 0

		try:
			load.L = float(values[4])
		except ValueError:
			load.L = 0

		try:
			load.Lr = float(values[5])
		except ValueError:
			load.Lr =0

		try:
			load.S = float(values[6])
		except ValueError:
			load.S = 0

		try:
			load.R = float(values[7])
		except ValueError:
			load.R = 0

		try:
			load.W = float(values[8])
		except ValueError:
			load.W = 0
			
		try:
			load.E = float(values[9])
		except ValueError:
			load.E = 0

		# update the plot
		self.plotter.updatePointLoads(
			self.model,
			self.loadCombination.get()
		)

	def updateMember(self):
		# identify the user selected load
		index, load = self.returnLoad()		

		# identify the user defined member
		mbrName = self.members.member_Var.get()
		member_id = int(mbrName[1:])
		mbr = self.model.members.members[member_id]

		# update the load member
		load.member = mbr

		# update the table
		values = self.table.item(index)['values']
		values[1] = load.member.label
		self.table.item(index, values = values)

		# update the reported member length
		self.updateLength()

		# update the plot
		self.plotter.updatePointLoads(
			self.model,
			self.loadCombination.get()
		)
		
	def updateLength(self):
		# identify the user selected load
		index, load = self.returnLoad()

		# calculate the member length
		ix = load.member.node_i.x
		iy = load.member.node_i.y
		iz = load.member.node_i.z

		jx = load.member.node_j.x
		jy = load.member.node_j.y
		jz = load.member.node_j.z

		dx = jx - ix
		dy = jy - iy
		dz = jz - iz

		l = round(np.sqrt(dx**2 + dy**2 + dz**2),2)

		# update the reported member length
		self.members.mbrLength_Var.set(l)

		# calculate the location of the load as a percentage of the length
		location = self.members.loadLocation_Var.get()

		try:
			self.members.loadLocation_Var2.set(
				round(l*float(location)/100,2)
			)

		except ValueError:
			self.members.loadLocation_Var2.set('0.0')

	def updateLoadDirection(self):
		# identify the user selected load
		index, load = self.returnLoad()

		# identify the user defined load direction
		direction = self.members.loadDirection_Var.get()

		# update the load direction
		load.direction = direction

		# update the table
		values = self.table.item(index)['values']
		values[2] = load.direction
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updatePointLoads(
			self.model,
			self.loadCombination.get()
		)
	
	def updateLoadLocation(self, *args):
		# identify the user selected load
		index, load = self.returnLoad()

		# identify the user defined load location
		length = self.members.mbrLength_Var.get()
		location = self.members.loadLocation_Var.get()

		# update the load location in feet combobox
		try:
			self.members.loadLocation_Var2.set(
				round(float(length)*float(location)/100,2)
			)

		except ValueError:
			self.members.loadLocation_Var2.set('0.0')

		# update the load location
		load.location = location

		# update the table
		values = self.table.item(index)['values']
		values[10] = location
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updatePointLoads(
			self.model,
			self.loadCombination.get()
		)

	def close(self):
		self.parent.destroy()