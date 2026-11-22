from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from math import sqrt
from types import MappingProxyType

import numpy as np

from .Member import Member
from .Node import Node
from .Submember import SubMember
from .Units import CONTINUOUS_BRACE_SPACING


# End force components of a submember, in local coordinates.
FORCE_KEYS = (
    'axial',
    'shear',
    'transverse shear',
    'torsional moments',
    'minor axis moments',
    'major axis moments',
)


@dataclass(frozen=True, slots=True)
class NodeResult:
    """Displacements and reactions of one node.

    Parameters:
        Ux, Uy, Uz (float): Translations in the global X, Y and Z directions.
        phi_x, phi_y, phi_z (float): Rotations about the global X, Y and Z
            axes, in radians.
        Rx, Ry, Rz (float): Reaction forces in the global X, Y and Z
            directions; zero at an unrestrained degree of freedom.
        Rmx, Rmy, Rmz (float): Reaction moments about the global X, Y and Z
            axes; zero at an unrestrained degree of freedom.
    """
    Ux: float
    Uy: float
    Uz: float
    phi_x: float
    phi_y: float
    phi_z: float
    Rx: float
    Ry: float
    Rz: float
    Rmx: float
    Rmy: float
    Rmz: float


def _check_axis(axis: str) -> None:
    if axis not in ('major', 'minor'):
        raise ValueError(
            f"axis must be 'major' or 'minor', not {axis!r}.")


def _pair(values: Sequence[float]) -> tuple[float, float]:
    i, j = values
    return float(i), float(j)


