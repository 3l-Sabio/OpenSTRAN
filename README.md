# OpenStruct

Open Source Structural Analysis in Python

## Installation
```
$ pip install OpenStruct
```

## Capabilities

OpenStruct allows for the creation of simple two-dimensional frame elements
and complex three-dimensional structures alike.

* 2D truss :heavy_check_mark:
* 3D truss :heavy_check_mark:
* 2D frame :heavy_check_mark:
* 3D space frame :heavy_check_mark:
* Unlimited members :heavy_check_mark:
* Unlimited loads :heavy_check_mark:

## Limitations
* First order elastic analysis only.
* Shear and torsional deformations are not considered.
* Currently supports imperial units only.

Second order analysis methods are under development for a future release.

## Example
Simply supported beam subject to a uniformly distributed load.
```python
import OpenStruct

model = OpenStruct.Model(plane='xy')

N1 = model.nodes.addNode(0,0)
N2 = model.nodes.addNode(10,0)

N1.addRestraint([1,1,1,0,0,0])
N2.addRestraint([1,1,1,0,0,0])

M1 = model.members.addMember(N1, N2)

M1.addTrapLoad(-1,-1,'Y',0,100)

model.solve()

model.plot()
```