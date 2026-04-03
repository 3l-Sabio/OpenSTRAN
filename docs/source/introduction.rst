Introduction
============

OpenSTRAN is an open-source structural analysis library written in Python. It provides a Python library that allows for the creation and analysis of two- and three-dimensional structural frames.

Capabilities
------------

OpenSTRAN allows for the creation of simple two-dimensional frame elements and complex three-dimensional structures alike.

* 2D truss ✅
* 3D truss ✅
* 2D frame ✅
* 3D space frame ✅
* AISC steel section library ✅

Limitations
-----------

* First order elastic analysis only.
* Shear and torsional deformations are not considered.
* Does not take advantage of matrix sparseness or bandedness.
* Supports Imperial units only.

In Development
--------------

* Second order non-linear analysis.
* Browser supported user interface.
* Steel utilization checks per the ANSI/AISC 360 standard.