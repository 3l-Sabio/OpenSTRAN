from .Node import Node

import numpy as np

from math import sqrt


class SubMember():
    """
    3D space-frame submember between mesh nodes.

    A thin wrapper representing a discretized sub-element between two
    mesh nodes. Contains geometry, section properties, and methods to
    build local and geometric stiffness matrices.

    Attributes:
        node_i (Node): Start node of the submember.
        node_j (Node): End node of the submember.
        i_release (bool): Release (pinned) flag at the start node.
        j_release (bool): Release (pinned) flag at the end node.
        E (float): Young's modulus.
        Ixx (float): Moment of inertia about the strong axis.
        Iyy (float): Moment of inertia about the weak axis.
        A (float): Cross-sectional area.
        G (float): Shear modulus.
        J (float): Polar moment of inertia.
        length (float): Submember length (computed).
        rotationMatrix (np.ndarray): Rotation matrix from local to global.
        Kl (np.ndarray): Local stiffness matrix.
        KG (np.ndarray): Global stiffness matrix.
    """

    def __init__(
        self,
        node_i: Node,
        node_j: Node,
        i_release: bool,
        j_release: bool,
        E: float,
        Ixx: float,
        Iyy: float,
        A: float,
        G: float,
        J: float,
    ):
        """Initialize a `SubMember`.

        :param node_i: Start node of the submember.
        :type node_i: Node
        :param node_j: End node of the submember.
        :type node_j: Node
        :param i_release: True if the start node is released (pinned).
        :type i_release: bool
        :param j_release: True if the end node is released (pinned).
        :type j_release: bool
        :param E: Young's modulus.
        :type E: float
        :param Ixx: Strong-axis moment of inertia.
        :type Ixx: float
        :param Iyy: Weak-axis moment of inertia.
        :type Iyy: float
        :param A: Cross-sectional area.
        :type A: float
        :param G: Shear modulus.
        :type G: float
        :param J: Polar moment of inertia.
        :type J: float
        """
        self.node_i = node_i
        self.node_j = node_j
        self.i_release = i_release
        self.j_release = j_release
        self.E = E
        self.Ixx = Ixx
        self.Iyy = Iyy
        self.A = A
        self.G = G
        self.J = J
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

        # calculate the member length based on the node coordinates
        self.length = self.calculate_length(node_i, node_j)

        # determine the transformation matrix for the member from the
        # member local coordinates to a global reference frame
        self.rotationMatrix = self.build_rotation_matrix(
            node_i,
            node_j,
            i_release,
            j_release
        )

        self.transformation_matrix = self.rotationMatrix.T

        # calculate the member local stiffness matrix
        self.Kl = self.build_stiffness_matrix(
            E,
            Ixx,
            Iyy,
            A,
            G,
            J,
            self.length
        )

        # calculate the member global stiffness matrix
        self.KG = self.transformation_matrix.T.dot(
            self.Kl).dot(self.transformation_matrix)

    def calculate_length(self, node_i: Node, node_j: Node) -> float:
        """
        Compute Euclidean length between two nodes.

        :param node_i: Start node.
        :type node_i: Node
        :param node_j: End node.
        :type node_j: Node
        :returns: Length between `node_i` and `node_j`.
        :rtype: float
        """
        # calculate the x, y and z vector components of the member
        dx = node_j.coordinates.x - node_i.coordinates.x
        dy = node_j.coordinates.y - node_i.coordinates.y
        dz = node_j.coordinates.z - node_i.coordinates.z
        # calculate and return the member length
        return (sqrt(dx**2 + dy**2 + dz**2))

    def build_rotation_matrix(self, node_i: Node, node_j: Node, i_release: bool, j_release: bool) -> np.ndarray:
        """
        Build the rotation/transformation matrix for the submember.

        Establishes the local x,y,z unit vectors using a Gram–Schmidt
        approach and constructs the transformation matrix between the
        local element frame and the global frame. The size of the
        returned matrix depends on release conditions.

        :param node_i: Start node.
        :type node_i: Node
        :param node_j: End node.
        :type node_j: Node
        :param i_release: Release flag at node i.
        :type i_release: bool
        :param j_release: Release flag at node j.
        :type j_release: bool
        :returns: Transformation matrix mapping local DOFs to global DOFs.
        :rtype: np.ndarray
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
        rotationMatrix = np.array(
            [local_x_unit, local_y_unit, local_z_unit,]).T

        # populate the rotation matrix with the proper values

        if i_release == False and j_release == False:
            transformation_matrix = np.zeros((12, 12))
            transformation_matrix[0:3, 0:3] = rotationMatrix
            transformation_matrix[3:6, 3:6] = rotationMatrix
            transformation_matrix[6:9, 6:9] = rotationMatrix
            transformation_matrix[9:12, 9:12] = rotationMatrix
        elif i_release == True and j_release == False:
            transformation_matrix = np.zeros((10, 10))
            transformation_matrix[0:3, 0:3] = rotationMatrix
            transformation_matrix[3, 3] = rotationMatrix[0, 0]
            transformation_matrix[4:7, 4:7] = rotationMatrix
            transformation_matrix[7:10, 7:10] = rotationMatrix
        elif i_release == False and j_release == True:
            transformation_matrix = np.zeros((10, 10))
            transformation_matrix[0:3, 0:3] = rotationMatrix
            transformation_matrix[3:6, 3:6] = rotationMatrix
            transformation_matrix[6:9, 6:9] = rotationMatrix
            transformation_matrix[9, 9] = rotationMatrix[0, 0]
        else:
            transformation_matrix = np.zeros((6, 6))
            transformation_matrix[0:3, 0:3] = rotationMatrix
            transformation_matrix[3:6, 3:6] = rotationMatrix

        return (transformation_matrix)

    def build_stiffness_matrix(self, E: float, Izz: float, Iyy: float, A: float, G: float, J: float, l: float) -> np.ndarray:
        # Convert units automatically in the future (based on units passed).
        l = float(l*12)
        if self.i_release == False and self.j_release == False:
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
        elif self.i_release == True and self.j_release == False:
            # beam element pinned at node i and fixed at node j
            return np.array(
                [
                    [
                        E*A/l,
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
                        3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        -3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        3*E*Izz/l**2
                    ],
                    [
                        0,
                        0,
                        3*E*Iyy/l**3,
                        0,
                        0,
                        0,
                        -3*E*Iyy/l**3,
                        0,
                        -3*E*Iyy/l**2,
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
                        -G*J/l,
                        0,
                        0
                    ],
                    [
                        -E*A/l,
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
                        -3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        -3*E*Izz/l**2
                    ],
                    [
                        0,
                        0,
                        -3*E*Iyy/l**3,
                        0,
                        0,
                        0,
                        3*E*Iyy/l**3,
                        0,
                        3*E*Iyy/l**2,
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
                        G*J/l,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        -3*E*Iyy/l**2,
                        0,
                        0,
                        0,
                        3*E*Iyy/l**2,
                        0,
                        3*E*Iyy/l,
                        0
                    ],
                    [
                        0,
                        3*E*Izz/l**2,
                        0,
                        0,
                        0,
                        -3*E*Izz/l**2,
                        0,
                        0,
                        0,
                        3*E*Izz/l
                    ]
                ], dtype=float
            )
        elif self.i_release == False and self.j_release == True:
            # beam element fixed at node i and pinned at node j
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
                        0
                    ],
                    [
                        0,
                        3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        3*E*Izz/l**2,
                        0,
                        -3*E*Izz/l**3,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        3*E*Iyy/l**3,
                        0,
                        -3*E*Iyy/l**2,
                        0,
                        0,
                        0,
                        -3*E*Iyy/l**3,
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
                        -G*J/l
                    ],
                    [
                        0,
                        0,
                        -3*E*Iyy/l**2,
                        0,
                        3*E*Iyy/l,
                        0,
                        0,
                        0,
                        3*E*Iyy/l**2,
                        0
                    ],
                    [
                        0,
                        3*E*Izz/l**2,
                        0,
                        0,
                        0,
                        3*E*Izz/l,
                        0,
                        -3*E*Izz/l**2,
                        0,
                        0
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
                        0
                    ],
                    [
                        0,
                        -3*E*Izz/l**3,
                        0,
                        0,
                        0,
                        -3*E*Izz/l**2,
                        0,
                        3*E*Izz/l**3,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        -3*E*Iyy/l**3,
                        0,
                        3*E*Iyy/l**2,
                        0,
                        0,
                        0,
                        3*E*Iyy/l**3,
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
                        G*J/l
                    ]
                ], dtype=float
            )
        else:
            # bar element (pinned at i and j nodes)
            # returns stiffness matrix in global coordinates

            return np.array(
                [
                    [
                        E*A/l,
                        0,
                        0,
                        -E*A/l,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        -E*A/l,
                        0,
                        0,
                        E*A/l,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                ], dtype=float
            )

    def build_geometric_stiffness_matrix(self) -> np.ndarray:
        """
        Compute the geometric (P-Delta) stiffness matrix from results.

        Uses the axial and moment results stored in `self.results` to
        assemble the geometric stiffness matrix for second-order effects.

        :returns: Geometric stiffness matrix in local element DOFs.
        :rtype: np.ndarray
        """
        # define section properties as local variables for readability
        J = self.J
        A = self.A
        L = float(self.length*12)

        # define first-order results as local variables for readability
        # Fx1 = self.results['axial'][0] # not used?
        Fx2 = self.results['axial'][1]
        # Fy1 = self.results['shear'][0] # not used?
        # Fy2 = self.results['shear'][1] # not used?
        # Fz1 = self.results['transverse shear'][0] # not used?
        # Fz2 = self.results['transverse shear'][1] # not used?
        # Mx1 = self.results['torsional moments'][0] # not used
        Mx2 = self.results['torsional moments'][1]
        My1 = self.results['minor axis moments'][0]
        My2 = self.results['minor axis moments'][1]
        Mz1 = self.results['major axis moments'][0]
        Mz2 = self.results['major axis moments'][1]

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
                    My1/L,
                    Mx2/L,
                    Fx2/10,
                    0,
                    -6*Fx2/(5*L),
                    0,
                    My2/L,
                    -Mx2/L,
                    Fx2/10
                ],
                [
                    0,
                    0,
                    6*Fx2/(5*L),
                    Mz1/L,
                    -Fx2/10,
                    Mx2/L,
                    0,
                    0,
                    -6*Fx2/(5*L),
                    Mz2/L,
                    -Fx2/10,
                    -Mx2/L
                ],
                [
                    0,
                    My1/L,
                    Mz1/L,
                    Fx2*J/(A*L),
                    (-2*Mz1-Mz2)/6,
                    (2*My1-My2)/6,
                    0,
                    -My1/L,
                    -Mz1/L,
                    -Fx2*J/(A*L),
                    (-Mz1+Mz2)/6,
                    (My1+My2)/6
                ],
                [
                    0,
                    Mx2/L,
                    -Fx2/10,
                    (-2*Mz1-Mz2)/6,
                    2*Fx2*L/15,
                    0,
                    0,
                    -Mx2/L,
                    Fx2/10,
                    (-Mz1+Mz2)/6,
                    -Fx2*L/30,
                    Mx2/2
                ],
                [
                    0,
                    Fx2/10,
                    Mx2/L,
                    (2*My1-My2)/6,
                    0,
                    2*Fx2*L/15,
                    0,
                    -Fx2/10,
                    -Mx2/L,
                    (My1+My2)/6,
                    -Mx2/2,
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
                    -My1/L,
                    -Mx2/L,
                    -Fx2/10,
                    0,
                    6*Fx2/(5*L),
                    0,
                    -My2/L,
                    Mx2/L,
                    -Fx2/10
                ],
                [
                    0,
                    0,
                    -6*Fx2/(5*L),
                    -Mz1/L,
                    Fx2/10,
                    -Mx2/L,
                    0,
                    0,
                    6*Fx2/(5*L),
                    -Mz2/L,
                    Fx2/10,
                    Mx2/L
                ],
                [
                    0,
                    My2/L,
                    Mz2/L,
                    -Fx2*J/(A*L),
                    (-Mz1+Mz2)/6,
                    (My1+My2)/6,
                    0,
                    -My2/L,
                    -Mz2/L,
                    Fx2*J/(A*L),
                    (Mz1-2*Mz2)/6,
                    (-My1-2*My2)/6
                ],
                [
                    0,
                    -Mx2/L,
                    -Fx2/10,
                    (-Mz1+Mz2)/6,
                    -Fx2*L/30,
                    -Mx2/2,
                    0,
                    Mx2/L,
                    Fx2/10,
                    (Mz1-2*Mz2)/6,
                    2*Fx2*L/15,
                    0
                ],
                [
                    0,
                    Fx2/10,
                    -Mx2/L,
                    (My1+My2)/6,
                    Mx2/2,
                    -Fx2*L/30,
                    0,
                    -Fx2/10,
                    Mx2/L,
                    (-My1-2*My2)/6,
                    0,
                    2*Fx2*L/15
                ]
            ], dtype=float
        )