@dataclass(frozen=True, slots=True, eq=False)
class SubMemberResult:
    """End displacements and end forces of one submember, and its internal
    forces along the span.

    Compared by identity, like the submember it belongs to.

    Parameters:
        submember (SubMember): The submember, as meshed for the analysis.
        displacements (np.ndarray): The 12 end displacements in the
            submember's local coordinates (a read-only copy).
        forces (Mapping[str, tuple[float, float]]): End forces in local
            coordinates, (i end, j end), for each key of ``FORCE_KEYS``
            (read-only). They are the forces the nodes apply to the
            submember's ends, including the fixed-end forces of span loads,
            so the axial force at the j end is positive in tension.
        w_major, w_minor (tuple[float, float]): Intensities (i end, j end)
            of the distributed load in the major (local y) and minor (local
            z) planes, in kips per inch.
        second_order_axial (float): Axial force (j end, tension positive)
            whose geometric stiffness was included in the analysis; zero
            after a first-order analysis.
    """
    submember: SubMember
    displacements: np.ndarray
    forces: Mapping[str, tuple[float, float]]
    w_major: tuple[float, float]
    w_minor: tuple[float, float]
    second_order_axial: float
    # The deflected shape in each plane, for the P-delta moment.
    _deflection: dict[str, tuple[float, float, float]] = field(
        init=False, repr=False)

    def __post_init__(self) -> None:
        # Keep read-only copies, so that neither a later solve nor the
        # caller can change the results.
        displacements = np.array(self.displacements, dtype=float).reshape(-1)
        displacements.setflags(write=False)
        object.__setattr__(self, 'displacements', displacements)
        object.__setattr__(self, 'forces', MappingProxyType(
            {key: _pair(value) for key, value in self.forces.items()}))
        object.__setattr__(self, 'w_major', _pair(self.w_major))
        object.__setattr__(self, 'w_minor', _pair(self.w_minor))
        object.__setattr__(
            self, 'second_order_axial', float(self.second_order_axial))
        major = minor = (0.0, 0.0, 0.0)
        if self.second_order_axial:
            major, minor = self.submember.deflection_polynomials(
                displacements, self.second_order_axial)
        object.__setattr__(
            self, '_deflection', {'major': major, 'minor': minor})

    def moment(self, x: float, axis: str = 'major') -> float:
        """Internal bending moment at a position along the submember.

        The exact closed-form moment of the i-end forces and the span load.
        After a second-order analysis it includes the moment of the axial
        force about the deflected axis, with the deflection interpolated by
        the cubic shape functions of the geometric stiffness.

        Args:
            x (float): Distance from the i end, in inches.
            axis (str, optional): 'major' (about local z) or 'minor' (about
                local y). Defaults to 'major'.

        Returns:
            float: Bending moment in kip-inches.

        Raises:
            ValueError: If ``axis`` is not 'major' or 'minor'.
        """
        _check_axis(axis)
        l = self.submember.length
        if axis == 'major':
            m1 = self.forces['major axis moments'][0]
            v1 = self.forces['shear'][0]
            w1, w2 = self.w_major
            return (m1 - v1*x - w1*x**2/2 - (w2 - w1)*x**3/(6*l)
                    - self._p_delta_moment(x, 'major'))
        m1 = self.forces['minor axis moments'][0]
        v1 = self.forces['transverse shear'][0]
        w1, w2 = self.w_minor
        return (m1 + v1*x + w1*x**2/2 + (w2 - w1)*x**3/(6*l)
                + self._p_delta_moment(x, 'minor'))

    def shear(self, x: float, axis: str = 'major') -> float:
        """Internal shear force at a position along the submember.

        Args:
            x (float): Distance from the i end, in inches.
            axis (str, optional): 'major' (along local y) or 'minor' (along
                local z). Defaults to 'major'.

        Returns:
            float: Shear force in kips.

        Raises:
            ValueError: If ``axis`` is not 'major' or 'minor'.
        """
        _check_axis(axis)
        l = self.submember.length
        if axis == 'major':
            v1 = self.forces['shear'][0]
            w1, w2 = self.w_major
        else:
            v1 = self.forces['transverse shear'][0]
            w1, w2 = self.w_minor
        return v1 + w1*x + (w2 - w1)*x**2/(2*l)

    def _p_delta_moment(self, x: float, axis: str) -> float:
        """Moment of the axial force about the deflected axis, N (v(x) - v1).

        Zero after a first-order analysis.
        """
        N = self.second_order_axial
        if N == 0:
            return 0.0
        a1, a2, a3 = self._deflection[axis]
        return N*(a1*x + a2*x**2 + a3*x**3)

    def force_extrema(self) -> dict[str, tuple[float, float]]:
        """The (max, min) internal force in each component over the span.

        Moment and shear extrema are found analytically. Moment peaks where
        dM/dx is zero. Axial force and torsion are constant along the
        submember, so their extrema are the end values. The values follow
        the sign convention of the i-end forces (the j-end forces with their
        sign reversed), so an axial force in tension is negative.

        Returns:
            dict[str, tuple[float, float]]: (max, min) for each key of
            ``FORCE_KEYS``.
        """
        l = self.submember.length

        def roots(a: float, b: float, c: float) -> list[float]:
            # Real roots of a*x^2 + b*x + c = 0 falling strictly within (0, L).
            candidates: list[float] = []
            if abs(a) < 1e-12:
                if abs(b) > 1e-12:
                    candidates.append(-c/b)
            else:
                disc = b*b - 4*a*c
                if disc >= 0:
                    sq = disc**0.5
                    candidates.append((-b + sq)/(2*a))
                    candidates.append((-b - sq)/(2*a))
            return [x for x in candidates if 0 < x < l]

        wy1, wy2 = self.w_major
        wz1, wz2 = self.w_minor
        vy1 = self.forces['shear'][0]
        vz1 = self.forces['transverse shear'][0]

        # Moment extrema: the ends plus any point where dM/dx is zero. In a
        # first-order analysis that is where the shear is zero; after a
        # second-order analysis the slope also carries the P-delta term
        # N (a1 + 2 a2 x + 3 a3 x^2), with the same sign for both axes.
        N = self.second_order_axial
        ay1, ay2, ay3 = self._deflection['major']
        az1, az2, az3 = self._deflection['minor']
        xs_Mz = [0.0, l] + roots(
            (wy2 - wy1)/(2*l) + 3*N*ay3, wy1 + 2*N*ay2, vy1 + N*ay1)
        xs_My = [0.0, l] + roots(
            (wz2 - wz1)/(2*l) + 3*N*az3, wz1 + 2*N*az2, vz1 + N*az1)

        # Shear extrema: the ends plus the point where the load intensity
        # is zero.
        xs_Vy = [0.0, l]
        if abs(wy2 - wy1) > 1e-12:
            xv = -wy1*l/(wy2 - wy1)
            if 0 < xv < l:
                xs_Vy.append(xv)
        xs_Vz = [0.0, l]
        if abs(wz2 - wz1) > 1e-12:
            xv = -wz1*l/(wz2 - wz1)
            if 0 < xv < l:
                xs_Vz.append(xv)

        def ext(func: Callable[[float, str], float], xs: list[float],
                axis: str) -> tuple[float, float]:
            vals = [func(x, axis) for x in xs]
            return (max(vals), min(vals))

        # Axial force and torsion do not vary along the submember, so their
        # extrema are the end values.
        axial = self.forces['axial']
        torque = self.forces['torsional moments']
        axial_vals = [axial[0], -axial[1]]
        torque_vals = [torque[0], -torque[1]]

        return {
            'axial': (max(axial_vals), min(axial_vals)),
            'torsional moments': (max(torque_vals), min(torque_vals)),
            'shear': ext(self.shear, xs_Vy, 'major'),
            'transverse shear': ext(self.shear, xs_Vz, 'minor'),
            'major axis moments': ext(self.moment, xs_Mz, 'major'),
            'minor axis moments': ext(self.moment, xs_My, 'minor'),
        }


