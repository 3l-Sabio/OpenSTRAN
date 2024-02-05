import sys
import os

# Import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

class Channels(tk.Frame):
	def __init__(self, parent, query):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.query = query

		# register a command to use for validation
		self.vcmd = (self.register(self._validate), '%P')

	# Column 1
		# Define the Database Label
		self.database_Lbl = ttk.Label(
			self.parent,
			text = 'Database:'
			)

		# Display the Database Label
		self.database_Lbl.grid(
			column = 0,
			row = 0,
			columnspan = 2,
			rowspan = 2,
			sticky = ['N','S','E','W'],
			padx = [5,0],
			pady = [10,0]
			)

		# Define the Database Combobox
		self.database_Cbox = ttk.Combobox(
			self.parent,
			state = ['readonly'],
			values = ['AISC v15.0']			
			)

		# Bind the Database Combobox to the changeDatabase Function
		self.database_Cbox.bind(
			'<<ComboboxSelected>>',
			self.changeDatabase()
			)
		
		# Display the Database Combobox
		self.database_Cbox.grid(
			column = 0,
			row = 2,
			columnspan = 2,
			sticky = ['N','S','E','W'],
			padx = [5,0],
			pady = [0,0]
			)

		# Set the Default Database Combobox Selection
		self.database_Cbox.set('AISC v15.0')		

		# Define the Shape Type Label
		self.shapeType_Lbl = ttk.Label(
			self.parent,
			text = 'Shape Type:'
			)
 
		# Display the Shape Type Label
		self.shapeType_Lbl.grid(
			column = 0,
			row = 3,
			columnspan = 2,
			rowspan = 2,
			sticky = ['N','S','E','W'],
			padx = [5,0],
			pady = [10,0]
			)

		# Define Shape Type Variable
		self.shapeType = tk.StringVar()

		# Define the C-Shapes Radio Button
		self.Cshape_RBtn = ttk.Radiobutton(
			self.parent,
			text = 'C-Shapes',
			variable = self.shapeType,
			value = 'C',
			command = lambda: self.updateShapeTypeList('C')
			)

		# Display the C-Shapes Radio Button
		self.Cshape_RBtn.grid(
			column = 0,
			row = 5,
			columnspan = 2,
			rowspan = 2,
			sticky = ['N','S','E','W'],
			padx = [5,0],
			pady = [5,5]
			)

		# Define the MC-Shapes Radio Button
		self.MCshape_RBtn = ttk.Radiobutton(
			self.parent,
			text = 'MC-Shapes',
			variable = self.shapeType,
			value = 'MC',
			command = lambda: self.updateShapeTypeList('MC')
			)

		# Display the MC-Shapes Radio Button
		self.MCshape_RBtn.grid(
			column = 0,
			row = 7,
			columnspan = 2,
			rowspan = 2,
			sticky = ['N','S','E','W'],
			padx = [5,0],
			pady = [5,5]
			)

	# Column 2
		# Define the Shape Name Label
		self.shapeName_Lbl = ttk.Label(
			self.parent,
			text = 'Shape Name:'
			)

		# Display the Shape Name Label
		self.shapeName_Lbl.grid(
			column = 2,
			row = 0,
			columnspan = 2,
			rowspan = 2,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Shape Search Variable
		self.shapeSearch = tk.StringVar()

		# Define the Shape Search Entry Box
		self.shapeSearch_Entry = ttk.Entry(
			self.parent,
			textvariable = self.shapeSearch,
			validate='key',
			validatecommand=self.vcmd
			)

		# Display the Shape Search Entry Box
		self.shapeSearch_Entry.grid(
			column = 2,
			row = 2,
			columnspan = 2,
			rowspan = 1,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [0,0]
			)

		# Create a Frame to Hold the Shape Type List Box and Scroll Bar
		self.ListBoxFrame = ttk.Frame(self.parent)

		# Creata a Scrollbar for the Shape Type List Box
		self.ListBoxScrollbar = ttk.Scrollbar(
			self.ListBoxFrame,
			orient = 'vertical'
			)

		# Define the Shape Type List Box
		self.shapes_lbox = tk.Listbox(
			self.ListBoxFrame,
			yscrollcommand = self.ListBoxScrollbar.set,
			height = 17
			)

		# Bind the updateSelection Function to the Shape Type List Box
		self.shapes_lbox.bind(
			'<<ListboxSelect>>',
			lambda e: self.updateSelection()
			)

		# Configure the Shape List Box Scroll Bar
		self.ListBoxScrollbar.config(
			command = self.shapes_lbox.yview
			)

		# Place the Shape Type List Box Scroll Bar in the List Box Frame
		self.ListBoxScrollbar.pack(
			side = 'right',
			fill = 'y'
			)

		# Place the Shape Type List Box in the List Box Frame
		self.shapes_lbox.pack()

		# Display the Shape Type List Box Frame
		self.ListBoxFrame.grid(
			column = 2,
			row = 4,
			columnspan = 2,
			rowspan = 14,
			sticky = ['N','S','E','W'],
			padx = [15,0],
			pady = [15,0]
			)

	# Column 3
		# Define Section Property Label Frame
		sctnProp_Frame = ttk.Labelframe(
			self.parent,
			text = 'Section Properties'
			)

		# Display the Section Property Label Frame
		sctnProp_Frame.grid(
				column = 5,
				row = 0,
				columnspan = 4,
				rowspan = 14,
				sticky = ['S'],
				padx = [15,0],
				pady = [10,0]
			)

		# Define the Area Label
		self.Area_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Area, A'
			)

		# Display the Area Label
		self.Area_Lbl.grid(
			column = 3,
			row = 2,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Depth Label
		self.Depth_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Depths, d'
			)

		# Display the Depth Label
		self.Depth_Lbl.grid(
			column = 3,
			row = 4,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Web Thickness Label
		self.Tw_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Web Thickness, tw'
			)

		# Display the Web Thickness Label
		self.Tw_Lbl.grid(
			column = 3,
			row = 6,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Flange Width Label
		self.bf_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Flange Thickness, bf'
			)

		# Display the Flange Width Label
		self.bf_Lbl.grid(
			column = 3,
			row = 8,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Average Flange Thickness Label
		self.tf_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Flange Thickness, tf'
			)

		# Display the Average Flange Thickness Label
		self.tf_Lbl.grid(
			column = 3,
			row = 10,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Kdes Label
		self.Kdes_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Kdes'
			)

		# Display the Kdes Label
		self.Kdes_Lbl.grid(
			column = 3,
			row = 12,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Ixx Label
		self.Ixx_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Moment of Inertia, Ixx'
			)

		# Display the Ixx Label
		self.Ixx_Lbl.grid(
			column = 3,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Sxx Label
		self.Sxx_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Section Modulus, Sxx'
			)

		# Display the Sxx Label
		self.Sxx_Lbl.grid(
			column = 3,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the rxx Label
		self.rxx_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Radius of Gyration, rxx'
			)

		# Display the rxx Label
		self.rxx_Lbl.grid(
			column = 3,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,0]
			)

		# Define the Zxx Label
		self.Zxx_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Plastic Modulus, Zxx'
			)

		# Display the Zxx Label
		self.Zxx_Lbl.grid(
			column = 3,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [15,0],
			pady = [10,25]
			)	

	# Column 4
		# Define the Area Variable
		self.Area_Var = tk.StringVar()
		self.Area_Var.set('A')

		# Define the Area Label
		self.Area_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Area_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Area Label
		self.Area_Value.grid(
			column = 5,
			row = 2,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Depth Variable
		self.Depth_Var = tk.StringVar()
		self.Depth_Var.set('d')

		# Define the Depth Label
		self.Depth_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Depth_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Depth Label
		self.Depth_Value.grid(
			column = 5,
			row = 4,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Web Thickness Variable
		self.tw_Var = tk.StringVar()
		self.tw_Var.set('tw')

		# Define the Web Thickness Label
		self.Tw_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.tw_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Web Thickness Label
		self.Tw_Value.grid(
			column = 5,
			row = 6,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Flange Width Variable
		self.bf_Var = tk.StringVar()
		self.bf_Var.set('bf')

		# Define the Flange Width Label
		self.bf_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.bf_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Flange Width Label
		self.bf_Value.grid(
			column = 5,
			row = 8,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Average Flange Thickness Variable
		self.tf_Var = tk.StringVar()
		self.tf_Var.set('tf')

		# Define the Average Flange Thickness Label
		self.tf_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.tf_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Average Flange Thickness Label
		self.tf_Value.grid(
			column = 5,
			row = 10,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Kdes Variable
		self.Kdes_Var = tk.StringVar()
		self.Kdes_Var.set('Kdes')

		# Define the Kdes Label
		self.Kdes_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Kdes_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Kdes Label
		self.Kdes_Value.grid(
			column = 5,
			row = 12,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Ixx Variable
		self.Ixx_Var = tk.StringVar()
		self.Ixx_Var.set('Ixx')

		# Define the Ixx Label
		self.Ixx_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Ixx_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Ixx Label
		self.Ixx_Value.grid(
			column = 5,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Sxx Variable
		self.Sxx_Var = tk.StringVar()
		self.Sxx_Var.set('Sxx')

		# Define the Sxx Label
		self.Sxx_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Sxx_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Sxx Label
		self.Sxx_Value.grid(
			column = 5,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the rxx Variable
		self.rxx_Var = tk.StringVar()
		self.rxx_Var.set('rxx')

		# Define the rxx Label
		self.rxx_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.rxx_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the rxx Label
		self.rxx_Value.grid(
			column = 5,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Zxx Variable
		self.Zxx_Var = tk.StringVar()
		self.Zxx_Var.set('Zxx')

		# Define the Zxx Label
		self.Zxx_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Zxx_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Zxx Label
		self.Zxx_Value.grid(
			column = 5,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,25]
			)
	
	# Column 5
		# Define the Area Units Label
		self.AreaUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^2'
			)

		# Display the Area Label
		self.AreaUnits_Lbl.grid(
			column = 7,
			row = 2,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Depth Label
		self.DepthUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the Depth Label
		self.DepthUnits_Lbl.grid(
			column = 7,
			row = 4,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Web Thickness Units Label
		self.TwUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the Web Thickness Units Label
		self.TwUnits_Lbl.grid(
			column = 7,
			row = 6,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Flange Width Units Label
		self.bfUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the Flange Width Units Label
		self.bfUnits_Lbl.grid(
			column = 7,
			row = 8,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Flange Thickness Units Label
		self.tfUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the Flange Thickness Units Label
		self.tfUnits_Lbl.grid(
			column = 7,
			row = 10,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Kdes Units Label
		self.Kdes_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the Kdes Label
		self.Kdes_Lbl.grid(
			column = 7,
			row = 12,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Ixx Units Label
		self.IxxUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^4'
			)

		# Display the Ixx Label
		self.IxxUnits_Lbl.grid(
			column = 7,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Sxx Units Label
		self.SxxUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^3'
			)

		# Display the Sxx Label
		self.SxxUnits_Lbl.grid(
			column = 7,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the rxx Units Label
		self.rxxUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the rxx Units Label
		self.rxxUnits_Lbl.grid(
			column = 7,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Zxx Units Label
		self.ZxxUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^3'
			)

		# Display the Zxx Label
		self.ZxxUnits_Lbl.grid(
			column = 7,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,25]
			)

	# Column 6
		# Define the Iyy Label
		self.Iyy_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Iyy'
			)

		# Display the Iyy Label
		self.Iyy_Lbl.grid(
			column = 9,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [50,0],
			pady = [10,0]
			)

		# Define the Syy Label
		self.Syy_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Syy'
			)

		# Display the Syy Label
		self.Syy_Lbl.grid(
			column = 9,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [50,0],
			pady = [10,0]
			)

		# Define the ryy Label
		self.ryy_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'ryy'
			)

		# Display the ryy Label
		self.ryy_Lbl.grid(
			column = 9,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [50,0],
			pady = [10,0]
			)

		# Define the Zyy Label
		self.Zyy_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'Zyy'
			)

		# Display the Zyy Label
		self.Zyy_Lbl.grid(
			column = 9,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			sticky = ['E'],
			padx = [50,0],
			pady = [10,25]
			)


		# Set the default selection to 'C-Shapes'
		self.shapeType.set('C')
		self.updateShapeTypeList('C')

	# Column 7
		# Define the Iyy Variable
		self.Iyy_Var = tk.StringVar()
		self.Iyy_Var.set('Iyy')

		# Define the Iyy Label
		self.Iyy_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Iyy_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Iyy Label
		self.Iyy_Value.grid(
			column = 11,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Syy Variable
		self.Syy_Var = tk.StringVar()
		self.Syy_Var.set('Syy')

		# Define the Syy Label
		self.Syy_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Syy_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Syy Label
		self.Syy_Value.grid(
			column = 11,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the ryy Variable
		self.ryy_Var = tk.StringVar()
		self.ryy_Var.set('ryy')

		# Define the ryy Label
		self.ryy_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.ryy_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the ryy Label
		self.ryy_Value.grid(
			column = 11,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,0]
			)

		# Define the Zyy Variable
		self.Zyy_Var = tk.StringVar()
		self.Zyy_Var.set('Zyy')

		# Define the Zyy Label
		self.Zyy_Value = ttk.Label(
			sctnProp_Frame,
			textvariable = self.Zyy_Var,
			width = 8,
			anchor = 'center'
			)

		# Display the Zyy Label
		self.Zyy_Value.grid(
			column = 11,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			padx = [10,10],
			pady = [10,25]
			)

	# Column 8
		# Define the Iyy Units Label
		self.IyyUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^4'
			)

		# Display the Iyy Label
		self.IyyUnits_Lbl.grid(
			column = 13,
			row = 14,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Syy Units Label
		self.SyyUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^3'
			)

		# Display the Syy Label
		self.SyyUnits_Lbl.grid(
			column = 13,
			row = 16,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the ryy Units Label
		self.ryyUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in'
			)

		# Display the ryy Units Label
		self.ryyUnits_Lbl.grid(
			column = 13,
			row = 18,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,0]
			)

		# Define the Zyy Units Label
		self.ZyyUnits_Lbl = ttk.Label(
			sctnProp_Frame,
			text = 'in^3'
			)

		# Display the Zyy Label
		self.ZyyUnits_Lbl.grid(
			column = 13,
			row = 20,
			columnspan = 2,
			rowspan = 2,
			sticky = ['W'],
			padx = [0,0],
			pady = [10,25]
			)

	def changeDatabase(self):
		pass

	def updateShapeTypeList(self, shapeType):
		"""
		function to populate the Shapes List Box
		"""

		# clear the Shape Search Entry Box
		self.shapeSearch_Entry.delete(0, 'end')

		# clear the Shapes List Box values
		self.shapes_lbox.delete(0, 'end')

		# collect the relevant steel section labels by type ('M' or 'MC')
		self.shapes = self.query.Get_AISC_Manual_Labels(shapeType)

		# populate the Shapes List Box
		for shape in self.shapes:
			self.shapes_lbox.insert('end', shape)

	def updateSelection(self):
		"""
		function to update labels when user selects a section type
		"""
		
		# Store the user selected shape as a variable
		index = self.shapes_lbox.curselection()
		self.shape = self.shapes_lbox.get(index)

		# collect the relevant steel section properties		
		self.properties = self.query.Get_Section_Properties(self.shape)

		# Update Values
		self.Area_Var.set(self.properties['A'][0])
		self.Depth_Var.set(self.properties['d'][0])
		self.tw_Var.set(self.properties['tw'][0])
		self.bf_Var.set(self.properties['bf'][0])
		self.tf_Var.set(self.properties['tf'][0])
		self.Kdes_Var.set(self.properties['kdes'][0])
		self.Ixx_Var.set(self.properties['Ix'][0])
		self.Sxx_Var.set(self.properties['Sx'][0])
		self.rxx_Var.set(self.properties['rx'][0])
		self.Zxx_Var.set(self.properties['Zx'][0])
		self.Iyy_Var.set(self.properties['Iy'][0])
		self.Syy_Var.set(self.properties['Sy'][0])
		self.ryy_Var.set(self.properties['ry'][0])
		self.Zyy_Var.set(self.properties['Zy'][0])

	def _validate(self, P):
		P = P.upper()
		shapes = [shape for shape in self.shapes if P in shape]
		self.shapes_lbox.delete(0, 'end')
		for shape in shapes:
			self.shapes_lbox.insert('end', shape)
		return(True)
