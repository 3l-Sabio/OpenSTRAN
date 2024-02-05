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
		self.heading('deadLoad',text='D [kips]')
		self.heading('liveLoad',text='L [kips]')
		self.heading('roofLiveLoad',text='Lr [kips]')
		self.heading('snowLoad',text='S [kips]')
		self.heading('rainLoad',text='R [kips]')
		self.heading('windLoad',text='W [kips]')
		self.heading('seismicLoad',text='E [kips]')
		self.heading('location',text='Location [%]')

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
		for n, distLoad in model.loads.distLoads.items():
			values = []
			self.i += 1
			load = 'W{i}'.format(i=n)
			member = distLoad.member.label
			values.append(load)
			values.append(distLoad.member.label)
			values.append(distLoad.direction)
			values.append('{s} ; {e}'.format(s=distLoad.D[0], e=distLoad.D[1]))
			values.append('{s} ; {e}'.format(s=distLoad.L[0], e=distLoad.L[1]))
			values.append('{s} ; {e}'.format(s=distLoad.Lr[0], e=distLoad.Lr[1]))
			values.append('{s} ; {e}'.format(s=distLoad.S[0], e=distLoad.S[1]))
			values.append('{s} ; {e}'.format(s=distLoad.R[0], e=distLoad.R[1]))
			values.append('{s} ; {e}'.format(s=distLoad.W[0], e=distLoad.W[1]))
			values.append('{s} ; {e}'.format(s=distLoad.E[0], e=distLoad.E[1]))
			values.append('{s} ; {e}'.format(s=distLoad.location[0], e=distLoad.location[1]))

			self.insert('','end',self.i,values=values)

		# set the table entry to the last point load
		try:
			child_id = self.get_children()[-1]
			self.focus(child_id)
			self.selection_set(child_id)
		except IndexError:
			pass

		self.i = self.model.loads.distLoadCount

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
			D = '0.0 ; 0.0'
			L = '0.0 ; 0.0'
			S = '0.0 ; 0.0'
			Lr = '0.0 ; 0.0'
			R = '0.0 ; 0.0'
			W = '0.0 ; 0.0'
			E = '0.0 ; 0.0'
			location = '0 ; 100'

			self.model.loads.addDistLoad(
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
			self.model.loads.addDistLoad(
				mbr = member,
				direction = properties[2],
				D = properties[3],
				L = properties[4],
				Lr = properties[5],
				S = properties[6],
				R = properties[7],
				W = properties[8],
				E = properties[9],
				location = properties[10],
			)

		load = list(self.model.loads.distLoads.values())[-1]
		label = 'W{i}'.format(i=list(self.model.loads.distLoads.keys())[-1])

		values = []
		values.append(label)
		values.append(load.member.label)
		values.append(load.direction)
		values.append('{s} ; {e}'.format(s=load.D[0],e=load.D[1]))
		values.append('{s} ; {e}'.format(s=load.L[0],e=load.L[1]))
		values.append('{s} ; {e}'.format(s=load.Lr[0],e=load.Lr[1]))
		values.append('{s} ; {e}'.format(s=load.S[0],e=load.S[1]))
		values.append('{s} ; {e}'.format(s=load.R[0],e=load.R[1]))
		values.append('{s} ; {e}'.format(s=load.W[0],e=load.W[1]))
		values.append('{s} ; {e}'.format(s=load.E[0],e=load.E[1]))
		values.append('{s} ; {e}'.format(s=load.location[0],e=load.location[1]))

		self.insert('','end',self.i,values=values)

	def deleteLoad(self):
		self.delete(self.selection()[0])

class Members(ttk.Labelframe):
	def __init__(self, parent, model, *args, **kwargs):
		ttk.Labelframe.__init__(self, parent, text='Member')
		self.parent = parent
		self.model = model

		# Register commands to use for Load Location Input Validation
		vcmd = (self.register(self.validateLocation), '%P')


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
			columnspan = 2,
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
			column = 2,
			columnspan = 2,
			row = 0,
			sticky = ['N','S','E','W'],
			padx = [5,5],
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
			columnspan = 2,
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
			column = 2,
			columnspan = 2,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [5,5],
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
			columnspan = 2,
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
			values = ['X','Y','Z','x','y','z'],
			state = 'readonly'
		)

		# Display the Load Direction Combobox
		self.loadDirection_Cbox.grid(
			column = 2,
			columnspan = 2,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [5,5],
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
			columnspan = 2,
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
			column = 2,
			columnspan = 2,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = 'feet').grid(
			column = 4,
			columnspan = 2,
			row = 3,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### ---------- START AND END LOAD LOCATION LABELS ---------- ###

		# Define Load Location Label
		self.loadLocationStart_Label = ttk.Label(
			self,
			text = 'Start Location',
			anchor = 'center'
		)

		# Display the Load Location Label
		self.loadLocationStart_Label.grid(
			column = 2,
			row = 4,
			sticky = ['E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define Load Location Label
		self.loadLocationEnd_Label = ttk.Label(
			self,
			text = 'End Location',
			anchor = 'center'
		)

		# Display the Load Location Label
		self.loadLocationEnd_Label.grid(
			column = 3,
			row = 4,
			sticky = ['E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		### ---- LOAD START AND END LOCATION AS SPAN PERCENTAGE ---- ###

		# Define Load Start and End Location Variables
		self.loadLocationStart_Var = tk.StringVar()
		self.loadLocationEnd_Var = tk.StringVar()

		# Define the Span Location Label
		self.loadLocation_Label = ttk.Label(
			self,
			text = 'Span Location',
		)

		# Display the Load Location Label
		self.loadLocation_Label.grid(
			column = 0,
			columnspan = 2,
			row = 5,
			sticky = ['E'],
			padx = [15,0],
			pady = [0,0]
		)

		# Define the Load Start Location Entry Box
		self.loadLocationStart_Entry = ttk.Entry(
			self,
			textvariable = self.loadLocationStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Load Location Entry Box
		self.loadLocationStart_Entry.grid(
			column = 2,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [0,0]
		)

		# Define the Load End Location Entry Box
		self.loadLocationEnd_Entry = ttk.Entry(
			self,
			textvariable = self.loadLocationEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Load End Location Entry Box
		self.loadLocationEnd_Entry.grid(
			column = 3,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [0,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = '%').grid(
			column = 4,
			columnspan = 2,
			row = 5,
			sticky = ['W'],
			padx = [0,10],
			pady = [0,0]
		)

		### ------------ START AND END LOCATION IN FEET ------------ ###

		# Define Load Start and End Location Variables
		self.loadLocationStart_Var2 = tk.StringVar()
		self.loadLocationEnd_Var2 = tk.StringVar()

		# Define the Span Location Label
		self.loadLocation_Label2 = ttk.Label(
			self,
			text = 'Span Location',
		)

		# Display the Load Location Label
		self.loadLocation_Label2.grid(
			column = 0,
			columnspan = 2,
			row = 6,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Load Start Location Entry Box
		self.loadLocationStart_Entry2 = ttk.Entry(
			self,
			textvariable = self.loadLocationStart_Var2,
			validate = 'key',
			state = 'disabled'
		)

		# Display the Load Location Entry Box
		self.loadLocationStart_Entry2.grid(
			column = 2,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Load End Location Entry Box
		self.loadLocationEnd_Entry2 = ttk.Entry(
			self,
			textvariable = self.loadLocationEnd_Var2,
			validate = 'key',
			state = 'disabled'
		)

		# Display the Load End Location Entry Box
		self.loadLocationEnd_Entry2.grid(
			column = 3,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Load Location Units
		ttk.Label(self, text = 'feet').grid(
			column = 4,
			columnspan = 2,
			row = 6,
			sticky = ['W'],
			padx = [0,10],
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

	def validateLocation(self, P):
		if P.strip() == '':
			return True

		try:
			f = float(P)
		except ValueError:
			self.bell()
			return False

		if 0 <= f <= 100:
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

		### ----------------------- HEADERS ----------------------- ###
		self.startLabel = ttk.Label(
			self,
			text = 'Start Magnitude',
			anchor = 'center'
		)

		self.endLabel = ttk.Label(
			self,
			text = 'End Magnitude',
			anchor = 'center'
		)

		self.startLabel.grid(
			column = 2,
			row = 0,
			sticky = ['E','W'],
			padx = [0,0],
			pady = [0,0]
		)
		
		self.endLabel.grid(
			column = 3,
			row = 0,
			sticky = ['E','W'],
			padx = [0,0],
			pady = [0,0]
		)

		### ---------------------- DEAD LOAD ---------------------- ###

		# Define Dead Load Variable
		self.deadLoadStart_Var = tk.StringVar()
		self.deadLoadEnd_Var = tk.StringVar()

		# Define Dead Load Label
		self.deadLoad_Label = ttk.Label(
			self,
			text = 'Dead Load (D):'
		)

		# Display the Dead Load Label
		self.deadLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 1,
			sticky = ['E'],
			padx = [15,0],
			pady = [0,0]
		)

		# Define the Dead Load Start Entry Box
		self.deadLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.deadLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Dead Load Start Entry Box
		self.deadLoadStart_Entry.grid(
			column = 2,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [0,0]
		)

		# Define the Dead Load End Entry Box
		self.deadLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.deadLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Dead Load End Entry Box
		self.deadLoadEnd_Entry.grid(
			column = 3,
			row = 1,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [0,0]
		)

		# Display the Dead Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 1,
			sticky = ['W'],
			padx = [0,10],
			pady = [0,0]
		)

		### ---------------------- LIVE LOAD ---------------------- ###

		# Define Live Load Variable
		self.liveLoadStart_Var = tk.StringVar()
		self.liveLoadEnd_Var = tk.StringVar()

		# Define Live Load Label
		self.liveLoad_Label = ttk.Label(
			self,
			text = 'Live Load (L):'
		)

		# Display the Live Load Label
		self.liveLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Live Load Start Entry Box
		self.liveLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.liveLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Live Load Start Entry Box
		self.liveLoadStart_Entry.grid(
			column = 2,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Live Load End Entry Box
		self.liveLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.liveLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Live Load End Entry Box
		self.liveLoadEnd_Entry.grid(
			column = 3,
			row = 2,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Live Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 2,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### -------------------- ROOF LIVE LOAD -------------------- ###

		# Define Roof Live Load Variable
		self.roofLiveLoadStart_Var = tk.StringVar()
		self.roofLiveLoadEnd_Var = tk.StringVar()

		# Define Roof Live Load Label
		self.roofLiveLoad_Label = ttk.Label(
			self,
			text = 'Roof Live Load (Lr):'
		)

		# Display the Roof Live Load Label
		self.roofLiveLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 3,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Roof Live Load Start Entry Box
		self.roofLiveLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.roofLiveLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Roof Live Load Start Entry Box
		self.roofLiveLoadStart_Entry.grid(
			column = 2,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Roof Live Load End Entry Box
		self.roofLiveLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.roofLiveLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Roof Live Load End Entry Box
		self.roofLiveLoadEnd_Entry.grid(
			column = 3,
			row = 3,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Roof Live Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 3,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### ---------------------- SNOW LOAD ---------------------- ###

		# Define Snow Load Variable
		self.snowLoadStart_Var = tk.StringVar()
		self.snowLoadEnd_Var = tk.StringVar()

		# Define Snow Load Label
		self.snowLoad_Label = ttk.Label(
			self,
			text = 'Snow Load (S):'
		)

		# Display the Snow Load Label
		self.snowLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 4,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Snow Load Start Entry Box
		self.snowLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.snowLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Snow Load Start Entry Box
		self.snowLoadStart_Entry.grid(
			column = 2,
			row = 4,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Snow Load End Entry Box
		self.snowLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.snowLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Snow Load End Entry Box
		self.snowLoadEnd_Entry.grid(
			column = 3,
			row = 4,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Snow Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 4,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### ---------------------- RAIN LOAD ---------------------- ###

		# Define Rain Load Variable
		self.rainLoadStart_Var = tk.StringVar()
		self.rainLoadEnd_Var = tk.StringVar()

		# Define Rain Load Label
		self.rainLoad_Label = ttk.Label(
			self,
			text = 'Rain Load (R):'
		)

		# Display the Rain Load Label
		self.rainLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 5,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Rain Load Start Entry Box
		self.rainLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.rainLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Rain Load Start Entry Box
		self.rainLoadStart_Entry.grid(
			column = 2,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Rain Load End Entry Box
		self.rainLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.rainLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Rain Load End Entry Box
		self.rainLoadEnd_Entry.grid(
			column = 3,
			row = 5,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Rain Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 5,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### ---------------------- WIND LOAD ---------------------- ###

		# Define Wind Load Variable
		self.windLoadStart_Var = tk.StringVar()
		self.windLoadEnd_Var = tk.StringVar()

		# Define Wind Load Label
		self.windLoad_Label = ttk.Label(
			self,
			text = 'Wind Load (W):'
		)

		# Display the Wind Load Label
		self.windLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 6,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
		)

		# Define the Wind Load Start Entry Box
		self.windLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.windLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Wind Load Start Entry Box
		self.windLoadStart_Entry.grid(
			column = 2,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Define the Wind Load End Entry Box
		self.windLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.windLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Wind Load End Entry Box
		self.windLoadEnd_Entry.grid(
			column = 3,
			row = 6,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,0]
		)

		# Display the Wind Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 6,
			sticky = ['W'],
			padx = [0,10],
			pady = [10,0]
		)

		### ------------------- EARTHQUAKE LOAD ------------------- ###

		# Define Earthquake Load Variable
		self.earthquakeLoadStart_Var = tk.StringVar()
		self.earthquakeLoadEnd_Var = tk.StringVar()

		# Define Earthquake Load Label
		self.earthquakeLoad_Label = ttk.Label(
			self,
			text = 'Earthquake Load (E):'
		)

		# Display the Earthquake Load Label
		self.earthquakeLoad_Label.grid(
			column = 0,
			columnspan = 2,
			row = 7,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,10]
		)

		# Define the Earthquake Load Start Entry Box
		self.earthquakeLoadStart_Entry = ttk.Entry(
			self,
			textvariable = self.earthquakeLoadStart_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Earthquake Load Start Entry Box
		self.earthquakeLoadStart_Entry.grid(
			column = 2,
			row = 7,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,10]
		)

		# Define the Earthquake Load End Entry Box
		self.earthquakeLoadEnd_Entry = ttk.Entry(
			self,
			textvariable = self.earthquakeLoadEnd_Var,
			validate = 'key',
			validatecommand = vcmd,
			state = 'active'
		)

		# Display the Earthquake Load End Entry Box
		self.earthquakeLoadEnd_Entry.grid(
			column = 3,
			row = 7,
			sticky = ['N','S','E','W'],
			padx = [5,5],
			pady = [10,10]
		)

		# Display the Earthquake Load Units
		ttk.Label(self, textvariable=self.units_Var, anchor='w').grid(
			column = 4,
			columnspan = 2,
			row = 7,
			sticky = ['W'],
			padx = [0,10],
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

class distLoadInputWindow(ttk.Frame):
	def __init__(self, parent, model, plotter, loadCombination, *args, **kwargs):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.model = model
		self.plotter = plotter
		self.loadCombination = loadCombination

		# Set the title for the Member Definition Window
		self.parent.title('Member Distributed Load Definition')

		# Set the default geometry for the Member Definition Window
		self.parent.geometry('900x550')

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
			columnspan = 12,
			row = 0,
			rowspan = 11,
			sticky = ['E','W'],
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
		self.addDistLoad_Button  = ttk.Button(
			self.parent,
			text = 'Add Load',
			command = self.addDistLoad,
			default = 'active'
		)


		# Display the Add Poit Load Button
		self.addDistLoad_Button.grid(
			column = 0,
			columnspan = 4,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Enter Key to the Add Point Load Button
		self.parent.bind(
			'<Key-Return>',
			lambda e: self.addDistLoad_Button.invoke()
		)

		# Define the Delete Point Load Button
		self.deleteDistLoad_Button = ttk.Button(
			self.parent,
			text = 'Delete Load',
			command = self.deleteDistLoad,
		)

		# Display the Delete Point Load Button
		self.deleteDistLoad_Button.grid(
			column = 4,
			columnspan = 4,
			row = 12,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# Bind the Delete Key to the Delete Point Load Button
		self.parent.bind(
			'<Key-Delete>',
			lambda e: self.deleteDistLoad_Button.invoke()
		)

		# Define the OK Button
		self.OK_Button = ttk.Button(
			self.parent,
			text = 'OK',
			command = self.close
		)

		# Display the OK Button
		self.OK_Button.grid(
			column = 8,
			columnspan = 4,
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
			columnspan = 6,
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
		self.locationStart_Trace = \
		self.members.loadLocationStart_Var.trace_add(
			'write',
			self.updateLoadStartLocation
		)

		self.locationEnd_Trace = \
		self.members.loadLocationEnd_Var.trace_add(
			'write',
			self.updateLoadEndLocation
		)

		### ---------- MEMBER POINT LOAD DEFINITION FRAME ---------- ###

		# Define the Member Point Load Label Frame
		self.memberLoads = Loads(
			self.parent,
			self.model
		)

		# Display the Member Point Load label Frame
		self.memberLoads.grid(
			column = 6,
			columnspan = 6,
			row = 13,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
		)

		# watch for changes to the Dead Load Variables
		self.deadLoadStart_Trace = \
		self.memberLoads.deadLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.deadLoadEnd_Trace = \
		self.memberLoads.deadLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Live Load Variables
		self.liveLoadStart_Trace = \
		self.memberLoads.liveLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.liveLoadEnd_Trace = \
		self.memberLoads.liveLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Roof Live Load Variables
		self.roofLiveLoadStart_Trace = \
		self.memberLoads.roofLiveLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.roofLiveLoadEnd_Trace = \
		self.memberLoads.roofLiveLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Snow Load Variables
		self.snowLoadStart_Trace = \
		self.memberLoads.snowLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.snowLoadEnd_Trace = \
		self.memberLoads.snowLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Rain Load Variables
		self.rainLoadStart_Trace = \
		self.memberLoads.rainLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.rainLoadEnd_Trace = \
		self.memberLoads.rainLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Wind Load Variables
		self.windLoadStart_Trace = \
		self.memberLoads.windLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.windLoadEnd_Trace = \
		self.memberLoads.windLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Earthquake Load Variables
		self.earthquakeLoadStart_Trace = \
		self.memberLoads.earthquakeLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		# watch for changes to the Earthquake Load Variables
		self.earthquakeLoadEnd_Trace = \
		self.memberLoads.earthquakeLoadEnd_Var.trace_add(
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
		self.members.loadLocationStart_Var.trace_remove(
			'write',
			self.locationStart_Trace
		)

		self.members.loadLocationEnd_Var.trace_remove(
			'write',
			self.locationEnd_Trace
		)

		self.memberLoads.deadLoadStart_Var.trace_remove(
			'write',
			self.deadLoadStart_Trace
		)

		self.memberLoads.deadLoadEnd_Var.trace_remove(
			'write',
			self.deadLoadEnd_Trace
		)

		self.memberLoads.liveLoadStart_Var.trace_remove(
			'write',
			self.liveLoadStart_Trace
		)

		self.memberLoads.liveLoadEnd_Var.trace_remove(
			'write',
			self.liveLoadEnd_Trace
		)

		self.memberLoads.roofLiveLoadStart_Var.trace_remove(
			'write',
			self.roofLiveLoadStart_Trace
		)

		self.memberLoads.roofLiveLoadEnd_Var.trace_remove(
			'write',
			self.roofLiveLoadEnd_Trace
		)

		self.memberLoads.snowLoadStart_Var.trace_remove(
			'write',
			self.snowLoadStart_Trace
		)

		self.memberLoads.snowLoadEnd_Var.trace_remove(
			'write',
			self.snowLoadEnd_Trace
		)

		self.memberLoads.windLoadStart_Var.trace_remove(
			'write',
			self.windLoadStart_Trace
		)

		self.memberLoads.windLoadEnd_Var.trace_remove(
			'write',
			self.windLoadEnd_Trace
		)

		self.memberLoads.earthquakeLoadStart_Var.trace_remove(
			'write',
			self.earthquakeLoadStart_Trace
		)

		self.memberLoads.earthquakeLoadEnd_Var.trace_remove(
			'write',
			self.earthquakeLoadEnd_Trace
		)

		self.memberLoads.rainLoadStart_Var.trace_remove(
			'write',
			self.rainLoadStart_Trace
		)

		self.memberLoads.rainLoadEnd_Var.trace_remove(
			'write',
			self.rainLoadEnd_Trace
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
		self.members.loadLocationStart_Var.set(location[:location.index(';')].strip())
		self.members.loadLocationEnd_Var.set(location[location.index(';')+1:].strip())

		# update the start load values
		self.memberLoads.deadLoadStart_Var.set(D[:D.index(';')].strip())
		self.memberLoads.liveLoadStart_Var.set(L[:L.index(';')].strip())
		self.memberLoads.roofLiveLoadStart_Var.set(Lr[:Lr.index(';')].strip())
		self.memberLoads.snowLoadStart_Var.set(S[:S.index(';')].strip())
		self.memberLoads.rainLoadStart_Var.set(R[:R.index(';')].strip())
		self.memberLoads.windLoadStart_Var.set(W[:W.index(';')].strip())
		self.memberLoads.earthquakeLoadStart_Var.set(E[:E.index(';')].strip())

		# update the end load values
		self.memberLoads.deadLoadEnd_Var.set(D[D.index(';')+1:].strip())
		self.memberLoads.liveLoadEnd_Var.set(L[L.index(';')+1:].strip())
		self.memberLoads.roofLiveLoadEnd_Var.set(Lr[Lr.index(';')+1:].strip())
		self.memberLoads.snowLoadEnd_Var.set(S[S.index(';')+1:].strip())
		self.memberLoads.rainLoadEnd_Var.set(R[R.index(';')+1:].strip())
		self.memberLoads.windLoadEnd_Var.set(W[W.index(';')+1:].strip())
		self.memberLoads.earthquakeLoadEnd_Var.set(E[E.index(';')+1:].strip())

		# update the reported member length
		self.updateLength()

		# add object traces
		self.locationStart_Trace = \
		self.members.loadLocationStart_Var.trace_add(
			'write',
			self.updateLoadStartLocation
		)

		self.locationEnd_Trace = \
		self.members.loadLocationEnd_Var.trace_add(
			'write',
			self.updateLoadEndLocation
		)

		self.deadLoadStart_Trace = \
		self.memberLoads.deadLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.deadLoadEnd_Trace = \
		self.memberLoads.deadLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.liveLoadStart_Trace = \
		self.memberLoads.liveLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.liveLoadEnd_Trace = \
		self.memberLoads.liveLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.roofLiveLoadStart_Trace = \
		self.memberLoads.roofLiveLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.roofLiveLoadEnd_Trace = \
		self.memberLoads.roofLiveLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.snowLoadStart_Trace = \
		self.memberLoads.snowLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.snowLoadEnd_Trace = \
		self.memberLoads.snowLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.rainLoadStart_Trace = \
		self.memberLoads.rainLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.rainLoadEnd_Trace = \
		self.memberLoads.rainLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.windLoadStart_Trace = \
		self.memberLoads.windLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.windLoadEnd_Trace = \
		self.memberLoads.windLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.earthquakeLoadStart_Trace = \
		self.memberLoads.earthquakeLoadStart_Var.trace_add(
			'write',
			self.updateLoads
		)

		self.earthquakeLoadEnd_Trace = \
		self.memberLoads.earthquakeLoadEnd_Var.trace_add(
			'write',
			self.updateLoads
		)

	def addDistLoad(self):
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

		#identify the user added distributed load
		index, load = self.returnLoad()

		# plot the added distributed load
		self.plotter.updateDistLoads(
			self.model,
			self.loadCombination.get()
		)

	def deleteDistLoad(self):
		# store the user selected member as a variable
		index, load = self.returnLoad()

		# remove the point load from the model
		self.model.loads.removeDistLoad(load)

		# remove the point load from the table
		self.table.deleteLoad()

		# remove the point load from the plot
		self.plotter.removeDistLoad(load)
		self.plotter.canvas.draw_idle()
		self.plotter.canvas.flush_events()

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
		load = self.model.loads.distLoads[load_id]
		return(index, load)

	def updateLoads(self, *args):
		# identify the user selected load
		index, load = self.returnLoad()

		# retrieve the values stored in the table
		values = self.table.item(index)['values']

		# update the variables
		values[3] = str('{s} ; {e}'.format(
				s = self.memberLoads.deadLoadStart_Var.get(),
				e = self.memberLoads.deadLoadEnd_Var.get()
			)
		)

		values[4] = str('{s} ; {e}'.format(
				s = self.memberLoads.liveLoadStart_Var.get(),
				e = self.memberLoads.liveLoadEnd_Var.get()
			)
		)

		values[5] = str('{s} ; {e}'.format(
				s = self.memberLoads.roofLiveLoadStart_Var.get(),
				e = self.memberLoads.roofLiveLoadEnd_Var.get()
			)
		)

		values[6] = str('{s} ; {e}'.format(
				s = self.memberLoads.snowLoadStart_Var.get(),
				e = self.memberLoads.snowLoadEnd_Var.get()
			)
		)

		values[7] = str('{s} ; {e}'.format(
				s = self.memberLoads.rainLoadStart_Var.get(),
				e = self.memberLoads.rainLoadEnd_Var.get()
			)
		)

		values[8] = str('{s} ; {e}'.format(
				s = self.memberLoads.windLoadStart_Var.get(),
				e = self.memberLoads.windLoadEnd_Var.get()
			)
		)

		values[9] = str('{s} ; {e}'.format(
				s = self.memberLoads.earthquakeLoadStart_Var.get(),
				e = self.memberLoads.earthquakeLoadEnd_Var.get()
			)
		)

		# update the table
		self.table.item(index, values=values)

		# update the dead load
		try:
			s = float(values[3][:values[3].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[3][values[3].index(';')+1:])
		except ValueError:
			e = 0

		load.D = (s,e)

		# update the live load
		try:
			s = float(values[4][:values[4].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[4][values[4].index(';')+1:])
		except ValueError:
			e = 0

		load.L = (s,e)

		# update the roof live load
		try:
			s = float(values[5][:values[5].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[5][values[5].index(';')+1:])
		except ValueError:
			e = 0

		load.Lr = (s,e)

		# update the snow load
		try:
			s = float(values[6][:values[6].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[6][values[6].index(';')+1:])
		except ValueError:
			e = 0

		load.S = (s,e)

		# update the rain load
		try:
			s = float(values[7][:values[7].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[7][values[7].index(';')+1:])
		except ValueError:
			e = 0

		load.R = (s,e)

		# update the wind load
		try:
			s = float(values[8][:values[8].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[8][values[8].index(';')+1:])
		except ValueError:
			e = 0

		load.W = (s,e)

		# update the earthquake load
		try:
			s = float(values[9][:values[9].index(';')])
		except ValueError:
			s = 0

		try:
			e = float(values[9][values[9].index(';')+1:])
		except ValueError:
			e = 0

		load.E = (s,e)

		# update the plot
		self.plotter.updateDistLoads(
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
		self.plotter.updateDistLoads(
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

		# calculate the start and end locations of the load as a
		# percentage of the member length
		startLocation = self.members.loadLocationStart_Var.get()
		endLocation = self.members.loadLocationEnd_Var.get()

		try:
			self.members.loadLocationStart_Var2.set(
				round(l*float(startLocation)/100,2)
			)

		except ValueError:
			self.members.loadLocationStart_Var2.set('0.0')

		try:
			self.members.loadLocationEnd_Var2.set(
				round(l*float(endLocation)/100,2)
			)

		except ValueError:
			self.loadLocationEnd.set('100')

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
		self.plotter.updateDistLoads(
			self.model,
			self.loadCombination.get()
		)
	
	def updateLoadStartLocation(self, *args):
		# identify the user selected load
		index, load = self.returnLoad()

		# identify the user defined load location
		length = self.members.mbrLength_Var.get()
		location = self.members.loadLocationStart_Var.get()

		# update the load location in feet combobox
		try:
			self.members.loadLocationStart_Var2.set(
				round(float(length)*float(location)/100,2)
			)

		except ValueError:
			self.members.loadLocationStart_Var2.set('0.0')

		# update the load location
		load.location = (location, load.location[1])

		# update the table
		values = self.table.item(index)['values']
		e = values[10][values[10].index(';')+1:].strip()
		values[10] = '{s} ; {e}'.format(s=location,e=e)
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updateDistLoads(
			self.model,
			self.loadCombination.get()
		)

	def updateLoadEndLocation(self, *args):
		# identify the user selected load
		index, load = self.returnLoad()

		# identify the user defined load location
		length = self.members.mbrLength_Var.get()
		location = self.members.loadLocationEnd_Var.get()

		# update the load location in feet combobox
		try:
			self.members.loadLocationEnd_Var2.set(
				round(float(length)*float(location)/100,2)
			)

		except ValueError:
			self.members.loadLocationEnd_Var2.set('0.0')

		# update the load location
		load.location = (load.location[0], location)

		# update the table
		values = self.table.item(index)['values']
		s = values[10][:values[10].index(';')].strip()
		values[10] = '{s} ; {e}'.format(s=s,e=location)
		self.table.item(index, values = values)

		# update the plot
		self.plotter.updateDistLoads(
			self.model,
			self.loadCombination.get()
		)
		
	def close(self):
		self.parent.destroy()