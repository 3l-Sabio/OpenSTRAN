# OpenSTRAN

[![PyPI version](https://img.shields.io/pypi/v/OpenSTRAN.svg)](https://pypi.org/project/OpenSTRAN)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/OpenSTRAN.svg)]()
[![PyPI monthly downloads](https://img.shields.io/pypi/dm/OpenSTRAN.svg)](https://pypi.org/project/OpenSTRAN/)
[![Downloads (pepy)](https://pepy.tech/badge/OpenSTRAN)](https://pepy.tech/project/OpenSTRAN)
![Read the Docs](https://img.shields.io/readthedocs/OpenSTRAN)

Open-Source Structural Analysis with Python

* Version 0.0.5 - Alpha Release

## Installation
```
$ pip install OpenSTRAN
```

## Requirements

* Python 3.14 or higher

## Dependencies

OpenSTRAN depends on the following packages:
* <a href="https://scipy.org/">scipy</a> - used for linear algebra routines in the solver.
* <a href="https://numpy.org/">numpy</a> - used for vector and matrix mathematical operations.

Both of these dependencies are automatically installed by default when you run `pip install OpenSTRAN`.

## Documentation

<a href="https://openstran.readthedocs.io">Read the Docs!</a>

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
The graphical user interface that was programmed using <a href=https://tkdocs.com/shipman/>Tkinter</a> and <a href=https://matplotlib.org/stable/plot_types/basic/plot.html>matplotlib</a> as a backend has been removed and is no longer being further developed. It was slow, not portable across operating systems, and overall a poor implementation for real time structural modeling.

Instead, focus has been shifted to improving the core library, developing documentation, and standardizing output so that a better user interface can be built in the future. Currently, future development of the user interface is planned to be done using HTML, CSS, and Javascript so that an operating system independent solution can be run natively in any web browser.

 The Tkinter based UI was last available in <a href="https://pypi.org/project/OpenSTRAN/0.0.4/">Version 0.0.4</a> and can be installed with the following command.
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

See <a href="CONTRIBUTING.md">CONTRIBUTING.md</a> for how to set up a development environment, where dependencies are declared, how to run the test suite, and the branch naming, commit message and pull request conventions this project follows.

## Quickstart Example

Below is a simple example that will help you get started using OpenSTRAN. The example consists of a simply supported beam subject to a point load.


```python
from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape

# instantiate an empty model
model = Model()

# create a node located at the origin
N1 = model.nodes.add_node(0, 0, 0)  # (X [ft], Y [ft], Z[ft])

# create a node 10 feet away from the origin along the global X axis.
N2 = model.nodes.add_node(10, 0, 0)  # (X [ft], Y [ft], Z[ft])

# restrain the nodes from translation.
N1.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node
N2.restraint = [1, 1, 1, 0, 0, 0]  # [Ux, Uy, Uz, φx, φy, φz] -> pinned node

# define steel constants
E = 29000  # ksi - modulus of elasticity for steel
G = 12000  # ksi - shear modulus for steel

# import W12x14 member properties from the database
s = Shape("W12X14")

M1 = model.members.add_member(N1, N2, shape=s)

# add a load of -1 kips per lineal foot in the global Y direction along M1's span.
M1.add_distributed_load(-1, -1, 'Y', 0, 100)

# solve the model.
model.solve()

# perform post processing steps on the model
model.max_deflection()

# print the nodal reactions to the terminal.
model.reactions()
```
```bash
Nodal Reactions
        Node 1:
                Rx = 0.00 kips
                Ry = 5.00 kips
                Rz = 0.00 kips
                Mx = 0.00 kip-ft
                My = 0.00 kip-ft
                Mz = 0.00 kip-ft
        Node 2:
                Rx = 0.00 kips
                Ry = 5.00 kips
                Rz = 0.00 kips
                Mx = 0.00 kip-ft
                My = 0.00 kip-ft
                Mz = 0.00 kip-ft


```
