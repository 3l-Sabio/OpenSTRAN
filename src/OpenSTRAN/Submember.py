from .Node import Node
from .Units import VERTICAL_TOLERANCE

import numpy as np

from math import sqrt

from dataclasses import dataclass, field, asdict

from typing import Any


@dataclass(slots=True)
class SubMember():
    """A 3D space-frame submember between mesh nodes.

    A discretized sub-element between two mesh nodes containing geometry,
    section properties, and methods to build local and geometric stiffness matrices.

    Parameters:
        node_i (Node): Start node of the submember.
        node_j (Node): End node of the submember.
        i_release (list[int]): DOF releases at the start node.
        j_release (list[int]): DOF releases at the end node.
        E (float): Young's modulus.
        Ixx (float): Moment of inertia about the strong axis.
        Iyy (float): Moment of inertia about the weak axis.
        A (float): Cross-sectional area.
        G (float): Shear modulus.
        J (float): Polar moment of inertia.
        ENAs (dict[str, list[float]]): Equivalent nodal actions.
        results (dict[str, list[float]]): Analysis results storage.
        length (float): Submember length in inches (computed).
        rotation_matrix (np.ndarray): Rotation matrix from local to global coordinates.
        transformation_matrix (np.ndarray): Transformation matrix for coordinate conversion.
        Kl_unreleased (np.ndarray): Local elastic stiffness matrix before the
            end releases are condensed.
        Kl (np.ndarray): Local stiffness matrix.
    """
    node_i: Node
    node_j: Node
    i_release: list[int]
    j_release: list[int]
    E: float
    Ixx: float
    Iyy: float
    A: float
    G: float
    J: float
    ENAs: dict[str, list[float]] = field(
        default_factory=dict[str, list[float]])
    results: dict[str, list[float]] = field(
        default_factory=dict[str, list[float]])
    length: float = field(init=False)
    rotation_matrix: np.ndarray = field(init=False)
    transformation_matrix: np.ndarray = field(init=False)
    Kl_unreleased: np.ndarray = field(init=False)
    Kl: np.ndarray = field(init=False)
    w_major: list[float] = field(init=False)
    w_minor: list[float] = field(init=False)
    second_order_axial: float = field(init=False)

    def properties(self) -> dict[str, Any]:
        """Return all submember properties as a dictionary.

        Converts the dataclass instance into a dictionary representation containing
        all field names and their current values.

        Returns:
            dict[str, Any]: Dictionary containing all member attributes and their values.
        """
        return asdict(self)

    def __post_init__(self) -> None:
        """Initialize a SubMember instance.

        Calculates geometric properties and initializes equivalent nodal actions (ENAs)
        and results dictionaries.
        """
        self.ENAs = {
            'axial': [0, 0],
            'shear': [0, 0],
            'transverse shear': [0, 0],
            'torsional moments': [0, 0],
            'minor axis moments': [0, 0],
            'major axis moments': [0, 0]
        }
        self.results: dict[str, list[float]] = {
            'displacements': [],
            'axial': [],
            'shear': [],
            'transverse shear': [],
            'torsional moments': [],
            'minor axis moments': [],
            'major axis moments': []
        }
        # Local distributed-load intensities [i-end, j-end], in kips per inch,
        # in the member's major (local y) and minor (local z) bending planes.
        # Populated when distributed loads are applied; used to evaluate exact
        # internal forces along the span.
        self.w_major = [0.0, 0.0]
        self.w_minor = [0.0, 0.0]
        # Axial force (j end, tension positive) whose geometric stiffness was
        # included in the last analysis; zero after a first-order analysis.
        # It adds the P-delta moment to the internal forces along the span.
        self.second_order_axial = 0.0
        # calculate the member length based on the node coordinates
        self.length = self.calculate_length(self.node_i, self.node_j)

        # determine the transformation matrix for the member from the
        # member local coordinates to a global reference frame
        self.rotation_matrix = self.build_rotation_matrix(
            self.node_i,
            self.node_j
        )

        self.transformation_matrix = self.rotation_matrix.T

        # calculate the member local stiffness matrix
        self.Kl_unreleased = self.build_stiffness_matrix(
            self.E,
            self.Ixx,
            self.Iyy,
            self.A,
            self.G,
            self.J,
            self.length
        )

        # release DoFs
        self.Kl = self.pin(self.Kl_unreleased)

    def _deflection_polynomial(self, axis: str) -> tuple[float, float, float]:
        """Coefficients (a1, a2, a3) of the transverse displacement, relative
        to the i end, as a cubic in x along the submember.

        Uses the Hermite shape functions of the geometric stiffness matrix
        (McGuire et al., Eq. 9.13), so that the P-delta moment it gives is
        consistent with the recovered end forces. ``axis`` is 'major' (local
        y displacement, rotation about local z) or 'minor' (local z
        displacement, rotation about local y).

        At a released end the submember's rotation is not the node's. It is
        the rotation at which the released end force vanishes under the
        tangent stiffness of the analysis, the one the end forces were
        recovered with. A bar released at both ends therefore stays straight
        between its ends.
        """
        d = np.asarray(self.results['displacements'], dtype=float)
        M = self._release_map(
            self.Kl_unreleased
            + self.build_geometric_stiffness_matrix(self.second_order_axial))
        if M is not None:
            d = d - M @ d
        l = self.length
        if axis == 'major':
            v1, t1, v2, t2 = d[1], d[5], d[7], d[11]
        else:
            # A positive rotation about local y gives a negative slope dw/dx.
            v1, t1, v2, t2 = d[2], -d[4], d[8], -d[10]
        a1 = t1
        a2 = (3*(v2 - v1) - (2*t1 + t2)*l)/l**2
        a3 = (2*(v1 - v2) + (t1 + t2)*l)/l**3
        return float(a1), float(a2), float(a3)

    def _p_delta_moment(self, x: float, axis: str) -> float:
        """Moment of the axial force about the deflected axis, N (v(x) - v1).

        Zero unless the last analysis was second order.
        """
        N = self.second_order_axial
        if N == 0:
            return 0.0
        a1, a2, a3 = self._deflection_polynomial(axis)
        return N*(a1*x + a2*x**2 + a3*x**3)

    def moment_major(self, x: float) -> float:
        """Internal major-axis bending moment at local position x.

        Evaluates the exact closed-form moment by superposing the i-end member
        forces with the span load. After a second-order analysis it adds the
        moment of the axial force about the deflected axis, interpolated with
        the cubic shape functions of the geometric stiffness.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Bending moment in kip-inches.
        """
        l = self.length
        m1 = self.results['major axis moments'][0]
        v1 = self.results['shear'][0]
        w1, w2 = self.w_major
        return (m1 - v1*x - w1*x**2/2 - (w2 - w1)*x**3/(6*l)
                - self._p_delta_moment(x, 'major'))

    def shear_major(self, x: float) -> float:
        """Internal major-axis shear force at local position x.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Shear force in kips.
        """
        l = self.length
        v1 = self.results['shear'][0]
        w1, w2 = self.w_major
        return v1 + w1*x + (w2 - w1)*x**2/(2*l)

    def moment_minor(self, x: float) -> float:
        """Internal minor-axis bending moment at local position x.

        Evaluates the exact closed-form moment by superposing the i-end member
        forces with the span load. After a second-order analysis it adds the
        moment of the axial force about the deflected axis, interpolated with
        the cubic shape functions of the geometric stiffness.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Bending moment in kip-inches.
        """
        l = self.length
        m1 = self.results['minor axis moments'][0]
        v1 = self.results['transverse shear'][0]
        w1, w2 = self.w_minor
        return (m1 + v1*x + w1*x**2/2 + (w2 - w1)*x**3/(6*l)
                + self._p_delta_moment(x, 'minor'))

    def shear_minor(self, x: float) -> float:
        """Internal minor-axis transverse shear at local position x.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Shear force in kips.
        """
        l = self.length
        v1 = self.results['transverse shear'][0]
        w1, w2 = self.w_minor
        return v1 + w1*x + (w2 - w1)*x**2/(2*l)

    def force_extrema(self) -> dict[str, tuple[float, float]]:
        """Return the (max, min) internal force in each component over the span.

        Moment and shear extrema are found analytically. Moment peaks where
        dM/dx (shear) is zero. Axial force and torsion are constant along
        the submember, so their extrema are the end values.

        Returns:
            dict[str, tuple[float, float]]: Mapping of result key to (max, min).
        """
        l = self.length

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
        vy1 = self.results['shear'][0]
        vz1 = self.results['transverse shear'][0]

        # Moment extrema: the ends plus any point where dM/dx is zero. In a
        # first-order analysis that is where the shear is zero; after a
        # second-order analysis the slope also carries the P-delta term
        # N (a1 + 2 a2 x + 3 a3 x^2), with the same sign for both axes.
        N = self.second_order_axial
        ay1, ay2, ay3 = self._deflection_polynomial(
            'major') if N else (0, 0, 0)
        az1, az2, az3 = self._deflection_polynomial(
            'minor') if N else (0, 0, 0)
        xs_Mz = [0.0, l] + roots(
            (wy2 - wy1)/(2*l) + 3*N*ay3, wy1 + 2*N*ay2, vy1 + N*ay1)
        xs_My = [0.0, l] + roots(
            (wz2 - wz1)/(2*l) + 3*N*az3, wz1 + 2*N*az2, vz1 + N*az1)

        # Shear extrema: the ends plus the point where the load intensity is zero.
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

        def ext(func, xs: list[float]) -> tuple[float, float]:
            vals = [float(func(x)) for x in xs]
            return (max(vals), min(vals))

        # Axial and torsion are not considered to vary along the submember;
        # therefore, the extrema are considered the end values.
        axial_vals = [
            float(self.results['axial'][0]),
            float(-self.results['axial'][1])
        ]
        torque_vals = [
            float(self.results['torsional moments'][0]),
            float(-self.results['torsional moments'][1])
        ]

        return {
            'axial': (max(axial_vals), min(axial_vals)),
            'torsional moments': (max(torque_vals), min(torque_vals)),
            'shear': ext(self.shear_major, xs_Vy),
            'transverse shear': ext(self.shear_minor, xs_Vz),
            'major axis moments': ext(self.moment_major, xs_Mz),
            'minor axis moments': ext(self.moment_minor, xs_My),
        }

    def calculate_length(self, node_i: Node, node_j: Node) -> float:
        """Compute Euclidean length between two nodes.

        Args:
            node_i (Node): Start node.
            node_j (Node): End node.

        Returns:
            float: Length between ``node_i`` and ``node_j``.
        """
        # calculate the difference in vector components of the member
        dv = node_j.coordinates.vector - node_i.coordinates.vector
        # calculate and return the member length
        return float(np.linalg.norm(dv))

    def build_rotation_matrix(self, node_i: Node, node_j: Node) -> np.ndarray:
        """Build the rotation/transformation matrix for the submember.

        Establishes the local x,y,z unit vectors using a Gram-Schmidt
        approach and constructs the transformation matrix between the
        local element frame and the global frame.

        Args:
            node_i (Node): Start node.
            node_j (Node): End node.

        Returns:
            np.ndarray: Transformation matrix mapping local DOFs to global DOFs.
        """
        # assign nodal coordinates to a local variable for readability
        ix = node_i.coordinates.x
        iy = node_i.coordinates.y
        iz = node_i.coordinates.z
        jx = node_j.coordinates.x
        jy = node_j.coordinates.y
        jz = node_j.coordinates.z

        # Calculate the x, y, and z vector components of the member
        dx = jx - ix
        # dy = jy - iy (this does not appear to be used)
        dz = jz - iz

        # Check if the member is oriented vertically and, if so, offset the
        # member nodes by one unit in the negative global x direction to
        # define the local x-y plane.
        if (abs(dx) < VERTICAL_TOLERANCE and abs(dz) < VERTICAL_TOLERANCE):
            i_offset = np.array([ix-1, iy, iz])
            j_offset = np.array([jx-1, jy, jz])

        # Otherwise, the member is not oriented vertically and instead,
        # the member nodes must be offset by one unit in the positive
        # global y direction to define local x-y plane.
        else:
            i_offset = np.array([ix, iy+1, iz])
            j_offset = np.array([jx, jy+1, jz])

        # determine the local x-vector and unit x-vector of the member
        # in the global reference frame
        local_x_vector = node_j.coordinates.vector - node_i.coordinates.vector
        local_x_unit = local_x_vector/self.length

        # determine the local y-vector and unit y-vector of the member
        # in the global reference frame. This calculation requires the
        # definition of a reference point that lies in the local x-y
        # plane in order to utilize the Gram-Schmidt process vector.
        node_k = i_offset + 0.5*(j_offset-i_offset)
        vector_in_plane = node_k-node_i.coordinates.vector
        # local y-vector in global RF (Gram-Schmidt)
        local_y_vector = vector_in_plane - \
            np.dot(vector_in_plane, local_x_unit)*local_x_unit
        # Length of local y-vector
        magY = sqrt(
            local_y_vector[0]**2 + local_y_vector[1]**2 + local_y_vector[2]**2)
        # Local unit vector defining the local y-axis
        local_y_unit = local_y_vector/magY

        # Local z-vector in global RF using matrix cross product
        # Local unit vector defining the local z-axis
        local_z_unit = np.cross(local_x_unit, local_y_unit)
        # combine reference frame into a standard rotation matrix for
        # the element x,y,z => columns 1,2,3
        rotation_matrix = np.array(
            [local_x_unit, local_y_unit, local_z_unit,]).T

        # populate the rotation matrix with the proper values
        transformation_matrix = np.zeros((12, 12))
        transformation_matrix[0:3, 0:3] = rotation_matrix
        transformation_matrix[3:6, 3:6] = rotation_matrix
        transformation_matrix[6:9, 6:9] = rotation_matrix
        transformation_matrix[9:12, 9:12] = rotation_matrix

        return (transformation_matrix)

    def build_stiffness_matrix(self, E: float, Izz: float, Iyy: float, A: float, G: float, J: float, l: float) -> np.ndarray:
        l = float(l)
        # beam element (fixed at i and j nodes)
        return np.array(
            [
                [
                    E*A/l,
                    0,
                    0,
                    0,
                    0,
                    0,
                    -E*A/l,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                [
                    0,
                    12*E*Izz/l**3,
                    0,
                    0,
                    0,
                    6*E*Izz/l**2,
                    0,
                    -12*E*Izz/l**3,
                    0,
                    0,
                    0,
                    6*E*Izz/l**2
                ],
                [
                    0,
                    0,
                    12*E*Iyy/l**3,
                    0,
                    -6*E*Iyy/l**2,
                    0,
                    0,
                    0,
                    -12*E*Iyy/l**3,
                    0,
                    -6*E*Iyy/l**2,
                    0
                ],
                [
                    0,
                    0,
                    0,
                    G*J/l,
                    0,
                    0,
                    0,
                    0,
                    0,
                    -G*J/l,
                    0,
                    0
                ],
                [
                    0,
                    0,
                    -6*E*Iyy/l**2,
                    0,
                    4*E*Iyy/l,
                    0,
                    0,
                    0,
                    6*E*Iyy/l**2,
                    0,
                    2*E*Iyy/l,
                    0
                ],
                [
                    0,
                    6*E*Izz/l**2,
                    0,
                    0,
                    0,
                    4*E*Izz/l,
                    0,
                    -6*E*Izz/l**2,
                    0,
                    0,
                    0,
                    2*E*Izz/l
                ],
                [
                    -E*A/l,
                    0,
                    0,
                    0,
                    0,
                    0,
                    E*A/l,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                [
                    0,
                    -12*E*Izz/l**3,
                    0,
                    0,
                    0,
                    -6*E*Izz/l**2,
                    0,
                    12*E*Izz/l**3,
                    0,
                    0,
                    0,
                    -6*E*Izz/l**2
                ],
                [
                    0,
                    0,
                    -12*E*Iyy/l**3,
                    0,
                    6*E*Iyy/l**2,
                    0,
                    0,
                    0,
                    12*E*Iyy/l**3,
                    0,
                    6*E*Iyy/l**2,
                    0
                ],
                [
                    0,
                    0,
                    0,
                    -G*J/l,
                    0,
                    0,
                    0,
                    0,
                    0,
                    G*J/l,
                    0,
                    0
                ],
                [
                    0,
                    0,
                    -6*E*Iyy/l**2,
                    0,
                    2*E*Iyy/l,
                    0,
                    0,
                    0,
                    6*E*Iyy/l**2,
                    0,
                    4*E*Iyy/l,
                    0
                ],
                [
                    0,
                    6*E*Izz/l**2,
                    0,
                    0,
                    0,
                    2*E*Izz/l,
                    0,
                    -6*E*Izz/l**2,
                    0,
                    0,
                    0,
                    4*E*Izz/l
                ]
            ], dtype=float
        )

    def _release_matrix(self) -> np.ndarray:
        """Diagonal 12x12 matrix with ones at the released local DOFs."""
        return np.diag(np.concatenate([
            np.asarray(self.i_release, dtype=float).ravel(),
            np.asarray(self.j_release, dtype=float).ravel(),
        ]))

    def _release_map(self, K: np.ndarray) -> np.ndarray | None:
        """Static condensation operator of the released DOFs.

        For a 12x12 local matrix K of the unreleased submember, returns
        ``M = pinv(G K G) G K``, in which G selects the released DOFs, or
        None if nothing is released. ``(I - M) d`` replaces the released
        components of the end displacements d by those at which the
        released end forces vanish, the submember's own end displacements.
        Every condensation of the submember is formed from it:
        ``pin(K) = K - K M``, and a fixed-end force vector f condenses to
        ``f - M^T f``.

        Args:
            K (np.ndarray): 12x12 local matrix of the unreleased submember.

        Returns:
            np.ndarray | None: The 12x12 operator M, or None.
        """
        G = self._release_matrix()
        if not G.any():
            return None
        return np.linalg.pinv(G @ K @ G) @ G @ K

    def pin(self, Kl: np.ndarray) -> np.ndarray:
        """Statically condense the released DOFs out of a local matrix.

        Args:
            Kl (np.ndarray): 12x12 local matrix of the unreleased submember.

        Returns:
            np.ndarray: The condensed 12x12 matrix, with zero rows and columns
            at the released DOFs (a copy of Kl if nothing is released).
        """
        M = self._release_map(Kl)
        if M is None:
            return Kl.copy()
        return Kl - Kl @ M

    def pin_vector(self, f: np.ndarray) -> np.ndarray:
        """Statically condense the released DOFs out of a local force vector.

        The fixed-end forces of a load on the unreleased submember are
        condensed with its elastic stiffness, consistently with ``Kl``: the
        forces that the released ends cannot carry are redistributed to the
        other degrees of freedom.

        Args:
            f (np.ndarray): Local fixed-end force vector (12 rows) of the
                unreleased submember.

        Returns:
            np.ndarray: The condensed vector, zero at the released DOFs (a
            copy of f if nothing is released).
        """
        M = self._release_map(self.Kl_unreleased)
        if M is None:
            return f.copy()
        return f - M.T @ f

    def tangent_stiffness(self, Fx2: float) -> np.ndarray:
        """Local tangent stiffness matrix for a given axial force.

        The elastic and geometric stiffness matrices are added before the end
        releases are condensed out. Condensing the sum is what gives a bar
        released at both ends the geometric stiffness of an axial force
        member (McGuire et al., Eq. 9.9).

        Args:
            Fx2 (float): Axial force at the j end in local coordinates,
                positive in tension.

        Returns:
            np.ndarray: 12x12 tangent stiffness matrix in local coordinates.
        """
        return self.pin(
            self.Kl_unreleased + self.build_geometric_stiffness_matrix(Fx2))

    def tangent_difference(self, Fx2_from: float, Fx2_to: float) -> np.ndarray:
        """Change in the local tangent stiffness between two axial forces.

        Returns ``tangent_stiffness(Fx2_from) - tangent_stiffness(Fx2_to)``.
        Without end releases (pins), the difference is 
        ``kg(Fx2_from - Fx2_to)``. With end releases, the difference is 
        ``T_from^T kg(Fx2_from - Fx2_to) T_to``, with ``T = I - M`` formed from
        each uncondensed tangent stiffness (see ``_release_map``).

        Args:
            Fx2_from (float): Axial force at the j end, positive in tension.
            Fx2_to (float): Axial force at the j end, positive in tension.

        Returns:
            np.ndarray: 12x12 matrix in local coordinates.
        """
        dkg = self.build_geometric_stiffness_matrix(Fx2_from - Fx2_to)
        Ke = self.Kl_unreleased
        M_from = self._release_map(
            Ke + self.build_geometric_stiffness_matrix(Fx2_from))
        if M_from is None:
            return dkg
        M_to = self._release_map(
            Ke + self.build_geometric_stiffness_matrix(Fx2_to))
        assert M_to is not None
        return (np.eye(12) - M_from).T @ dkg @ (np.eye(12) - M_to)

    def geometric_stiffness(self, Fx2: float) -> np.ndarray:
        """Local geometric stiffness matrix for an elastic critical load.

        The matrix of ``build_geometric_stiffness_matrix`` without its axial
        terms.

        Released DOFs are condensed with the elastic stiffness: the result is
        ``T^T kg T``, where ``T`` gives the released end displacements of the
        condensed elastic submember. This keeps the matrix linear in Fx2, as
        the eigenproblem requires. For a bar released at both ends it is
        exactly the axial force member matrix of Eq. 9.9 (McGuire et al.).

        Args:
            Fx2 (float): Axial force at the j end in local coordinates,
                positive in tension.

        Returns:
            np.ndarray: 12x12 geometric stiffness matrix in local coordinates.
        """
        kg = self.build_geometric_stiffness_matrix(Fx2)
        kg[np.ix_([0, 6], [0, 6])] = 0.0
        M = self._release_map(self.Kl_unreleased)
        if M is None:
            return kg
        T = np.eye(12) - M
        return T.T @ kg @ T

    def build_geometric_stiffness_matrix(self, Fx2: float) -> np.ndarray:
        """Geometric stiffness matrix of an unreleased submember.

        The matrix of McGuire et al., Eq. 9.14, extended to three dimensions
        with the torsional terms of Eq. 9.17. This yields the three-dimensional
        geometric stiffness matrix presented in Eq. 9.18 (McGuire et al.).

        End moment terms presented in Eq. 9.18 (McGuire et al.) are excluded,
        and the polar moment of inertia is taken as Ixx + Iyy.

        Args:
            Fx2 (float): Axial force at the j end in local coordinates,
                positive in tension.

        Returns:
            np.ndarray: 12x12 geometric stiffness matrix in local coordinates.
        """
        A = self.A
        Ip = self.Ixx + self.Iyy
        L = float(self.length)
        # Torsional coefficient of Eq. 9.17.
        T = Fx2*Ip/(A*L)

        # beam element (fixed at i and j nodes)
        return np.array(
            [
                [
                    Fx2/L,
                    0,
                    0,
                    0,
                    0,
                    0,
                    -Fx2/L,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                [
                    0,
                    6*Fx2/(5*L),
                    0,
                    0,
                    0,
                    Fx2/10,
                    0,
                    -6*Fx2/(5*L),
                    0,
                    0,
                    0,
                    Fx2/10
                ],
                [
                    0,
                    0,
                    6*Fx2/(5*L),
                    0,
                    -Fx2/10,
                    0,
                    0,
                    0,
                    -6*Fx2/(5*L),
                    0,
                    -Fx2/10,
                    0
                ],
                [
                    0,
                    0,
                    0,
                    T,
                    0,
                    0,
                    0,
                    0,
                    0,
                    -T,
                    0,
                    0
                ],
                [
                    0,
                    0,
                    -Fx2/10,
                    0,
                    2*Fx2*L/15,
                    0,
                    0,
                    0,
                    Fx2/10,
                    0,
                    -Fx2*L/30,
                    0
                ],
                [
                    0,
                    Fx2/10,
                    0,
                    0,
                    0,
                    2*Fx2*L/15,
                    0,
                    -Fx2/10,
                    0,
                    0,
                    0,
                    -Fx2*L/30
                ],
                [
                    -Fx2/L,
                    0,
                    0,
                    0,
                    0,
                    0,
                    Fx2/L,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                [
                    0,
                    -6*Fx2/(5*L),
                    0,
                    0,
                    0,
                    -Fx2/10,
                    0,
                    6*Fx2/(5*L),
                    0,
                    0,
                    0,
                    -Fx2/10
                ],
                [
                    0,
                    0,
                    -6*Fx2/(5*L),
                    0,
                    Fx2/10,
                    0,
                    0,
                    0,
                    6*Fx2/(5*L),
                    0,
                    Fx2/10,
                    0
                ],
                [
                    0,
                    0,
                    0,
                    -T,
                    0,
                    0,
                    0,
                    0,
                    0,
                    T,
                    0,
                    0
                ],
                [
                    0,
                    0,
                    -Fx2/10,
                    0,
                    -Fx2*L/30,
                    0,
                    0,
                    0,
                    Fx2/10,
                    0,
                    2*Fx2*L/15,
                    0
                ],
                [
                    0,
                    Fx2/10,
                    0,
                    0,
                    0,
                    -Fx2*L/30,
                    0,
                    -Fx2/10,
                    0,
                    0,
                    0,
                    2*Fx2*L/15
                ]
            ], dtype=float
        )