@dataclass(frozen=True, slots=True, eq=False)
class MemberResult:
    """Results of one member.

    Compared by identity, like the member it belongs to.

    Parameters:
        member (Member): The member.
        submembers (tuple[SubMemberResult, ...]): Results of the member's
            submembers, from its i end to its j end, as meshed for the
            analysis.
    """
    member: Member
    submembers: tuple[SubMemberResult, ...]

    def _locate(self, location: float) -> tuple[SubMemberResult, float]:
        """The submember at a location along the span, and the distance (in
        inches) from its i end. A location outside the span is clamped to
        the nearer end."""
        length = self.member.length
        # Inches from node i, within the span.
        target = min(max(length*location/100, 0.0), length)
        run = 0.0
        for sub in self.submembers:
            sub_length = sub.submember.length
            if run - 1e-6 <= target <= run + sub_length + 1e-6:
                return sub, min(max(target - run, 0.0), sub_length)
            run += sub_length
        last = self.submembers[-1]
        return last, last.submember.length

    def moment(self, location: float, axis: str = 'major') -> float:
        """Internal bending moment at a location along the member.

        Evaluates the exact closed-form moment of the submember there (see
        ``SubMemberResult.moment``), between mesh nodes too.

        Args:
            location (float): Position along the span as a percentage
                (0-100%). A location outside the span is taken at the
                nearer end.
            axis (str, optional): 'major' (about local z) or 'minor' (about
                local y). Defaults to 'major'.

        Returns:
            float: Bending moment in kip-inches.

        Raises:
            ValueError: If ``axis`` is not 'major' or 'minor'.
        """
        sub, x = self._locate(location)
        return sub.moment(x, axis)

    def shear(self, location: float, axis: str = 'major') -> float:
        """Internal shear force at a location along the member.

        Args:
            location (float): Position along the span as a percentage
                (0-100%). A location outside the span is taken at the
                nearer end.
            axis (str, optional): 'major' (along local y) or 'minor' (along
                local z). Defaults to 'major'.

        Returns:
            float: Shear force in kips.

        Raises:
            ValueError: If ``axis`` is not 'major' or 'minor'.
        """
        sub, x = self._locate(location)
        return sub.shear(x, axis)

    def calculate_Cb(self) -> float:
        """Calculate the lateral-torsional buckling coefficient (Cb) for the
        member, from the major-axis moments of this analysis.

        Computes Cb based on moment variation along unbraced spans using the
        standard AISC formula: Cb = 12.5*Mmax / (2.5*Mmax + 3*Ma + 4*Mb + 3*Mc).
        The calculation accounts for lateral bracing locations and interpolates
        moments at quarter-span points. The result is limited to a maximum of
        3.0.

        Returns:
            float: The lateral-torsional buckling coefficient, limited to 3.0 maximum.

        Raises:
            ValueError: If the member's bracing is not 'continuous',
                'quarter', 'third', 'midspan' or a list of locations.
        """
        member = self.member
        # Instantiate an array to hold Cb for each unbraced span
        Cb: list[float] = []

        def discretize(length: float, n: int, l1: float = 0.0) -> list[float]:
            """Discretize span into n segments and return division points.

            Args:
                length (float): Length of span.
                n (int): Number of segments.
                l1 (float, optional): Offset location. Defaults to 0.0.

            Returns:
                list[float]: List of discretized locations.
            """            # Returns an n-sized array of locations along the member span
            locations: list[float] = []
            for i in range(n-1):
                i += 1
                locations.append(l1 + i * length / n)
            return (locations)

        def braceCoordinates(bracePoint: float) -> tuple[float, float, float]:
            """Calculate the global coordinates of a brace point along the member.

            Args:
                bracePoint (float): Distance along member span.

            Returns:
                tuple[float, float, float]: Tuple of (x, y, z) coordinates.
            """
            # Calculate the x, y and z vector components of the member
            dx = member.node_j.coordinates.x - member.node_i.coordinates.x
            dy = member.node_j.coordinates.y - member.node_i.coordinates.y
            dz = member.node_j.coordinates.z - member.node_i.coordinates.z
            # Calculate the member unit vectors
            x_unit = dx/member.length
            y_unit = dy/member.length
            z_unit = dz/member.length
            # Calculate nodal coordinates of brace point
            x = member.node_i.coordinates.x + bracePoint*x_unit
            y = member.node_i.coordinates.y + bracePoint*y_unit
            z = member.node_i.coordinates.z + bracePoint*z_unit
            # Return the brace point coordinates
            return (x, y, z)

        if member.bracing == 'continuous':
            # Continuous bracing is taken as evenly spaced brace points.
            bracePoints = discretize(
                member.length, round(member.length/CONTINUOUS_BRACE_SPACING))
        elif member.bracing == 'quarter':
            bracePoints = discretize(member.length, 4)
        elif member.bracing == 'third':
            bracePoints = discretize(member.length, 3)
        elif member.bracing == 'midspan':
            bracePoints = discretize(member.length, 2)
        else:
            if type(member.bracing) == list:
                pass
            else:
                raise ValueError(
                    "Must be 'quarter','third','midspan' or an array of locations"
                )
            bracePoints = member.bracing

        unbracedSpans = len(bracePoints) + 1

        for i in range(unbracedSpans):

            # Determine unbraced span length
            if i == 0:
                l1 = 0.0
                unbracedLength = bracePoints[i]
            elif i == len(bracePoints):
                l1 = bracePoints[i-1]
                unbracedLength = member.length - l1
            else:
                l1 = bracePoints[i-1]
                unbracedLength = bracePoints[i] - l1

            # Determine the 1/4 point locations along the unbraced span
            quarterPoints = discretize(unbracedLength, 4, l1)

            # Instantiate an empty array to hold Mmax
            moments: list[float] = []
            # Instantiate an empty array to hold Ma, Mb, and Mc
            M: list[float] = []

            # Determine the nodal coordinates of the quarter points
            for quarterPoint in quarterPoints:
                coordinates = braceCoordinates(quarterPoint)

                for sub in self.submembers:
                    submbr = sub.submember
                    ends = sub.forces['major axis moments']
                    # 1/4 point coordinates
                    x = coordinates[0]
                    y = coordinates[1]
                    z = coordinates[2]
                    # Node i coordinates
                    xi = submbr.node_i.coordinates.x
                    yi = submbr.node_i.coordinates.y
                    zi = submbr.node_i.coordinates.z
                    # Node j coordinates
                    xj = submbr.node_j.coordinates.x
                    yj = submbr.node_j.coordinates.y
                    zj = submbr.node_j.coordinates.z
                    # Determine which submembers the 1/4 point falls between
                    if (xi, yi, zi) <= coordinates <= (xj, yj, zj):
                        # Location values for linear interpolation
                        Lp: list[float] = []
                        Lp.append(0.0)
                        Lp.append(submbr.length)
                        # Moment values for linear interpolation
                        Mp: list[float] = []
                        Mp.append(ends[0])
                        Mp.append(-1*ends[1])
                        # Location for moment interpolation
                        dx = x - xi
                        dy = y - yi
                        dz = z - zi
                        L = sqrt(dx**2 + dy**2 + dz**2)
                        # Interpolate the quarter point moment value
                        M.append(abs(np.interp(L, Lp, Mp)))
                        moments.append(max(
                            abs(ends[0]),
                            abs(ends[1])
                        ))
                    else:
                        moments.append(max(
                            abs(ends[0]),
                            abs(ends[1])
                        ))
            # Calculate Cb
            Mmax = max(moments)
            Ma = M[0]
            Mb = M[1]
            Mc = M[2]
            Cb.append(12.5*Mmax/(2.5*Mmax + 3*Ma + 4*Mb + 3*Mc))

        return float(min(min(Cb), 3))


