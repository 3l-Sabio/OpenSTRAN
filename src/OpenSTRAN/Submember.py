from .Node import Node

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
        length (float): Submember length (computed).
        rotation_matrix (np.ndarray): Rotation matrix from local to global coordinates.
        transformation_matrix (np.ndarray): Transformation matrix for coordinate conversion.
        Kl (np.ndarray): Local stiffness matrix.
        Kg (np.ndarray): Global stiffness matrix.
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
    Kl: np.ndarray = field(init=False)
    Kg: np.ndarray = field(init=False)
    w_major: list[float] = field(init=False)
    w_minor: list[float] = field(init=False)

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
        # Local distributed-load intensities [i-end, j-end] in the member's
        # major (local y) and minor (local z) bending planes. Populated when
        # distributed loads are applied; used to evaluate exact internal forces
        # along the span.
        self.w_major = [0.0, 0.0]
        self.w_minor = [0.0, 0.0]
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
        self.Kl = self.build_stiffness_matrix(
            self.E,
            self.Ixx,
            self.Iyy,
            self.A,
            self.G,
            self.J,
            self.length
        )

        # release DoFs
        self.Kl = self.pin(self.Kl)

        # calculate the member global stiffness matrix
        self.Kg = self.transformation_matrix.T.dot(
            self.Kl).dot(self.transformation_matrix)

    def moment_major(self, x: float) -> float:
        """Internal major-axis bending moment at local position x.

        Evaluates the exact closed-form moment by superposing the i-end member
        forces with the span load.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Bending moment in kip-inches.
        """
        l = self.length*12
        m1 = self.results['major axis moments'][0]
        v1 = self.results['shear'][0]
        w1, w2 = self.w_major[0]/12, self.w_major[1]/12
        return m1 - v1*x - w1*x**2/2 - (w2 - w1)*x**3/(6*l)

    def shear_major(self, x: float) -> float:
        """Internal major-axis shear force at local position x.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Shear force in kips.
        """
        l = self.length*12
        v1 = self.results['shear'][0]
        w1, w2 = self.w_major[0]/12, self.w_major[1]/12
        return v1 + w1*x + (w2 - w1)*x**2/(2*l)

    def moment_minor(self, x: float) -> float:
        """Internal minor-axis bending moment at local position x.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Bending moment in kip-inches.
        """
        l = self.length*12
        m1 = self.results['minor axis moments'][0]
        v1 = self.results['transverse shear'][0]
        w1, w2 = self.w_minor[0]/12, self.w_minor[1]/12
        return m1 - v1*x - w1*x**2/2 - (w2 - w1)*x**3/(6*l)

    def shear_minor(self, x: float) -> float:
        """Internal minor-axis transverse shear at local position x.

        Args:
            x (float): Distance from node i along the submember, in inches.

        Returns:
            float: Shear force in kips.
        """
        l = self.length*12
        v1 = self.results['transverse shear'][0]
        w1, w2 = self.w_minor[0]/12, self.w_minor[1]/12
        return v1 + w1*x + (w2 - w1)*x**2/(2*l)

    def force_extrema(self) -> dict[str, tuple[float, float]]:
        """Return the (max, min) internal force in each component over the span.

        Moment and shear extrema are found analytically, moment peaks where the
        shear is zero, shear peaks where the distributed load is zero. Axial
        force and torsion are constant along the submember, so their extrema are
        the end values.

        Returns:
            dict[str, tuple[float, float]]: Mapping of result key to (max, min).
        """
        l = self.length*12

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

        wy1, wy2 = self.w_major[0]/12, self.w_major[1]/12
        wz1, wz2 = self.w_minor[0]/12, self.w_minor[1]/12
        vy1 = self.results['shear'][0]
        vz1 = self.results['transverse shear'][0]

        # Moment extrema: the ends plus any point where the shear is zero.
        xs_Mz = [0.0, l] + roots((wy2 - wy1)/(2*l), wy1, vy1)
        xs_My = [0.0, l] + roots((wz2 - wz1)/(2*l), wz1, vz1)

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

        # Check if the member is oriented vertically and, if so, offset
        # the member nodes by one unit in the negative global x
        # direction to define the local x-y plane.
        if (abs(dx) < 0.001 and abs(dz) < 0.001):
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
        # Convert units automatically in the future (based on units passed).
        l = float(l*12)
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

    def pin(self, Kl: np.ndarray) -> np.ndarray:
        G = np.zeros((12, 12), dtype=float)

        i_release = np.asarray(self.i_release, dtype=float).ravel()
        j_release = np.asarray(self.j_release, dtype=float).ravel()

        G[np.arange(6), np.arange(6)] = i_release
        G[np.arange(6, 12), np.arange(6, 12)] = j_release

        Kl = Kl - Kl @ G @ np.linalg.pinv(G @ Kl @ G) @ G @ Kl

        return (Kl)

    def build_geometric_stiffness_matrix(self) -> np.ndarray:
        """
        Compute the geometric (P-Delta) stiffness matrix from results.

        Uses the axial and moment results stored in `self.results` to
        assemble the geometric stiffness matrix for second-order effects.

        :returns: Geometric stiffness matrix in local element DOFs.
        :rtype: np.ndarray
        """
        # define section properties as local variables for readability
        A = self.A
        Ip = self.Ixx + self.Iyy
        L = float(self.length*12)

        # define first-order results as local variables for readability
        Fx2 = self.results['axial'][1]

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
                    Ip/A,
                    0,
                    0,
                    0,
                    0,
                    0,
                    -Ip/A,
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
                    -Ip/A,
                    0,
                    0,
                    0,
                    0,
                    0,
                    Ip/A,
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
