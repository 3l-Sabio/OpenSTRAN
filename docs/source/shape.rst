Shape object
============

The :class:`~OpenSTRAN.Database.Shape.Shape` class is a convenient wrapper for
steel section properties from the built-in shape database. It loads property
values automatically on construction and exposes them as attributes.

Usage
-----

1. Import the class:

   .. code-block:: python

      from OpenSTRAN.Database.Shape import Shape

2. Create an object with a section designation:

   .. code-block:: python

      s = Shape("W12X14")

3. Access common properties:

   .. code-block:: python

      weight = s.W
      area = s.A
      inertia_x = s.Ix  # second moment of area about x-axis (strong axis)
      intertia_y = s.Iy # second moment of area about y-axis (weak axis)
      raw = s._props    # database raw mapping

4. Use the generic property dictionary:

   .. code-block:: python

      all_props = s.properties()

Attributes
----------

The class dynamically sets attributes from the database columns. Example attributes
include:

- ``Type``
- ``AISC_Manual_Label``
- ``W`` (weight)
- ``A`` (cross-sectional area)
- ``d, bf, tf, tw`` (dimensions)
- ``Ix, Iy, Iz`` (second moments of area)
- ``Sx, Sy`` (section modulii)
- ``Zx, Zy`` (plastic section moduli)
- ``rx, ry, rz`` (radii of gyration)
- ``J, Cw`` (torsional/warping constants)

Additional properties are available for many steel sections. Any DB column
name is mapped to an attribute name by replacing spaces with underscores.

Notes
-----

- If the queried shape is not found, the underlying query may raise an error.
- Numeric-looking values are converted to ``float``; empty strings become ``None``.
- The raw property mapping is available as ``_props`` (dict of lists of str).
