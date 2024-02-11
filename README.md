# OpenSTRAN
# Version 0.0.4 - Alpha Release

Open Source Structural Analysis in Python

## Installation
```
$ pip install OpenSTRAN
```

## Capabilities

OpenStruct allows for the creation of simple two-dimensional frame elements
and complex three-dimensional structures alike.

* 2D truss :heavy_check_mark:
* 3D truss :heavy_check_mark:
* 2D frame :heavy_check_mark:
* 3D space frame :heavy_check_mark:
* Interactive diagrams :heavy_check_mark:

## Limitations
* First order elastic analysis only.
* Shear and torsional deformations are not considered.

Second order analysis methods are under development for a future release.

## Example
Simply supported beam subject to a point load.
```python
from OpenSTRAN.model import Model

simpleBeam = Model()

N1 = simpleBeam.nodes.addNode(0,0,0,'N1')
N2 = simpleBeam.nodes.addNode(10,0,0,'N2')

N1.restraint = [1,1,1,0,0,0]
N2.restraint = [1,1,1,0,0,0]

M1 = simpleBeam.members.addMember(N1, N2)

simpleBeam.loads.addPointLoad(M1, direction='Y', D=-10, location=50)

simpleBeam.plot()
```
![](Images/simpleBeam.png)
![](Images/Reactions.png)
![](Images/ShearDiagram.png)
![](Images/MomentDiagram.png)
![](Images/Deflection.png)