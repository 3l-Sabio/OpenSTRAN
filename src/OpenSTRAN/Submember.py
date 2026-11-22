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
        results (dict[str, list[float]]): Analysis results storage: the end
            displacements and end forces of the last solve, and the
            distributed-load intensities it applied (``w_major`` and
            ``w_minor``, i end and j end, in kips per inch, in the major
            (local y) and minor (local z) planes).
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
    results: dict[str, list[float]] = field(
        default_factory=dict[str, list[float]])
    length: float = field(init=False)
    rotation_matrix: np.ndarray = field(init=False)
    transformation_matrix: np.ndarray = field(init=False)
    Kl_unreleased: np.ndarray = field(init=False)
    Kl: np.ndarray = field(init=False)
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

        Calculates geometric properties and initializes the results
        dictionary.
        """
        self.results: dict[str, list[float]] = {
            'displacements': [],
            'axial': [],
            'shear': [],
            'transverse shear': [],
            'torsional moments': [],
            'minor axis moments': [],
            'major axis moments': [],
            'w_major': [],
            'w_minor': []
        }
        # Axial force (j end, tension positive) whose geometric stiffness was
        # included in the last analysis; zero after a first-order analysis.
        # Copied into the results, where it adds the P-delta moment to the
        # internal forces along the span.
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

    def deflection_polynomials(
        self, displacements: np.ndarray, axial: float
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Coefficients (a1, a2, a3) of the transverse displacements,
        relative to the i end, as cubics in x along the submember.

        Uses the Hermite shape functions of the geometric stiffness matrix
        (McGuire et al., Eq. 9.13), so that the P-delta moment they give is
        consistent with the recovered end forces.

        At a released end the submember's rotation is not the node's. It is
        the rotation at which the released end force vanishes under the
        tangent stiffness of the analysis, the one the end forces were
        recovered with. A bar released at both ends therefore stays straight
        between its ends.

        Args:
            displacements (np.ndarray): The 12 end displacements in local
                coordinates.
            axial (float): Axial force (j end, tension positive) of the
                tangent stiffness the end forces were recovered with.

        Returns:
            tuple: The coefficients in the major plane (local y displacement,
            rotation about local z) and in the minor plane (local z
            displacement, rotation about local y).
        """
        d = np.asarray(displacements, dtype=float).reshape(-1)
        M = self._release_map(
            self.Kl_unreleased + self.build_geometric_stiffness_matrix(axial))
        if M is not None:
            d = d - M @ d
        l = self.length

        def cubic(v1: float, t1: float, v2: float, t2: float
                  ) -> tuple[float, float, float]:
            a2 = (3*(v2 - v1) - (2*t1 + t2)*l)/l**2
            a3 = (2*(v1 - v2) + (t1 + t2)*l)/l**3
            return float(t1), float(a2), float(a3)

        # A positive rotation about local y gives a negative slope dw/dx.
        return (cubic(d[1], d[5], d[7], d[11]),
                cubic(d[2], -d[4], d[8], -d[10]))

    # Temporary: the old result methods, until they are removed. Each
    # evaluates the results of the submember's current state.

    def moment_major(self, x: float) -> float:
        """Major-axis bending moment at local position x, in kip-inches; see
        ``SubMemberResult.moment``."""
        return self._result().moment(x, 'major')

    def shear_major(self, x: float) -> float:
        """Major-axis shear force at local position x, in kips; see
        ``SubMemberResult.shear``."""
        return self._result().shear(x, 'major')

    def moment_minor(self, x: float) -> float:
        """Minor-axis bending moment at local position x, in kip-inches; see
        ``SubMemberResult.moment``."""
        return self._result().moment(x, 'minor')

    def shear_minor(self, x: float) -> float:
        """Minor-axis shear force at local position x, in kips; see
        ``SubMemberResult.shear``."""
        return self._result().shear(x, 'minor')

    def force_extrema(self) -> dict[str, tuple[float, float]]:
        """(max, min) of each internal force over the span; see
        ``SubMemberResult.force_extrema``."""
        return self._result().force_extrema()

    def _p_delta_moment(self, x: float, axis: str) -> float:
        return self._result()._p_delta_moment(x, axis)

    def _result(self):
        # Imported here because the Results module imports this one.
        from .Results import SubMemberResult
        return SubMemberResult.from_submember(self)

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
