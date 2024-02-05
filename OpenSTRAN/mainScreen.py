import sys
import os

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk

# Project User Interface Imports
from .screens.shapeScreen import shapeSelector
from .screens.plotScreen import plotFrame
from .screens.nodeInputScreen import nodeInputWindow
from .screens.memberInputScreen import memberInputWindow
from .Menu import Menu


# Project Databse Imports
from .projectFiles.Database.Queries import QuerySteelDb

#model = Model()

class mainScreen():
	def __init__(self, model):
		# Define the Main Screen
		self.root = tk.Tk()

		# Set the default Main Screen Properties
		self.default(self.root)

		# Connect to The Steel Shape Database
		self.query = QuerySteelDb()

		# Define the 3D Plotter
		self.plotFrame = plotFrame(self.root)

		# Define the model
		self.model = model
		
		# Define the UI Menu
		self.Menu = Menu(self.root, self.model, self.plotFrame, shapeSelector, self.query)

		# Display the UI Menu and 3D Plotter
		self.Menu.grid(column=0, row=0, sticky=['N','S','E','W'])
		self.plotFrame.grid(column=0, row=1, sticky=['N','S','E','W'])

		# Set the plotFrame to expand with the window as it is resized
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(1, weight=1)

	def default(self, root):
		# define the Main Screen title
		title = 'OpenStruct - Open Source Structural Analysis'

		# define the path to icon assets
		icon = os.path.join(os.path.dirname(__file__), 'projectFiles', 'Icons', '3DFrame.ico')

		# define the default main screen dimensions
		screenSize = '1080x720'

		# set the Main Screen title, icon, and geometry
		root.title(title)
		root.iconbitmap(icon)
		root.geometry(screenSize)

	def openWindow(self, frame):
		sub = tk.Toplevel()
		if frame == 'shapeSelector':
			shapeSelector(sub, self.query).grid()
		elif frame == 'nodeInputWindow':
			nodeInputWindow(sub, model, self.plotFrame).grid()
		elif frame == 'MemberInputWindow':
			memberInputWindow(sub, model, self.plotFrame, shapeSelector, self.query).grid()