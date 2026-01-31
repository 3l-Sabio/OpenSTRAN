from .Nodes import Nodes
from .Node import Node
from .Submember import SubMember
import numpy as np
from math import sqrt

from typing import Any

from dataclasses import dataclass, field, asdict


@dataclass(slots=True)
class Member():
    """
    Represents a 3D space frame member connecting two nodes.

    A member is a structural element that connects two nodes and can be discretized into
    submembers for analysis. It supports various boundary conditions, material properties,
    and loading conditions.

    :ivar nodes: Reference to the Nodes collection object.
    :vartype nodes: Nodes
    :ivar node_i: Start node of the member.
    :vartype node_i: Node
    :ivar node_j: End node of the member.
    :vartype node_j: Node
    :ivar i_release: Boundary condition at node i (False = fixed/pinned, True = pinned).
    :vartype i_release: bool
    :ivar j_release: Boundary condition at node j (False = fixed/pinned, True = pinned).
    :vartype j_release: bool
    :ivar E: Young's modulus in ksi.
    :vartype E: float
    :ivar Ixx: Strong axis moment of inertia in in^4.
    :vartype Ixx: float
    :ivar Iyy: Weak axis moment of inertia in in^4.
    :vartype Iyy: float
    :ivar A: Cross-sectional area in in^2.
    :vartype A: float
    :ivar G: Shear modulus in ksi.
    :vartype G: float
    :ivar J: Polar moment of inertia in in^4.
    :vartype J: float
    :ivar mesh: Number of discretizations (submembers) along the member span.
    :vartype mesh: int
    :ivar bracing: Lateral bracing configuration. Can be 'continuous', 'quarter', 'third',
                   'midspan', or a list of bracing locations along the span.
    :vartype bracing: str | list[float]
    :ivar shape: Cross-sectional shape identifier.
    :vartype shape: str
    :ivar length: Calculated length of the member (in).
    :vartype length: float
    :ivar Cb: Lateral-torsional buckling coefficient.
    :vartype Cb: float
    :ivar count: Counter for submember creation.
    :vartype count: int
    :ivar submembers: Dictionary of submembers indexed by creation order.
    :vartype submembers: dict[int, SubMember]
    """

    nodes: Nodes
    node_i: Node
    node_j: Node
    i_release: bool
    j_release: bool
    E: float
    Ixx: float
    Iyy: float
    A: float
    G: float
    J: float
    mesh: int
    bracing: str | list[float]
    shape: str
    length: float = field(init=False)
    Cb: float = field(init=False)
    count: int = 0
    submembers: dict[int, SubMember] = field(
        default_factory=dict[int, SubMember])

    def __post_init__(self) -> None:
        """
        Initialize the member after dataclass instantiation.

        Calculates the member length and discretizes the member into submembers
        based on the specified mesh parameter. Creates connectivity between
        submembers using intermediate mesh nodes.

        :returns: None
        :rtype: None
        """
        # Calculate the member length based on the node coordinates
        self.length = self.calculate_length(self.node_i, self.node_j)

        j: Node = self.node_i
        for i, node in enumerate(
            self.add_mesh(self.nodes, self.node_i,
                          self.node_j, self.mesh, self.length)
        ):
            if i+1 == 1:
                i = self.node_i
                j = node

                self.add_submember(
                    i,
                    j,
                    self.i_release,
                    False,
                    self.E,
                    self.Ixx,
                    self.Iyy,
                    self.A,
                    self.G,
                    self.J)

            elif i+1 < self.mesh:
                i = j
                j = node

                self.add_submember(
                    i,
                    j,
                    False,
                    False,
                    self.E,
                    self.Ixx,
                    self.Iyy,
                    self.A,
                    self.G,
                    self.J
                )

            else:
                i = j
                j = self.node_j

                self.add_submember(
                    i,
                    j,
                    False,
                    self.j_release,
                    self.E,
                    self.Ixx,
                    self.Iyy,
                    self.A,
                    self.G,
                    self.J
                )

    def calculate_length(self, node_i: Node, node_j: Node) -> float:
        """
        Calculate the length of the member using the Euclidean distance formula.

        Computes the 3D distance between two nodes based on their coordinate
        positions in the global reference frame.

        :param node_i: Start node of the member.
        :type node_i: Node
        :param node_j: End node of the member.
        :type node_j: Node
        :returns: The length of the member in inches.
        :rtype: float
        """
        # Calculate the x, y and z vector components of the member
        dx = node_j.coordinates.x - node_i.coordinates.x
        dy = node_j.coordinates.y - node_i.coordinates.y
        dz = node_j.coordinates.z - node_i.coordinates.z
        # Calculate and return the member length
        return (sqrt(dx**2 + dy**2 + dz**2))

    def properties(self) -> dict[str, Any]:
        """
        Return all member properties as a dictionary.

        Converts the dataclass instance into a dictionary representation containing
        all field names and their current values.

        :returns: Dictionary containing all member attributes and their values.
        :rtype: dict[str, Any]
        """
        return asdict(self)

    def add_mesh(self, nodes: Nodes, node_i: Node, node_j: Node, mesh: int, l: float) -> list[Node]:
        """
        Create intermediate mesh nodes along the member span.

        Generates evenly spaced nodes along the member length based on the mesh
        parameter. These nodes are used as intermediary connection points for
        submembers in the discretization process.

        :param nodes: Collection of nodes in the model.
        :type nodes: Nodes
        :param node_i: Start node of the member.
        :type node_i: Node
        :param node_j: End node of the member.
        :type node_j: Node
        :param mesh: Number of equal segments to divide the member into.
        :type mesh: int
        :param l: Total length of the member in inches.
        :type l: float
        :returns: List of intermediate mesh nodes along the member.
        :rtype: list[Node]
        """
        # Instantiate an array to hold the mesh nodes
        mesh_nodes: list[Node] = []
        # Calculate the x, y and z vector components of the member
        dx = node_j.coordinates.x - node_i.coordinates.x
        dy = node_j.coordinates.y - node_i.coordinates.y
        dz = node_j.coordinates.z - node_i.coordinates.z
        # Calculate the member unit vectors
        x_unit = dx/l
        y_unit = dy/l
        z_unit = dz/l
        # Add the mesh to the model
        for i in range(mesh):
            # Calculate the scalar
            scalar = l/mesh*(i+1)
            # Calculate nodal coordinates of mesh point
            x = node_i.coordinates.x + scalar*x_unit
            y = node_i.coordinates.y + scalar*y_unit
            z = node_i.coordinates.z + scalar*z_unit
            # Add the mesh coordinates as a node to the model
            mesh_nodes.append(nodes.add_node(x, y, z, mesh_node=True))
        # Return a list of the mesh nodes
        return (mesh_nodes)

    def add_submember(
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
        J: float
    ) -> None:
        """
        Add a submember to the member collection.

        Creates a new submember element connecting two nodes with specified
        boundary conditions and material properties. The submember is stored
        in the submembers dictionary using an auto-incremented counter.

        :param node_i: Start node of the submember.
        :type node_i: Node
        :param node_j: End node of the submember.
        :type node_j: Node
        :param i_release: Release condition at start node (False = fixed, True = pinned).
        :type i_release: bool
        :param j_release: Release condition at end node (False = fixed, True = pinned).
        :type j_release: bool
        :param E: Young's modulus in ksi.
        :type E: float
        :param Ixx: Strong axis moment of inertia in in^4.
        :type Ixx: float
        :param Iyy: Weak axis moment of inertia in in^4.
        :type Iyy: float
        :param A: Cross-sectional area in in^2.
        :type A: float
        :param G: Shear modulus in ksi.
        :type G: float
        :param J: Polar moment of inertia in in^4.
        :type J: float
        :returns: None
        :rtype: None
        """
        self.count += 1
        submbr = SubMember(
            node_i,
            node_j,
            i_release,
            j_release,
            E,
            Ixx,
            Iyy,
            A,
            G,
            J
        )
        self.submembers[self.count] = submbr

    def calculate_Cb(self) -> float:
        """
        Calculate the lateral-torsional buckling coefficient (Cb) for the member.

        Computes Cb based on moment variation along unbraced spans using the
        standard AISC formula: Cb = 12.5*Mmax / (2.5*Mmax + 3*Ma + 4*Mb + 3*Mc).
        The calculation accounts for lateral bracing locations and interpolates
        moments at quarter-span points. The result is limited to a maximum of 3.0.

        :returns: The lateral-torsional buckling coefficient, limited to 3.0 maximum.
        :rtype: float
        """
        # Instantiate an array to hold Cb for each unbraced span
        Cb: list[float] = []

        def discretize(length: float, n: int, l1: float = 0.0) -> list[float]:
            """Discretize span into n segments and return division points.

            :param length: Length of span.
            :type length: float
            :param n: Number of segments.
            :type n: int
            :param l1: Offset location.
            :type l1: float
            :returns: List of discretized locations.
            :rtype: list[float]
            """
            # Returns an n-sized array of locations along the member span
            locations: list[float] = []
            for i in range(n-1):
                i += 1
                locations.append(l1 + i * length / n)
            return (locations)

        def braceCoordinates(bracePoint: float) -> tuple[float, float, float]:
            """Calculate the global coordinates of a brace point along the member.

            :param bracePoint: Distance along member span.
            :type bracePoint: float
            :returns: Tuple of (x, y, z) coordinates.
            :rtype: tuple[float, float, float]
            """
            # Calculate the x, y and z vector components of the member
            dx = self.node_j.coordinates.x - self.node_i.coordinates.x
            dy = self.node_j.coordinates.y - self.node_i.coordinates.y
            dz = self.node_j.coordinates.z - self.node_i.coordinates.z
            # Calculate the member unit vectors
            x_unit = dx/self.length
            y_unit = dy/self.length
            z_unit = dz/self.length
            # Calculate nodal coordinates of brace point
            x = self.node_i.coordinates.x + bracePoint*x_unit
            y = self.node_i.coordinates.y + bracePoint*y_unit
            z = self.node_i.coordinates.z + bracePoint*z_unit
            # Return the brace point coordinates
            return (x, y, z)

        if self.bracing == 'quarter':
            bracePoints = discretize(self.length, 4)
        elif self.bracing == 'third':
            bracePoints = discretize(self.length, 3)
        elif self.bracing == 'midspan':
            bracePoints = discretize(self.length, 2)
        else:
            if type(self.bracing) == list:
                pass
            else:
                raise ValueError(
                    "Must be 'quarter','third','midspan' or an array of locations"
                )
            bracePoints = self.bracing

        unbracedSpans = len(bracePoints) + 1

        for i in range(unbracedSpans):

            # Determine unbraced span length
            if i == 0:
                l1 = 0
                unbracedLength = bracePoints[i]
            elif i == len(bracePoints):
                l1 = bracePoints[i-1]
                unbracedLength = self.length - l1
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

                for submbr in self.submembers.values():
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
                        Mp.append(submbr.results['major axis moments'][0])
                        Mp.append(-1*submbr.results['major axis moments'][1])
                        # Location for moment interpolation
                        dx = x - xi
                        dy = y - yi
                        dz = z - zi
                        L = sqrt(dx**2 + dy**2 + dz**2)
                        # Interpolate the quarter point moment value
                        M.append(abs(np.interp(L, Lp, Mp)))
                        moments.append(max(
                            abs(submbr.results['major axis moments'][0]),
                            abs(submbr.results['major axis moments'][1])
                        ))
                    else:
                        moments.append(max(
                            abs(submbr.results['major axis moments'][0]),
                            abs(submbr.results['major axis moments'][1])
                        ))
            # Calculate Cb
            Mmax = max(moments)
            Ma = M[0]
            Mb = M[1]
            Mc = M[2]
            Cb.append(12.5*Mmax/(2.5*Mmax + 3*Ma + 4*Mb + 3*Mc))

        self.Cb = min(min(Cb), 3)
        return self.Cb

    def add_point_load(self, mag: float, direction: str, location: float) -> None:
        """
        Apply a concentrated point load to the member.

        Applies a point load at a specified location along the member span.
        The load can be specified in either global (X, Y, Z) or local (x, y, z)
        coordinates. The method calculates equivalent nodal actions and distributes
        loads to the appropriate nodes and submembers.

        :param mag: Magnitude of the load in kips.
        :type mag: float
        :param direction: Load direction - global ('X', 'Y', 'Z') or local ('x', 'y', 'z').
        :type direction: str
        :param location: Load location as percentage of member span (0-100%).
        :type location: float
        :returns: None
        :rtype: None
        :raises ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """
        # Convert location from percentage to absolute distance
        location = self.length*(location/100)

        # Instantiate a variable measuring distance along the member
        l1 = 0

        # Acceptable floating-point error tolerance to consider load at a node
        pointError = 1*10**-10

        # Iterate through the submembers
        for _, submbr in self.submembers.items():

            l2 = l1 + submbr.length

            # Check if the load lands on the current submember
            if l1 <= location <= l2:

                # Extract rotation matrix for the current submember
                transformation_matrix = submbr.rotation_matrix[0:3, 0:3]

                # Initialize a global force vector
                if direction == 'X':
                    fg = np.array([mag, 0, 0])

                elif direction == 'x':
                    fg = np.array(
                        np.matmul(transformation_matrix, np.array([mag, 0, 0])))

                elif direction == 'Y':
                    fg = np.array([0, mag, 0])

                elif direction == 'y':
                    fg = np.array(
                        np.matmul(transformation_matrix, np.array([0, mag, 0])))

                elif direction == 'Z':
                    fg = np.array([0, 0, mag])

                elif direction == 'z':
                    fg = np.array(
                        np.matmul(transformation_matrix, np.array([0, 0, mag])))
                else:
                    raise ValueError(
                        "Load direction must be global ('X', 'Y', 'Z') or local ('x', 'y', 'z')."
                    )

                # Check if the load lands on node i of the submember
                if l1-pointError < location < l1+pointError:
                    # Add the X component of the load
                    submbr.node_i.add_load(mag=fg[0], lType='v', direction='X')

                    # Add the Y component of the load
                    submbr.node_i.add_load(mag=fg[1], lType='v', direction='Y')

                    # Add the Z component of the load
                    submbr.node_i.add_load(mag=fg[2], lType='v', direction='Z')

                # Check if the load lands on node j of the submember
                elif l2-pointError < location < l2+pointError:
                    # Add the X component of the load
                    submbr.node_j.add_load(mag=fg[0], lType='v', direction='X')

                    # Add the Y component of the load
                    submbr.node_j.add_load(mag=fg[1], lType='v', direction='Y')

                    # Add the Z component of the load
                    submbr.node_j.add_load(mag=fg[2], lType='v', direction='Z')

                # Load lands somewhere between the nodes of the submember
                else:
                    #         P
                    # o-------|-----o
                    # |<- a ->|<-b->|
                    b = l2 - location
                    a = submbr.length - b

                    # Transform the global force vector to local coordinates
                    FL = np.matmul(transformation_matrix, fg)

                    # Extract local axial force
                    axial = FL[0]

                    # Extract local shearing force
                    v = FL[1]

                    # Extract local transverse force
                    t = FL[2]

                    # Calculate equivalent nodal actions
                    if submbr.i_release == True and submbr.j_release == False:
                        # instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([10, 1])

                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b**2 * \
                            (a+2*submbr.length)/(2*submbr.length**3)
                        f_local[2, 0] = t*b**2 * \
                            (a+2*submbr.length)/(2*submbr.length**3)
                        f_local[4, 0] = axial*a/(submbr.length)
                        f_local[5, 0] = v*a * \
                            (3*submbr.length**2-a**2)/(2*submbr.length**3)
                        f_local[6, 0] = t*a * \
                            (3*submbr.length**2-a**2)/(2*submbr.length**3)
                        f_local[8, 0] = t*a*b * \
                            (a+submbr.length)/(2*submbr.length**2)
                        f_local[9, 0] = v*a*b * \
                            (a+submbr.length)/(2*submbr.length**2)

                    elif submbr.i_release == False and submbr.j_release == True:
                        # Instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([10, 1])

                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b * \
                            (3*submbr.length**2-b**2)/(2*submbr.length**3)
                        f_local[2, 0] = t*b * \
                            (3*submbr.length**2-b**2)/(2*submbr.length**3)
                        f_local[4, 0] = -t*b*a * \
                            (b+submbr.length)/(2*submbr.length**2)
                        f_local[5, 0] = -v*b*a * \
                            (b+submbr.length)/(2*submbr.length**2)
                        f_local[6, 0] = axial*a/(submbr.length)
                        f_local[7, 0] = v*a**2 * \
                            (b+2*submbr.length)/(2*submbr.length**3)
                        f_local[8, 0] = t*a**2 * \
                            (b+2*submbr.length)/(2*submbr.length**3)

                    else:
                        # Instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([12, 1])

                        # Forces at node i
                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b**2*(3*a+b)/submbr.length**3
                        f_local[2, 0] = t*b**2*(3*a+b)/submbr.length**3
                        f_local[4, 0] = -t*a*b**2/submbr.length**2
                        f_local[5, 0] = -v*a*b**2/submbr.length**2

                        # Forces at node j
                        f_local[6, 0] = axial*a/(submbr.length)
                        f_local[7, 0] = v*a**2*(a+3*b)/submbr.length**3
                        f_local[8, 0] = t*a**2*(a+3*b)/submbr.length**3
                        f_local[10, 0] = t*a**2*b/submbr.length**2
                        f_local[11, 0] = v*a**2*b/submbr.length**2

                    # Transform the local force vector to the global reference plane
                    transformation_matrix = np.matrix(submbr.rotation_matrix)
                    f_global = transformation_matrix.I*f_local

                    # Add the equivalent nodal forces and moments to each node
                    if submbr.i_release == True and submbr.j_release == False:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_j.Fx += f_global[4, 0]
                        submbr.node_j.Fy += f_global[5, 0]
                        submbr.node_j.Fz += f_global[6, 0]
                        submbr.node_j.Mx += f_global[7, 0]
                        submbr.node_j.My += f_global[8, 0]
                        submbr.node_j.Mz += f_global[9, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_j.eFx += f_global[4, 0]
                        submbr.node_j.eFy += f_global[5, 0]
                        submbr.node_j.eFz += f_global[6, 0]
                        submbr.node_j.eMx += f_global[7, 0]
                        submbr.node_j.eMy += f_global[8, 0]
                        submbr.node_j.eMz += f_global[9, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[4, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[5, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[6, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[8, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[9, 0]

                    elif submbr.i_release == False and submbr.j_release == True:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_i.My += f_global[4, 0]
                        submbr.node_i.Mz += f_global[5, 0]
                        submbr.node_j.Fx += f_global[6, 0]
                        submbr.node_j.Fy += f_global[7, 0]
                        submbr.node_j.Fz += f_global[8, 0]
                        submbr.node_j.Mx += f_global[9, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_i.eMy += f_global[4, 0]
                        submbr.node_i.eMz += f_global[5, 0]
                        submbr.node_j.eFx += f_global[6, 0]
                        submbr.node_j.eFy += f_global[7, 0]
                        submbr.node_j.eFz += f_global[8, 0]
                        submbr.node_j.eMx += f_global[9, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[6, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[7, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[5, 0]

                    else:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_i.My += f_global[4, 0]
                        submbr.node_i.Mz += f_global[5, 0]
                        submbr.node_j.Fx += f_global[6, 0]
                        submbr.node_j.Fy += f_global[7, 0]
                        submbr.node_j.Fz += f_global[8, 0]
                        submbr.node_j.Mx += f_global[9, 0]
                        submbr.node_j.My += f_global[10, 0]
                        submbr.node_j.Mz += f_global[11, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_i.eMy += f_global[4, 0]
                        submbr.node_i.eMz += f_global[5, 0]
                        submbr.node_j.eFx += f_global[6, 0]
                        submbr.node_j.eFy += f_global[7, 0]
                        submbr.node_j.eFz += f_global[8, 0]
                        submbr.node_j.eMx += f_global[9, 0]
                        submbr.node_j.eMy += f_global[10, 0]
                        submbr.node_j.eMz += f_global[11, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[6, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[7, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                        submbr.ENAs['minor axis moments'][1] += f_local[10, 0]
                        submbr.ENAs['major axis moments'][0] += f_local[5, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[11, 0]

                break

            l1 = l2

    def add_distributed_load(self, Mag1: float, Mag2: float, direction: str, loc1: float, loc2: float):
        """
        Apply a trapezoidal distributed load along the member.

        Applies a distributed load with linearly varying magnitude over a specified
        portion of the member span. Handles loading that spans across multiple
        submembers by calculating equivalent nodal actions for each affected segment.

        :param Mag1: Starting magnitude of the distributed load in kips.
        :type Mag1: float
        :param Mag2: Ending magnitude of the distributed load in kips.
        :type Mag2: float
        :param direction: Load direction - global ('X', 'Y', 'Z') or local ('x', 'y', 'z').
        :type direction: str
        :param loc1: Starting location of load along member span as percentage (0-100%).
        :type loc1: float
        :param loc2: Ending location of load along member span as percentage (0-100%).
        :type loc2: float
        :returns: None
        :rtype: None
        :raises ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """

        # Convert the start and end locations to absolute distance
        loc1 = self.length*(loc1/100)
        loc2 = self.length*(loc2/100)

        # Calculate the slope of the trapezoidal load
        m = (Mag2-Mag1)/(loc2-loc1)

        # Instantiate a variable to measure distance along the member
        l1 = 0

        # Iterate through the member's submembers
        for _, submbr in self.submembers.items():
            # Calculate the end location of the current submember
            l2 = l1+submbr.length

            # Extract rotation matrix for the current submember
            transformation_matrix = submbr.rotation_matrix[0:3, 0:3]

            if l2 < loc1 or l1 > loc2:
                # The load does not land on the current submember
                # Continue to the next iteration
                l1 = l2
                continue

            elif l1 <= loc1 and l2 >= loc2:
                # The load is located entirely on the current submember
                w1 = Mag1
                w2 = Mag2
                l = submbr.length
                a = loc1 - l1
                lw = loc2 - loc1
                b = l2 - loc2

            elif l1 <= loc1 and l2 <= loc2:
                # The load begins on the current submember
                w1 = Mag1
                w2 = m*(l2-loc1)+Mag1
                l = submbr.length
                a = loc1 - l1
                lw = l2 - loc1
                b = 0

            elif l1 >= loc1 and l2 >= loc2:
                # The load ends on the current submember
                w1 = m*(l1-loc1)+Mag1
                w2 = Mag2
                l = submbr.length
                a = 0
                lw = loc2 - l1
                b = l2 - loc2

            else:
                # l1 >= loc1 and l2 <= loc2:
                # Load continues over the current submember
                w1 = m*(l1-loc1)+Mag1
                w2 = m*(l2-loc1)+Mag1
                l = submbr.length
                a = 0
                lw = l2 - l1
                b = 0

            # Initialize a global force vector
            if direction == 'X':
                fg1 = np.array([w1, 0, 0])
                fg2 = np.array([w2, 0, 0])

            elif direction == 'x':
                fg1 = np.matmul(transformation_matrix, np.array([w1, 0, 0]))
                fg2 = np.matmul(transformation_matrix, np.array([w2, 0, 0]))

            elif direction == 'Y':
                fg1 = np.array([0, w1, 0])
                fg2 = np.array([0, w2, 0])

            elif direction == 'y':
                fg1 = np.matmul(transformation_matrix, np.array([0, w1, 0]))
                fg2 = np.matmul(transformation_matrix, np.array([0, w2, 0]))

            elif direction == 'Z':
                fg1 = np.array([0, 0, w1])
                fg2 = np.array([0, 0, w2])

            elif direction == 'z':
                fg1 = np.matmul(transformation_matrix, np.array([0, 0, w1]))
                fg2 = np.matmul(transformation_matrix, np.array([0, 0, w2]))
            else:
                raise ValueError(
                    "Force vector must be bound to a global or local axis."
                )

            # Transform the global force vector to local coordinates
            FL1 = np.matmul(transformation_matrix, fg1)
            FL2 = np.matmul(transformation_matrix, fg2)

            # Extract local axial force
            a1 = FL1[0]
            a2 = FL2[0]

            # Extract local shearing force
            v1 = FL1[1]
            v2 = FL2[1]
            vd = v2 - v1
            vm = (v1+v2)/2

            # Extract local transverse force
            t1 = FL1[2]
            t2 = FL2[2]
            td = t2 - t1
            tm = (t1+t2)/2

            if submbr.i_release == False and submbr.j_release == False:
                # Instantiate a local force vector
                f_local = np.zeros([12, 1])

                # Calculate the geometric constants
                s1 = 10*((l**2+a**2)*(l+a)-(a**2+b**2)*(a-b)-l*b*(l+b)-a**3)
                s2 = lw*(l*(2*l+a+b)-3*(a-b)**2-2*a*b)
                s3 = 120*a*b*(a+lw)+10*lw*(6*a**2+4*l*lw-3*lw**2)
                s4 = 10*l*lw**2-10*lw*a*(l-3*b)-9*lw**3

                # forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[7, 0] = (lw*(s1*vm+s2*vd))/(20*l**3)  # normal shear
                f_local[8, 0] = (lw*(s1*tm+s2*td)) / \
                    (20*l**3)  # transverse shear
                f_local[10, 0] = -(lw*(s3*tm+s4*td)) / \
                    (120*l**2)  # minor axis moment
                f_local[11, 0] = -(lw*(s3*vm+s4*vd)) / \
                    (120*l**2)  # major axis moment

                # Forces at node i
                vj = f_local[7, 0]  # Normal shear force at node j
                tj = f_local[8, 0]  # Transverse shear force at node j
                mj = f_local[10, 0]  # Minor axis moment at node j
                Mj = f_local[11, 0]  # Major axis moment at node j

                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = lw*vm-vj  # normal shear
                f_local[2, 0] = lw*tm-tj  # transverse shear
                f_local[4, 0] = mj+tj*l-a*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[5, 0] = Mj+vj*l-a*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

            elif submbr.i_release == True and submbr.j_release == False:
                # Instantiate a local force vector
                f_local = np.zeros([12, 1])

                s1 = 40*l*(2*l**2-lw**2)+10*lw * \
                    (lw**2-2*b**2)-40*b*(l-a)*(2*l+a)
                s2 = lw*(3*lw**2-10*l*(lw+2*b)+10*b*(b+lw))

                # Forces at node i
                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = (lw*(s1*vm+s2*vd))/(80*l**3)  # normal shear
                f_local[2, 0] = (lw*(s1*tm+s2*td)) / \
                    (80*l**3)  # transverse shear
                f_local[4, 0] = 0  # minor axis moment
                f_local[5, 0] = 0  # major axis moment

                # forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[7, 0] = lw*vm-f_local[1, 0]  # normal shear
                f_local[8, 0] = lw*vm-f_local[2, 0]  # transverse shear
                f_local[10, 0] = f_local[8, 0]*l-b*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[11, 0] = f_local[7, 0]*l-b*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

            else:
                # Instantiate a local force vector
                # (submbr.i_release == False and submbr.j_release == True)
                f_local = np.zeros([12, 1])

                s1 = 40*l*(2*l**2-lw**2)+10*lw * \
                    (lw**2-2*a**2)-40*a*(l-b)*(2*l+b)
                s2 = lw*(3*lw**2-10*l*(lw+2*a)+10*a*(a+lw))

                # Forces at node i
                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = (lw*(s1*vm+s2*vd))/(80*l**3)  # normal shear
                f_local[2, 0] = (lw*(s1*tm+s2*td)) / \
                    (80*l**3)  # transverse shear
                f_local[4, 0] = f_local[2, 0]*l-a*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[5, 0] = f_local[1, 0]*l-a*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

                # Forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # Axial
                f_local[7, 0] = lw*vm-f_local[1, 0]  # Normal shear
                f_local[8, 0] = lw*vm-f_local[2, 0]  # Transverse shear
                f_local[10, 0] = 0  # Minor axis moment
                f_local[11, 0] = 0  # Major axis moment

            # Transform the local force vector to the global reference plane
            transformation_matrix = np.matrix(submbr.rotation_matrix)
            f_global = transformation_matrix.I*f_local

            # Add the equivalent nodal forces and moments to each node
            if submbr.i_release == True and submbr.j_release == False:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_j.Fx += f_global[4, 0]
                submbr.node_j.Fy += f_global[5, 0]
                submbr.node_j.Fz += f_global[6, 0]
                submbr.node_j.Mx += f_global[7, 0]
                submbr.node_j.My += f_global[8, 0]
                submbr.node_j.Mz += f_global[9, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_j.eFx += f_global[4, 0]
                submbr.node_j.eFy += f_global[5, 0]
                submbr.node_j.eFz += f_global[6, 0]
                submbr.node_j.eMx += f_global[7, 0]
                submbr.node_j.eMy += f_global[8, 0]
                submbr.node_j.eMz += f_global[9, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[4, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[5, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[6, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[8, 0]
                submbr.ENAs['major axis moments'][1] += f_local[9, 0]

            elif submbr.i_release == False and submbr.j_release == True:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_i.My += f_global[4, 0]
                submbr.node_i.Mz += f_global[5, 0]
                submbr.node_j.Fx += f_global[6, 0]
                submbr.node_j.Fy += f_global[7, 0]
                submbr.node_j.Fz += f_global[8, 0]
                submbr.node_j.Mx += f_global[9, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_i.eMy += f_global[4, 0]
                submbr.node_i.eMz += f_global[5, 0]
                submbr.node_j.eFx += f_global[6, 0]
                submbr.node_j.eFy += f_global[7, 0]
                submbr.node_j.eFz += f_global[8, 0]
                submbr.node_j.eMx += f_global[9, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[6, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[7, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                submbr.ENAs['major axis moments'][1] += f_local[5, 0]

            else:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_i.My += f_global[4, 0]
                submbr.node_i.Mz += f_global[5, 0]
                submbr.node_j.Fx += f_global[6, 0]
                submbr.node_j.Fy += f_global[7, 0]
                submbr.node_j.Fz += f_global[8, 0]
                submbr.node_j.Mx += f_global[9, 0]
                submbr.node_j.My += f_global[10, 0]
                submbr.node_j.Mz += f_global[11, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_i.eMy += f_global[4, 0]
                submbr.node_i.eMz += f_global[5, 0]
                submbr.node_j.eFx += f_global[6, 0]
                submbr.node_j.eFy += f_global[7, 0]
                submbr.node_j.eFz += f_global[8, 0]
                submbr.node_j.eMx += f_global[9, 0]
                submbr.node_j.eMy += f_global[10, 0]
                submbr.node_j.eMz += f_global[11, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[6, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[7, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                submbr.ENAs['minor axis moments'][1] += f_local[10, 0]
                submbr.ENAs['major axis moments'][0] += f_local[5, 0]
                submbr.ENAs['major axis moments'][1] += f_local[11, 0]

            l1 = l2

    def second_order(self) -> None:
        """
        Apply second-order (P-delta) effects to account for geometric nonlinearity.

        Constructs and adds geometric stiffness matrices to all submembers to account
        for second-order effects including P-delta moments. This modifies the local
        stiffness matrix of each submember by including the effects of axial forces
        on bending behavior.

        :returns: None
        :rtype: None
        """
        for submbr in self.submembers.values():
            # Calculate the submember local geometric stiffness matrix
            KG = submbr.build_geometric_stiffness_matrix()

            # Redefine the submember local stiffness matrix
            submbr.Kl += KG

            # Calculate the submember global geometric stiffness matrix
            submbr.KG = submbr.transformation_matrix.T.dot(
                submbr.Kl).dot(submbr.transformation_matrix)
