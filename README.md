# OpenSTRAN

[![PyPI version](https://img.shields.io/pypi/v/OpenSTRAN.svg)](https://pypi.org/project/OpenSTRAN)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/OpenSTRAN.svg)]()
[![PyPI monthly downloads](https://img.shields.io/pypi/dm/OpenSTRAN.svg)](https://pypi.org/project/OpenSTRAN/)
[![Downloads (pepy)](https://pepy.tech/badge/OpenSTRAN)](https://pepy.tech/project/OpenSTRAN)



Open-Source Structural Analysis with Python

* Version 0.0.5 - Alpha Release

## Installation
```
$ pip install OpenSTRAN
```

## Dependencies

OpenSTRAN depends on the following packages:
* <a href="https://numpy.org/">numpy</a> - used for vector and matrix mathematical operations.

It is recommended to install these dependencies which may be done using the following command.
```
pip install numpy
```

## Capabilities

OpenSTRAN allows for the creation of simple two-dimensional frame elements and complex three-dimensional structures alike.

* 2D truss :heavy_check_mark:
* 3D truss :heavy_check_mark:
* 2D frame :heavy_check_mark:
* 3D space frame :heavy_check_mark:

## Limitations
* First order elastic analysis only.
* Shear and torsional deformations are not considered.
* Does not take advantage of matrix sparseness or bandedness.
* Supports Imperial units only.

## What happened to the UI?
The graphical user interface that was programmed in tkinter and relied on matplotlib as a backend has been removed and is no longer being maintained or further developed.

Instead, focus has been shifted to improving the core library, developing documentation, and standardizing output in the <a href="https://vtk.org/">VTK</a> legacy format so that solutions can be visualized using open source post processing visualization tools such as <a href="https://www.paraview.org/">ParaView</a>.

 The UI was last available in <a href="https://pypi.org/project/OpenSTRAN/0.0.4/">Version 0.0.4</a> and can be installed with the following command.
```bash
pip install OpenSTRAN==0.0.4
```

## Get Involved

If you would like to contribute to the development of OpenSTRAN, you are encouraged to get involved. Below are some simple ways that you can begin contributing. Keep in mind that this is not an exhaustive list and that contributions can be as simple as reporting an error if you find one, sharing your experience with the library or suggesting the addition of a feature you would like to see.

* Help potential users learn OpenSTRAN by creating examples.
* Create documentation for portions of the code base.
* Validate output by comparing results with known solutions.
* Develop features by issuing a pull request.
* Increase readability of source code through refactoring and commenting.

All contributions are welcome and done on a voluntary basis.

## Quickstart Example

Below is a simple example that will help you get started using OpenSTRAN. The example consists of a simply supported beam subject to a point load.


```python
from OpenSTRAN.model import Model

# instantiate an empty model
simpleBeam = Model()

# create a node located at the origin
N1 = simpleBeam.nodes.addNode(0,0,0,'N1') # (X [ft], Y [ft], Z[ft], name)

# create a node 10 feet away from the origin along the global X axis.
N2 = simpleBeam.nodes.addNode(10,0,0,'N2') # (X [ft], Y [ft], Z[ft], name)

# restrain the nodes from translation.
N1.restraint = [1,1,1,0,0,0] # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
N2.restraint = [1,1,1,0,0,0] # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

# define a member between nodes N1 and N2.
M1 = simpleBeam.members.addMember(N1, N2) # (i node, j node)

# add a dead load of -10 kips in the global Y direction 50% along M1's span.
simpleBeam.loads.addPointLoad(M1, direction='Y', D=-10, location=50)
```