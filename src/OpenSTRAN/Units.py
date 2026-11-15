"""Unit conventions for OpenSTRAN.

The library does not convert units. Values passed into the library must match
the reference unit system until the library is made unit agnostic.

The reference units match the shape database:

* Lengths (node coordinates, brace locations, displacements): inches
* Forces (concentrated loads, reactions): kips
* Distributed loads: kips per inch
* Moments (nodal moments, member moments, reaction moments): kip-inches
* Section and material properties: inches and ksi

Load locations along a member are given as a percentage of its length.

The constants below are the only values in the library that depend on the
unit of length. They are sized for inches.
"""

# Nodes closer together than this, along every axis, are the same node.
NODE_SNAP_TOLERANCE: float = 1.2e-5  # in

# A node is on a member's line when the cross product of the member vector and
# the vector to the node is smaller than this. The cross product is an area.
COLLINEAR_TOLERANCE: float = 1.44e-4  # in^2

# A member whose ends are closer together than this in both global X and
# global Z is treated as vertical.
VERTICAL_TOLERANCE: float = 0.012  # in

# A submember that a distributed load overlaps by less than this is treated as
# unloaded.
LOAD_OVERLAP_TOLERANCE: float = 1.2e-8  # in

# Spacing of the brace points assumed for continuous bracing.
CONTINUOUS_BRACE_SPACING: float = 12.0  # in (1-foot)