class Results:
    """Results of one analysis, as returned by ``Model.solve()``.

    The results do not change after the analysis: a later solve of the same
    model returns a new object.

    Parameters:
        members (tuple[MemberResult, ...]): Results of each member, in the
            order the members were added.
        second_order (bool): Whether the analysis was second order.
        iterations (int): Number of iterations of a second-order analysis;
            0 for a first-order analysis.

    Maxima, each the largest absolute value over the model: reactions
    ``Rx_max``, ``Ry_max``, ``Rz_max``, ``Rmx_max``, ``Rmy_max``,
    ``Rmz_max``; translations ``Ux_max``, ``Uy_max``, ``Uz_max``; member
    forces ``axial_max``, ``torque_max``, ``Vy_max``, ``Vz_max``,
    ``Mzz_max``, ``Myy_max``. Member force maxima include the peaks between
    the ends of each submember.
    """

    def __init__(
        self,
        nodes: list[Node],
        displacements: np.ndarray,
        reactions: np.ndarray,
        members: list[MemberResult],
        second_order: bool,
        iterations: int,
    ) -> None:
        """Store the results of an analysis.

        Args:
            nodes: The nodes of the model, in degree-of-freedom order.
            displacements: Global displacement vector (6 per node).
            reactions: Global reaction vector (6 per node), zero at the
                unrestrained degrees of freedom.
            members: Results of each member.
            second_order: Whether the analysis was second order.
            iterations: Iterations of a second-order analysis.
        """
        self._nodes = tuple(nodes)
        self._U = np.array(displacements, dtype=float).reshape(-1)
        self._R = np.array(reactions, dtype=float).reshape(-1)
        self._U.setflags(write=False)
        self._R.setflags(write=False)
        self._members = {id(m.member): m for m in members}
        # The largest magnitude of each member force component, between the
        # ends of the submembers too.
        self._force_peaks = {key: 0.0 for key in FORCE_KEYS}
        for member in members:
            for sub in member.submembers:
                for key, values in sub.force_extrema().items():
                    self._force_peaks[key] = max(
                        self._force_peaks[key], *(abs(v) for v in values))
        self._second_order = second_order
        self._iterations = iterations

    def __repr__(self) -> str:
        kind = 'second-order' if self.second_order else 'first-order'
        return (f"<Results: {kind}, {len(self._nodes)} nodes, "
                f"{len(self._members)} members>")

    @property
    def second_order(self) -> bool:
        return self._second_order

    @property
    def iterations(self) -> int:
        return self._iterations

    @property
    def nodes(self) -> tuple[Node, ...]:
        """The nodes of the analysis, in order."""
        return self._nodes

    @property
    def members(self) -> tuple[MemberResult, ...]:
        return tuple(self._members.values())

    def node(self, node: Node) -> NodeResult:
        """Displacements and reactions of a node.

        Args:
            node (Node): A node of the analysed model.

        Returns:
            NodeResult: The node's results.

        Raises:
            KeyError: If the node was not part of the analysis.
        """
        k = node.node_ID - 1
        if not (0 <= k < len(self._nodes) and self._nodes[k] is node):
            raise KeyError(
                f"Node {node.node_ID} was not part of this analysis.")
        U = self._U[6*k:6*k + 6]
        R = self._R[6*k:6*k + 6]
        return NodeResult(*(float(v) for v in U), *(float(v) for v in R))

    def member(self, member: Member) -> MemberResult:
        """Results of a member.

        Args:
            member (Member): A member of the analysed model.

        Returns:
            MemberResult: The member's results.

        Raises:
            KeyError: If the member was not part of the analysis.
        """
        result = self._members.get(id(member))
        if result is None or result.member is not member:
            raise KeyError("The member was not part of this analysis.")
        return result

    def _max_abs(self, values: np.ndarray) -> float:
        return float(np.max(np.abs(values), initial=0.0))

    @property
    def Rx_max(self) -> float:
        return self._max_abs(self._R[0::6])

    @property
    def Ry_max(self) -> float:
        return self._max_abs(self._R[1::6])

    @property
    def Rz_max(self) -> float:
        return self._max_abs(self._R[2::6])

    @property
    def Rmx_max(self) -> float:
        return self._max_abs(self._R[3::6])

    @property
    def Rmy_max(self) -> float:
        return self._max_abs(self._R[4::6])

    @property
    def Rmz_max(self) -> float:
        return self._max_abs(self._R[5::6])

    @property
    def Ux_max(self) -> float:
        return self._max_abs(self._U[0::6])

    @property
    def Uy_max(self) -> float:
        return self._max_abs(self._U[1::6])

    @property
    def Uz_max(self) -> float:
        return self._max_abs(self._U[2::6])

    @property
    def axial_max(self) -> float:
        return self._force_peaks['axial']

    @property
    def torque_max(self) -> float:
        return self._force_peaks['torsional moments']

    @property
    def Vy_max(self) -> float:
        return self._force_peaks['shear']

    @property
    def Vz_max(self) -> float:
        return self._force_peaks['transverse shear']

    @property
    def Mzz_max(self) -> float:
        return self._force_peaks['major axis moments']

    @property
    def Myy_max(self) -> float:
        return self._force_peaks['minor axis moments']
