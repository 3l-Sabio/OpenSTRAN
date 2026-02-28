from dataclasses import dataclass, field, asdict

from .Queries import QuerySteelDb


@dataclass(slots=True)
class Shape:
    """Container for section properties retrieved from the steel section DB.

    This class is a thin dataclass wrapper around the mapping returned by
    :py:meth:`QuerySteelDb.get_section_properties`. Only ``shape`` is passed
    to the constructor; during ``__post_init__`` the class queries the DB and
    dynamically creates attributes for each returned column. Column names
    containing spaces are converted to Python-friendly attribute names by
    replacing spaces with underscores (for example, the DB column
    ``"AISC Manual Label"`` becomes the attribute ``AISC_Manual_Label``).

    Numeric-looking values are converted to ``float`` when possible; empty
    strings are converted to ``None``. The original raw mapping is stored in
    ``_props`` for callers that prefer keyed access.

    Parameters
    ----------
    shape : str
        Section designation passed to the DB query (for example ``"W12X14"``).

    Attributes
    ----------
    Type : None | str
        Section family/type returned by the DB.
    EDI_Std_Nomenclature : None | str
        EDI standard nomenclature (if present).
    AISC_Manual_Label : None | str
        Label from the AISC manual.
    T_F : None | str
        Section type/flag used by the DB.
    W, self_weight : None | float
        Section weight (W) in the DB and a convenience alias ``self_weight``.
    A : None | float
        Cross-sectional area.
    d, ddet, Ht, h1, OD, bf, bfdet, B1, b2, ID : None | float
        Geometric dimensions and derived values (depths, widths, outer/inner
        diameters, etc.).
    tw, twdet, twdet_over_2, tf, tfdet, t1, tnom, tdes, kdes, kdet, k1 : None | float
        Thicknesses, tolerances and related geometric properties.
    x, y, eo, xp, yp : None | float
        Centroid and eccentricity related coordinates.
    bf_over_2tf, b_over_t, b_over_tdes, h_over_tw, h_over_tdes, D_over_t : None | float
        Slenderness and ratio parameters used in section checks.
    Ix, Zx, Sx, rx, Iy, Zy, Sy, ry, Iz, rz, Sz : None | float
        Second moments of area, section moduli and radii of gyration.
    J, Cw, C : None | float
        Torsional and warping constants.
    Wno, Sw1, Sw2, Sw3, Qf, Qw, ro, H, tana, Iw : None | float
        Miscellaneous sectional properties used in design calculations.
    zA, zB, zC, wA, wB, wC, SwA, SwB, SwC, SzA, SzB, SzC : None | float
        Section property partitions (zones A/B/C) and corresponding values.
    rts, ho, PA, PA2, PB, PC, PD, T, WGi, WGo : None | float
        Additional design-related values returned by the DB.
    _props : dict[str, list[str]]
        Raw mapping returned by :py:meth:`QuerySteelDb.get_section_properties`.

    Notes
    -----
    - Attributes are created dynamically at runtime. Static type checkers
      (Pylance, mypy) rely on the explicit attribute annotations in this
      class to provide completions and type information for commonly-used
      fields.
    - If you need a fully statically-typed representation for all DB
      columns, consider generating a typed dataclass from the DB schema at
      build time.

    Examples
    --------
    >>> s = Shape("W12X14")
    >>> s.W  # weight as a float (if present)
    14.0
    >>> s._props["W"]  # raw value(s) from the DB
    ["14.0"]
    """

    shape: str
    Type: None | str = field(init=False)
    EDI_Std_Nomenclature: None | str = field(init=False)
    AISC_Manual_Label: None | str = field(init=False)
    T_F: None | str = field(init=False)
    W: None | float = field(init=False)
    A: float = field(init=False)
    d: None | float = field(init=False)
    ddet: None | float = field(init=False)
    Ht: None | float = field(init=False)
    h1: None | float = field(init=False)
    OD: None | float = field(init=False)
    bf: None | float = field(init=False)
    bfdet: None | float = field(init=False)
    B1: None | float = field(init=False)
    b2: None | float = field(init=False)
    ID: None | float = field(init=False)
    tw: None | float = field(init=False)
    twdet: None | float = field(init=False)
    twdet_over_2: None | float = field(init=False)
    tf: None | float = field(init=False)
    tfdet: None | float = field(init=False)
    t1: None | float = field(init=False)
    tnom: None | float = field(init=False)
    tdes: None | float = field(init=False)
    kdes: None | float = field(init=False)
    kdet: None | float = field(init=False)
    k1: None | float = field(init=False)
    x: None | float = field(init=False)
    y: None | float = field(init=False)
    eo: None | float = field(init=False)
    xp: None | float = field(init=False)
    yp: None | float = field(init=False)
    bf_over_2tf: None | float = field(init=False)
    b_over_t: None | float = field(init=False)
    b_over_tdes: None | float = field(init=False)
    h_over_tw: None | float = field(init=False)
    h_over_tdes: None | float = field(init=False)
    D_over_t: None | float = field(init=False)
    Ix: float = field(init=False)
    Zx: None | float = field(init=False)
    Sx: None | float = field(init=False)
    rx: None | float = field(init=False)
    Iy: float = field(init=False)
    Zy: None | float = field(init=False)
    Sy: None | float = field(init=False)
    ry: None | float = field(init=False)
    Iz: None | float = field(init=False)
    rz: None | float = field(init=False)
    Sz: None | float = field(init=False)
    J: float = field(init=False)
    Cw: None | float = field(init=False)
    C: None | float = field(init=False)
    Wno: None | float = field(init=False)
    Sw1: None | float = field(init=False)
    Sw2: None | float = field(init=False)
    Sw3: None | float = field(init=False)
    Qf: None | float = field(init=False)
    Qw: None | float = field(init=False)
    ro: None | float = field(init=False)
    H: None | float = field(init=False)
    tana: None | float = field(init=False)
    Iw: None | float = field(init=False)
    zA: None | float = field(init=False)
    zB: None | float = field(init=False)
    zC: None | float = field(init=False)
    wA: None | float = field(init=False)
    wB: None | float = field(init=False)
    wC: None | float = field(init=False)
    SwA: None | float = field(init=False)
    SwB: None | float = field(init=False)
    SwC: None | float = field(init=False)
    SzA: None | float = field(init=False)
    SzB: None | float = field(init=False)
    SzC: None | float = field(init=False)
    rts: None | float = field(init=False)
    ho: None | float = field(init=False)
    PA: None | float = field(init=False)
    PA2: None | float = field(init=False)
    PB: None | float = field(init=False)
    PC: None | float = field(init=False)
    PD: None | float = field(init=False)
    T: None | float = field(init=False)
    WGi: None | float = field(init=False)
    WGo: None | float = field(init=False)
    _props: dict[str, list[str]] = field(init=False, repr=False)

    def __post_init__(self):
        props = QuerySteelDb().get_section_properties(self.shape)
        # store raw props
        self._props = props
        # map returned column names to single values when appropriate
        for key, value in props.items():
            val = value[0]
            # try numeric conversion when applicable
            try:
                # treat empty strings as None
                if val.strip() == "":
                    converted = None
                else:
                    converted = float(val)
            except Exception:
                converted = val
            # set attribute with a Python-friendly name (strip spaces)
            attr_name = key.replace(" ", "_")
            setattr(self, attr_name, converted)

    def properties(self) -> dict[str, str | float]:
        """Return the dataclass properties as a dictionary.

        :returns: Dictionary of this instance's fields
        :rtype: dict[str, Any]
        """
        return asdict(self)
