# OpenStruct

Open Source Structural Analysis and Design

## Installation
```
$ pip install ...
```

## Capabilities

* 2D truss :heavy_check_mark:
* 3D truss :heavy_check_mark:
* 2D frame :heavy_check_mark:
* 3D space frame :heavy_check_mark:

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
```