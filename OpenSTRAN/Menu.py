import sys

# import Tkinter
if sys.version_info[0] >= 3:
	import tkinter as tk
	from tkinter import ttk
else:
	import Tkinter as tk
	from Tkinter import ttk	

# Project User Interface Imports	
from .screens.nodeInputScreen import nodeInputWindow
from .screens.memberInputScreen import memberInputWindow
from .screens.pointLoadInputScreen import pointLoadInputWindow
from .screens.distLoadInputScreen import distLoadInputWindow
from .screens.nodeOutputScreen import nodeOutputWindow
from .screens.memberResultsScreen import memberResultsWindow

# import FEM Solver
from .fem.Model import Model as femSolver

class Menu(ttk.Notebook):
	def __init__(self, parent, model, plotFrame, shapeSelector, query, *args, **kwargs):
		ttk.Notebook.__init__(self, parent, *args, **kwargs)

		self.parent = parent
		self.model = model
		self.plotFrame = plotFrame
		self.shapeSelector = shapeSelector
		self.query = query
		self.femModels = {}
		self.loadCombinations = [
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

		self.fileFrame = ttk.Frame(self, height=50)
		self.resultsFrame = ResultsFrame(
			self,
			self.model,
			self.plotFrame,
			self.femModels
		)
		
		self.inputFrame = InputFrame(
			self,
			self.model,
			self.plotFrame,
			self.shapeSelector,
			self.query, height=50
		)

		self.add(self.fileFrame, text = 'File')
		self.add(self.inputFrame, text = 'Input')
		self.add(self.resultsFrame, text = 'Results')

		self.tab(2, state='disabled')

		self.grid(row=0, column=0, sticky='NSEW')

		self.select(self.inputFrame)

	def solve(self):
		# determine the user selected load combination
		for loadCombination in self.loadCombinations:
			print('Solving {combo}'.format(combo=loadCombination))
			self.femModels[loadCombination] = self.femModel(loadCombination)

		print('\nAll load combinations solved successfully.\n')
		
		self.tab(2, state='normal')
		self.select(self.resultsFrame)

	def femModel(self, loadCombination):
		# instantiate an FEM model
		femModel = femSolver()

		# add user defined nodes and members to the FEM model
		for mbr in self.model.members.members.values():

			# add the member i node to the FEM model
			node_i = femModel.nodes.addNode(
				mbr.node_i.x,
				mbr.node_i.y,
				mbr.node_i.z
			)

			# set the i node restraint
			node_i.restraint = mbr.node_i.restraint

			# add the member j node to the FEM model
			node_j = femModel.nodes.addNode(
				mbr.node_j.x,
				mbr.node_j.y,
				mbr.node_j.z
			)

			# set the j node restraint
			node_j.restraint = mbr.node_j.restraint

			# add the member to the FEM model
			femModel.members.addMember(
				node_i = node_i,
				node_j = node_j,
				i_release = mbr.i_release,
				j_release = mbr.j_release,
				E = mbr.E,
				Ixx = mbr.Izz,
				Iyy = mbr.Iyy,
				A = mbr.A,
				G = mbr.G,
				J = mbr.J,
				mesh = mbr.mesh,
				bracing = mbr.bracing,
				shape = mbr.shape
			)

		# add user defined point loads to the FEM model
		for load in self.model.loads.pointLoads.values():
			for mbr, member in self.model.members.members.items():
				if load.member == member:
					break

			magnitude = float(load.loadCombinations[loadCombination])
			location = float(load.location)
			direction = load.direction

			femModel.members.members[mbr].addPointLoad(
				magnitude,
				direction,
				location
			)

		# add user defined distributed loads to the FEM model
		for load in self.model.loads.distLoads.values():
			for mbr, member in self.model.members.members.items():
				if load.member == member:
					break

			Mag1 = load.loadCombinations_S[loadCombination]
			Mag2 = load.loadCombinations_E[loadCombination]
			direction = load.direction
			loc1 = float(load.location[0])
			loc2 = float(load.location[1])

			femModel.members.members[mbr].addTrapLoad(
				Mag1,
				Mag2,
				direction,
				loc1,
				loc2
			)

		# solve the FEM model
		femModel.solve()

		# return the FEM model for use by the GUI
		return(femModel)		

class FileFrame(ttk.Frame):
	def __init__(self, parnt, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

class InputFrame(ttk.Frame):
	def __init__(self, parent, model, plotter, shapeSelector, query, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.nodes = nodeFrame(self, model, plotter)
		self.members = memberFrame(self, model, plotter, shapeSelector, query)
		self.loads = loadFrame(self, model, plotter)		
		self.solver = solverFrame(self, model, plotter)

		self.nodes.grid(column=0, row=0)
		ttk.Separator(self, orient='vertical').grid(column=1,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.members.grid(column=2, row=0)
		ttk.Separator(self, orient='vertical').grid(column=3,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.loads.grid(column=4, row=0)
		ttk.Separator(self, orient='vertical').grid(column=5,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.solver.grid(column=6, row=0, sticky=['N','S','E','W'], pady=15)

class ResultsFrame(ttk.Frame):
	def __init__(self, parent, model, plotter, femModels, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)
		self.parent = parent

		self.nodalReactions = nodalReactionsFrame(self, plotter, femModels)
		self.forceDiagrams = memberForceDiagramFrame(self, plotter, femModels)
		self.deflectedShape = memberDeflectionDiagramFrame(self, plotter, femModels)
		self.detailedResults = detailedResultsFrame(self, femModels)

		self.nodalReactions.grid(column=0, row=0)
		ttk.Separator(self, orient='vertical').grid(column=1,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.forceDiagrams.grid(column=2, row=0)
		ttk.Separator(self, orient='vertical').grid(column=3,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.deflectedShape.grid(column=4, row=0)
		ttk.Separator(self, orient='vertical').grid(column=5,row=0,sticky=['N','S'],padx=[5,5],pady=[5,5])
		self.detailedResults.grid(column=6,row=0)

class nodalReactionsFrame(ttk.Frame):
	def __init__(self, parent, plotter, femModels, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.displayReactions_Var = tk.StringVar()
		self.displayReactions_Var.set('0')
		self.displayReactions = ttk.Checkbutton(
			self,
			variable = self.displayReactions_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Display Nodal Reactions',
			command = lambda: self.showReactions(plotter, femModels)
		)

		self.displayFx_Var = tk.StringVar()
		self.displayFx_Var.set('0')
		self.Fx = ttk.Checkbutton(
			self,
			variable = self.displayFx_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Fx',
			command = lambda: self.displayReaction(plotter, femModels, self.displayFx_Var, 'Fx'),
			state = 'disabled'
		)

		self.displayFy_Var = tk.StringVar()
		self.displayFy_Var.set('0')
		self.Fy = ttk.Checkbutton(
			self,
			variable = self.displayFy_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Fy',
			command = lambda: self.displayReaction(plotter, femModels, self.displayFy_Var, 'Fy'),
			state = 'disabled'
		)

		self.displayFz_Var = tk.StringVar()
		self.displayFz_Var.set('0')
		self.Fz = ttk.Checkbutton(
			self,
			variable = self.displayFz_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Fz',
			command = lambda: self.displayReaction(plotter, femModels, self.displayFz_Var, 'Fz'),
			state = 'disabled'
		)

		self.displayMx_Var = tk.StringVar()
		self.displayMx_Var.set('0')
		self.Mx = ttk.Checkbutton(
			self,
			variable = self.displayMx_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Mx',
			command = lambda: self.displayReaction(plotter, femModels, self.displayMx_Var, 'Mx'),
			state = 'disabled'
		)

		self.displayMy_Var = tk.StringVar()
		self.displayMy_Var.set('0')
		self.My = ttk.Checkbutton(
			self,
			variable = self.displayMy_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'My',
			command = lambda: self.displayReaction(plotter, femModels, self.displayMy_Var, 'My'),
			state = 'disabled'
		)

		self.displayMz_Var = tk.StringVar()
		self.displayMz_Var.set('0')
		self.Mz = ttk.Checkbutton(
			self,
			variable = self.displayMz_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Mz',
			command = lambda: self.displayReaction(plotter, femModels, self.displayMz_Var, 'Mz'),
			state = 'disabled'
		)

		self.reactionLabel = ttk.Label(
			self,
			text = 'Nodal Reactions',
			anchor = 'center',
			font = 10
		)

		self.displayReactions.grid(column=0, columnspan=2, row=0, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.Fx.grid(column=0, row=1, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.Fy.grid(column=0, row=2, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.Fz.grid(column=0, row=3, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.Mx.grid(column=1, row=1, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.My.grid(column=1, row=2, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.Mz.grid(column=1, row=3, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.reactionLabel.grid(column=0, columnspan=2, row=4, sticky=['E','W'], padx=[5,5], pady=[5,5])

	def getModel(self, femModels):
		return(femModels[
			self.parent.parent.inputFrame.loads.loadCombination_Var.get()
		])

	def displayReaction(self, plotter, femModels, display, reaction):
		femModel = self.getModel(femModels)

		if display.get() == '1':
			plotter.showReactions(femModel, reaction)
		else:
			plotter.removeReactions(femModel, reaction)	

	def removeReactions(self, plotter, femModels, reaction=None):
		loadCombination = self.parent.parent.inputFrame.loads.loadCombination_Var.get()
		femModel = femModels[loadCombination]

		plotter.removeReactions(femModel, reaction)

	def showReactions(self, plotter, femModels):
		if self.displayReactions_Var.get() == '1':
			self.activateCheckButtons()
		else:
			self.disableCheckButtons()
			self.removeReactions(plotter, femModels)

	def activateCheckButtons(self):
		self.Fx['state'] = 'active'
		self.Fy['state'] = 'active'
		self.Fz['state'] = 'active'
		self.Mx['state'] = 'active'
		self.My['state'] = 'active'
		self.Mz['state'] = 'active'

	def disableCheckButtons(self):
		self.displayFx_Var.set('0')
		self.Fx['state'] = 'disabled'
		self.displayFy_Var.set('0')
		self.Fy['state'] = 'disabled'
		self.displayFz_Var.set('0')
		self.Fz['state'] = 'disabled'
		self.displayMx_Var.set('0')
		self.Mx['state'] = 'disabled'
		self.displayMy_Var.set('0')
		self.My['state'] = 'disabled'
		self.displayMz_Var.set('0')
		self.Mz['state'] = 'disabled'

class memberForceDiagramFrame(ttk.Frame):
	def __init__(self, parent, plotter, femModels, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.selection = tk.StringVar()
		self.previousSelection = None

		self.displayMbrForces_Var = tk.StringVar()
		self.displayMbrForces_Var.set('0')

		self.displayForceDiagrams = ttk.Checkbutton(
			self,
			text = 'Display Member Force Diagrams',
			variable = self.displayMbrForces_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: self.showForceDiagrams(plotter, femModels)
		)

		self.displayAxial = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'axial',
			text = 'Axial',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.displayTorque = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'torque',
			text = 'Torque',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.displayVy = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'Vy',
			text = 'y Shear',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.displayMyy = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'Myy',
			text = 'y-y Moment',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.displayVz = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'Vz',
			text = 'z Shear',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.displayMzz = ttk.Radiobutton(
			self,
			variable = self.selection,
			value = 'Mzz',
			text = 'z-z Moment',
			state = 'disabled',
			command = lambda: self.updateSelection(plotter, femModels)
		)

		self.reactionLabel = ttk.Label(
			self,
			text = 'Member Force Diagrams',
			anchor = 'center',
			font = 10
		)

		self.displayForceDiagrams.grid(
			column=0,
			columnspan = 2,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayAxial.grid(
			column=0,
			row=1,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayTorque.grid(
			column=1,
			row=1,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayVy.grid(
			column=0,
			row=2,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayMyy.grid(column=1,
			row=2,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayVz.grid(column=0,
			row=3,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)

		self.displayMzz.grid(column=1,
			row=3,
			sticky=['E','W'],
			padx=[5,5],
			pady=[0,0]
		)
		
		self.reactionLabel.grid(column=0,
			columnspan=2,
			row=4,
			sticky=['E','W'],
			padx=[5,5],
			pady=[5,5]
		)

	def updateSelection(self, plotter, femModels):
		selection = self.selection.get()
		femModel = self.getModel(femModels)

		if self.previousSelection == None:
			pass
		else:
			if self.previousSelection == 'axial':
				plotter.removeAxial(femModel)
			if self.previousSelection == 'torque':
				plotter.removeTorque(femModel)
			if self.previousSelection == 'Vy':
				plotter.removeVy(femModel)
			if self.previousSelection == 'Vz':
				plotter.removeVz(femModel)
			if self.previousSelection == 'Mzz':
				plotter.removeMzz(femModel)
			if self.previousSelection == 'Myy':
				plotter.removeMyy(femModel)

		self.previousSelection = selection
		
		if selection == 'axial':
			plotter.showAxial(femModel)
		if selection == 'torque':
			plotter.showTorque(femModel)
		if selection == 'Vy':
			plotter.showVy(femModel)
		if selection == 'Vz':
			plotter.showVz(femModel)
		if selection == 'Mzz':
			plotter.showMzz(femModel)
		if selection == 'Myy':
			plotter.showMyy(femModel)

	def getModel(self, femModels):
		return(femModels[
			self.parent.parent.inputFrame.loads.loadCombination_Var.get()
		])

	def showForceDiagrams(self, plotter, femModels):
		if self.displayMbrForces_Var.get() == '1':
			self.activateRadioButtons()
			self.updateSelection(plotter, femModels)
		else:
			self.disableRadioButtons()
			self.updateSelection(plotter, femModels)

	def activateRadioButtons(self,):
		# enable the radio buttons
		self.displayAxial['state'] = 'active'
		self.displayTorque['state'] = 'active'
		self.displayVy['state'] = 'active'
		self.displayMyy['state'] = 'active'
		self.displayVz['state'] = 'active'
		self.displayMzz['state'] = 'active'
		# Set the default selection to the axial force diagram
		self.selection.set('axial')

	def disableRadioButtons(self):
		# deselect the user selection
		self.selection.set('None')
		# disable the radio buttons
		self.displayAxial['state'] = 'disabled'
		self.displayTorque['state'] = 'disabled'
		self.displayVy['state'] = 'disabled'
		self.displayMyy['state'] = 'disabled'
		self.displayVz['state'] = 'disabled'
		self.displayMzz['state'] = 'disabled'

class memberDeflectionDiagramFrame(ttk.Frame):
	def __init__(self, parent, plotter, femModels, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		self.displayDeflection_Var = tk.StringVar()
		self.displayDeflection_Var.set('0')

		self.displayDeflection = ttk.Checkbutton(
			self,
			variable = self.displayDeflection_Var,
			onvalue = '1',
			offvalue = '0',
			text = 'Display Deflected Shape',
			command = lambda: self.showDeflection(plotter, femModels)
		)

		self.scaleLabel = ttk.Label(
			self,
			text = 'Deflection Diagram Scale: [WIP]',
			anchor = 'w'
		)

		self.scale_Var = tk.StringVar()
		self.scale_Var.set('10')
		
		self.scaleEntryBox = ttk.Entry(
			self,
			textvariable = self.scale_Var,
			state = 'disabled'
		)

		self.deflectionLabel = ttk.Label(
			self,
			text = 'Deflected Shape',
			anchor = 'center',
			font = 10
		)

		self.displayDeflection.grid(column=0, columnspan=2, row=0, sticky=['E','W'], padx=[5,5])
		ttk.Label(self,text='').grid(column=0, columnspan=2, row=1)
		ttk.Label(self,text='').grid(column=0, columnspan=2, row=2)
		self.scaleLabel.grid(column=0, row=3, sticky=['E','W'], padx=[5,5])
		self.scaleEntryBox.grid(column=1, row=3, sticky=['E','W'], padx=[5,5])
		self.deflectionLabel.grid(column=0, columnspan=2, row=4, sticky=['E','W'], padx=[5,5], pady=[5,5])

	def getModel(self, femModels):
		return(femModels[
			self.parent.parent.inputFrame.loads.loadCombination_Var.get()
		])

	def showDeflection(self, plotter, femModels):
		femModel = self.getModel(femModels)
		if self.displayDeflection_Var.get() == '1':
			plotter.showDeformation(femModel)
		else:
			plotter.removeDeformation(femModel)



	def updateScale(self, plotter, femModels):
		pass

class detailedResultsFrame(ttk.Frame):
	def __init__(self, parent, femModels, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.parent = parent

		buttonWidth = 30

		self.nodes = ttk.Button(
			self,
			text = 'Detailed Nodal Results',
			command = lambda: self.openNodesWindow(femModels),
			width = buttonWidth
		)

		self.members = ttk.Button(
			self,
			text = 'Detailed Member Results [WIP]',
			command = lambda: self.openMembersWindow(femModels),
			width = buttonWidth,
			state = 'disabled'
		)

		self.nodes.pack()
		self.members.pack()

	def openNodesWindow(self, femModels):
		femModel = self.getModel(femModels)
		sub = tk.Toplevel()
		nodeOutputWindow(sub, femModel)

	def openMembersWindow(self, femModels):
		femModel = self.getModel(femModels)
		sub = tk.Toplevel()
		memberResultsWindow(sub, femModels)

	def getModel(self, femModels):
		return(femModels[
			self.parent.parent.inputFrame.loads.loadCombination_Var.get()
		])

class nodeFrame(ttk.Frame):
	def __init__(self, parent, model, plotter, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.displayNodes = False

		buttonWidth = 30

		self.nodes = ttk.Button(
			self,
			text = 'Node & Boundary Conditions',
			command = lambda: self.openWindow(model, plotter),
			width = buttonWidth
		)

		self.displayNodes_Var = tk.StringVar()
		self.displayNodes_Var.set('0')

		self.displayNodes = ttk.Checkbutton(
			self,
			text = 'Display Nodes',
			variable = self.displayNodes_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: self.showNodes(model, plotter)
		)

		self.displayNodeLabels_Var = tk.StringVar()
		self.displayNodeLabels_Var.set('0')

		self.displayNodeLabels = ttk.Checkbutton(
			self,
			text = 'Display Node Labels',
			variable = self.displayNodeLabels_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: plotter.showNodeLabels(model),
			width = buttonWidth,
			state = 'disabled'
		)

		self.displayRestraints_Var = tk.StringVar()
		self.displayRestraints_Var.set('0')
		
		self.displayRestraints = ttk.Checkbutton(
			self,
			text = 'Display Nodal Restraints',
			variable = self.displayRestraints_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: plotter.showRestraints(model),
			width = buttonWidth,
			state = 'disabled'
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
		self.nodes.grid(column=0, row=3, sticky=['E','W'], padx=[5,5], pady=[0,0])
		self.nodeLabel.grid(column=0, row=4, sticky=['E','W'], padx=[5,5], pady=[5,5])

	def showNodes(self, model, plotter):
		if self.displayNodes:
			self.displayNodes = False
			
			plotter.showNodes(model)

			if self.displayNodeLabels_Var.get() == '0':
				self.displayNodeLabels_Var.set('1')
				plotter.showNodeLabels(model)
			
			if self.displayRestraints_Var.get() == '0':
				self.displayRestraints_Var.set('1')
				plotter.showRestraints(model)

			self.displayNodeLabels['state'] = 'enabled'
			self.displayRestraints['state'] = 'enabled'

		else:
			self.displayNodes = True

			plotter.showNodes(model)
			plotter.showNodeLabels(model)
			plotter.showRestraints(model)

			self.displayNodeLabels_Var.set('0')
			self.displayNodeLabels['state'] = 'disabled'

			self.displayRestraints_Var.set('0')
			self.displayRestraints['state'] = 'disabled'

	def openWindow(self, model, plotter):
		sub = tk.Toplevel()
		nodeInputWindow(sub, model, plotter).grid()

class solverFrame(ttk.Frame):
	def __init__(self, parent, model, plotter, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		solveButton = ttk.Button(
			self,
			text = 'SOLVE',
			command = lambda: parent.parent.solve()
		)

		solveButton.grid(column=0, row=0, sticky=['N','S'], padx=[5,5], pady=[5,5], ipady=25)

class memberFrame(ttk.Frame):
	def __init__(
		self,
		parent,
		model,
		plotter,
		shapeSelector,
		query,
		*args,
		**kwargs
		):

		ttk.Frame.__init__(self, parent, *args, **kwargs)

		self.displayMembers = False
		buttonWidth = 30

		self.members = ttk.Button(
			self,
			text = 'Members',
			width = buttonWidth,
			command = lambda: self.openWindow(
				model,
				plotter,
				shapeSelector,
				query 
			)
		)

		self.displayMembers_Var = tk.StringVar()
		self.displayMembers_Var.set('0')

		self.displayMembers = ttk.Checkbutton(
			self,
			text = 'Display Members',
			variable = self.displayMembers_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: self.showMembers(model, plotter)
		)

		self.displayMemberLabels_Var = tk.StringVar()
		self.displayMemberLabels_Var.set('0')

		self.displayMemberLabels = ttk.Checkbutton(
			self,
			text = 'Display Member Labels',
			variable = self.displayMemberLabels_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: plotter.showMemberLabels(model),
			width = buttonWidth,
			state = 'disabled'
		)

		self.displayMemberPins_Var = tk.StringVar()
		self.displayMemberPins_Var.set('0')
		
		self.displayMemberPins = ttk.Checkbutton(
			self,
			text = 'Display Member Pins',
			variable = self.displayMemberPins_Var,
			onvalue='1',
			offvalue='0',
			command = lambda: plotter.showMemberPins(model),
			width = buttonWidth,
			state = 'disabled'
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
		self.members.grid(column=0, row=3, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		self.memberLabel.grid(column=0, row=4, sticky=['S','E','W'], padx=[5,5], pady=[5,5])

	def showMembers(self, model, plotter):
		if self.displayMembers:
			self.displayMembers = False
			
			plotter.showMembers(model)

			if self.displayMemberLabels_Var.get() == '0':
				self.displayMemberLabels_Var.set('1')
				plotter.showMemberLabels(model)
			
			if self.displayMemberPins_Var.get() == '0':
				self.displayMemberPins_Var.set('1')
				plotter.showMemberPins(model)

			self.displayMemberLabels['state'] = 'enabled'
			self.displayMemberPins['state'] = 'enabled'

		else:
			self.displayMembers = False

			plotter.showMembers(model)
			plotter.showMemberLabels(model)
			plotter.showMemberPins(model)

			self.displayMemberLabels_Var.set('0')
			self.displayMemberLabels['state'] = 'disabled'

			self.displayMemberPins_Var.set('0')
			self.displayMemberPins['state'] = 'disabled'

	def openWindow(self, model, plotter, shapeSelector, query):
		sub = tk.Toplevel()
		memberInputWindow(sub, model, plotter, shapeSelector, query)

class loadFrame(ttk.Frame):
	def __init__(self, parent, model, plotter, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		buttonWidth = 30

		# Define the Point Load Display Button
		self.pointLoadDisplay_Var = tk.StringVar()
		self.pointLoadDisplay_Var.set('0')

		displayPointLoads = ttk.Checkbutton(
			self,
			text = 'Display Point Loads',
			variable = self.pointLoadDisplay_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: plotter.showPointLoads(model, self.loadCombination_Var.get())
		)

		# Define the Distributed Load Display Button
		self.distLoadDisplay_Var = tk.StringVar()
		self.distLoadDisplay_Var.set('0')

		displayDistributedLoads = ttk.Checkbutton(
			self,
			text = 'Display Distributed Loads',
			variable = self.distLoadDisplay_Var,
			onvalue='1',
			offvalue='0',
			width = buttonWidth,
			command = lambda: plotter.showDistLoads(model, self.loadCombination_Var.get())
		)

		# Define the load combination variable
		self.loadCombination_Var = tk.StringVar()
		self.loadCombination_Var.set('Dead Load Only (D)')

		# Define the load combination Combobox
		loadCombination_Cbox = ttk.Combobox(
			self,
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
		loadCombination_Cbox.bind(
			'<<ComboboxSelected>>',
			lambda e: self.updateLoads(model, plotter, self.loadCombination_Var.get())
		)

		# Define the Point Loads Button
		pointLoads = ttk.Button(
			self,
			text = 'Point Loads',
			width = buttonWidth,
			command = lambda: self.openPointLoadWindow(model, plotter, self.loadCombination_Var)
		)

		# Define the Distributed Loads Button
		distributedLoads = ttk.Button(
			self,
			text = 'Distributed Loads',
			width = buttonWidth,
			command = lambda: self.openDistLoadWindow(model, plotter, self.loadCombination_Var)
		)

		# Define the Loads Menu Label
		loadLabel = ttk.Label(
			self,
			text = 'Loads',
			anchor = 'center',
			font = 10
		)

		# Display the Menu Widgets
		
		displayPointLoads.grid(column=0, columnspan=2, row=0, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		displayDistributedLoads.grid(column=0, columnspan=2, row=1, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		loadCombination_Cbox.grid(column=0, columnspan=2, row=2, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		pointLoads.grid(column=0, row=3, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		distributedLoads.grid(column=1, row=3, sticky=['S','E','W'], padx=[5,5], pady=[0,0])
		loadLabel.grid(column=0, columnspan = 2, row=4, sticky=['S','E','W'], padx=[5,5], pady=[5,5])

	def updateLoads(self, model, plotter, loadCombination):
		plotter.updatePointLoads(model, loadCombination)
		plotter.updateDistLoads(model, loadCombination)

	def openPointLoadWindow(self, model, plotter, loadCombination):
		sub = tk.Toplevel()
		pointLoadInputWindow(sub, model, plotter, loadCombination)

	def openDistLoadWindow(self, model, plotter, loadCombination):
		sub = tk.Toplevel()
		distLoadInputWindow(sub, model, plotter, loadCombination)

