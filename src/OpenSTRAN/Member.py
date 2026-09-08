from .Nodes import Nodes
from .Node import Node
from .Submember import SubMember
from .Database.Shape import Shape
from .Coordinates import Coordinate
import numpy as np
from scipy.linalg import inv
from math import sqrt

from typing import Any

from dataclasses import dataclass, field, asdict


@dataclass(slots=True)
class Member():
    """Represents a 3D space frame member connecting two nodes.

    A member is a structural element that connects two nodes and can be
    discretized into submembers for analysis. It supports various boundary
    conditions, material properties, and loading conditions.

    Parameters:
        nodes (Nodes): Reference to the Nodes collection object.
        node_i (Node): Start node of the member.
        node_j (Node): End node of the member.
        i_release (list[int]): Boundary condition at node i.
        j_release (list[int]): Boundary condition at node j.
        E (float): Young's modulus in ksi.
        Ixx (float): Strong axis moment of inertia in in^4.
        Iyy (float): Weak axis moment of inertia in in^4.
        A (float): Cross-sectional area in in^2.
        G (float): Shear modulus in ksi.
        J (float): Polar moment of inertia in in^4.
        mesh (int): Number of discretizations (submembers) along the member span.
        bracing (str | list[float]): Lateral bracing configuration. Can be
            'continuous', 'quarter', 'third', 'midspan', or a list of bracing
            locations along the span.
        shape (str | Shape | None): Cross-sectional shape identifier.
        length (float): Calculated length of the member (in).
        Cb (float): Lateral-torsional buckling coefficient.
        count (int): Counter for submember creation.
        submembers (dict[int, SubMember]): Dictionary of submembers indexed by
            creation order.
    """
    nodes: Nodes
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
    mesh: int
    bracing: str | list[float]
    shape: Shape | None
    length: float = field(init=False)
    Cb: float = field(init=False)
    count: int = 0
    submembers: dict[int, SubMember] = field(
        default_factory=dict[int, SubMember])
    point_loads: list = field(default_factory=list, init=False)
    distributed_loads: list = field(default_factory=list, init=False)
    _prepared: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Initialize the member after dataclass instantiation to calculate
        the member's length based on the i (start) and j (end) nodes.
        """
        # Calculate the member length based on the node coordinates
        self.length = self.calculate_length(self.node_i, self.node_j)

    def prepare(self) -> None:
        """Generate the member mesh and apply deferred loads.

        Called by :meth:`OpenSTRAN.Model.Model.solve` prior to assembling the
        global stiffness matrix. Meshing is deferred until this point so that
        nodes created by loads (point load locations and distributed load
        extents) are included when the member is discretized into submembers.
        """
        if self._prepared:
            return
        self.generate_mesh()
        for load in self.distributed_loads:
            self._apply_distributed_load(*load)
        self._prepared = True

    def generate_mesh(self) -> None:
        """Discretize the member into submembers.

        Builds the uniform subdivision requested by ``mesh`` and merges in every
        other node lying on the member axis. These include user-defined nodes
        and the nodes created at point-load locations and distributed-load extents.
        Consecutive nodes along the member are connected by submembers, with the
        member end releases applied only to the first and last submembers.
        """
        # Reset any previously generated submembers so meshing is repeatable.
        self.submembers: dict[int, SubMember] = {}
        self.count: int = 0

        # Create the uniform subdivision nodes along the member span.
        i = self.node_i.coordinates
        j = self.node_j.coordinates
        dx = j.x - i.x
        dy = j.y - i.y
        dz = j.z - i.z
        for k in range(1, self.mesh):
            frac = k/self.mesh
            self.nodes.add_node(
                i.x + frac*dx, i.y + frac*dy, i.z + frac*dz, mesh_node=True)

        # Collect and order every node lying on the member axis.
        mesh_nodes = self._axis_nodes()

        # Connect consecutive nodes, applying the member end releases only to
        # the first and last submembers.
        n_segments = len(mesh_nodes) - 1
        for idx in range(n_segments):
            i_release = self.i_release if idx == 0 else [0, 0, 0, 0, 0, 0]
            j_release = self.j_release if idx == n_segments - 1 \
                else [0, 0, 0, 0, 0, 0]
            self.add_submember(
                mesh_nodes[idx],
                mesh_nodes[idx+1],
                i_release,
                j_release,
                self.E,
                self.Ixx,
                self.Iyy,
                self.A,
                self.G,
                self.J
            )

    def _axis_nodes(self) -> list[Node]:
        """Return the nodes lying on the member axis, ordered without duplicates.

        Returns:
            list[Node]: Nodes on the member (including its end nodes) ordered
            from ``node_i`` to ``node_j`` along the dominant global axis, with
            coincident nodes removed.
        """
        nodes_on_axis = [
            n for n in self.nodes.nodes.values() if self.on_segment(n)]

        # Sort along the dominant global axis so submembers connect in order.
        dx = self.node_j.coordinates.x - self.node_i.coordinates.x
        dy = self.node_j.coordinates.y - self.node_i.coordinates.y
        dz = self.node_j.coordinates.z - self.node_i.coordinates.z
        if abs(dx) >= abs(dy) and abs(dx) >= abs(dz):
            def key(n): return n.coordinates.x
            reverse = dx < 0
        elif abs(dy) >= abs(dz):
            def key(n): return n.coordinates.y
            reverse = dy < 0
        else:
            def key(n): return n.coordinates.z
            reverse = dz < 0
        nodes_on_axis.sort(key=key, reverse=reverse)

        # Remove coincident nodes (e.g. a load landing on a uniform mesh node).
        seen: set = set()
        unique: list[Node] = []
        for node in nodes_on_axis:
            coord = tuple(np.round(node.coordinates.vector, 6))
            if coord not in seen:
                seen.add(coord)
                unique.append(node)
        return unique

    def on_segment(self, node_k: Node) -> bool:
        """Check whether a node lies on the segment between the member end nodes.

        Args:
            node_k (Node): The node to test.

        Returns:
            bool: True if ``node_k`` is collinear with and between ``node_i`` and
            ``node_j`` (inclusive), False otherwise.
        """
        i = self.node_i.coordinates.vector
        j = self.node_j.coordinates.vector
        k = node_k.coordinates.vector
        v = j - i
        w = k - i
        L2 = float(np.dot(v, v))
        if L2 == 0:
            return False
        # Collinearity: the cross product of the member vector and (k - i) is ~0.
        if not np.allclose(np.cross(v, w), 0.0, atol=1e-6):
            return False
        # Parametric position along the member must fall within [0, 1].
        t = float(np.dot(w, v)/L2)
        return -1e-9 <= t <= 1 + 1e-9

    def _local_axes(self) -> np.ndarray:
        """Return the 3x3 rotation matrix mapping member-local axes to global.

        The columns are the member's local x, y and z unit vectors expressed in
        the global reference frame, derived with the same Gram-Schmidt approach
        used by :class:`OpenSTRAN.Submember.SubMember`.

        Returns:
            np.ndarray: A 3x3 rotation matrix.
        """
        i = self.node_i.coordinates
        j = self.node_j.coordinates
        dx = j.x - i.x
        dz = j.z - i.z
        # Offset to define the local x-y plane; vertical members are special-cased.
        if abs(dx) < 0.001 and abs(dz) < 0.001:
            i_offset = np.array([i.x-1, i.y, i.z])
            j_offset = np.array([j.x-1, j.y, j.z])
        else:
            i_offset = np.array([i.x, i.y+1, i.z])
            j_offset = np.array([j.x, j.y+1, j.z])

        local_x_unit = (j.vector - i.vector)/self.length
        node_k = i_offset + 0.5*(j_offset - i_offset)
        vector_in_plane = node_k - i.vector
        local_y_vector = vector_in_plane - \
            np.dot(vector_in_plane, local_x_unit)*local_x_unit
        local_y_unit = local_y_vector/np.linalg.norm(local_y_vector)
        local_z_unit = np.cross(local_x_unit, local_y_unit)
        return np.array([local_x_unit, local_y_unit, local_z_unit]).T

    def _node_at_fraction(self, frac: float) -> Node:
        """Create (or reuse) a node at a fractional position along the member.

        Args:
            frac (float): Position along the span as a fraction from 0.0 to 1.0.

        Returns:
            Node: The node at the requested position.
        """
        i = self.node_i.coordinates
        dx = self.node_j.coordinates.x - i.x
        dy = self.node_j.coordinates.y - i.y
        dz = self.node_j.coordinates.z - i.z
        return self.nodes.add_node(
            i.x + frac*dx, i.y + frac*dy, i.z + frac*dz, mesh_node=True)

    def calculate_length(self, node_i: Node, node_j: Node) -> float:
        """Calculate the length of the member using the Euclidean distance formula.

        Computes the 3D distance between two nodes based on their coordinate
        positions in the global reference frame.

        Args:
            node_i (Node): Start node of the member.
            node_j (Node): End node of the member.

        Returns:
            float: The length of the member.
        """
        # Calculate the difference in vector components of the member
        dv = node_j.coordinates.vector-node_i.coordinates.vector
        # Calculate and return the member length
        return float(np.linalg.norm(dv))

    def properties(self) -> dict[str, Any]:
        """Return all member properties as a dictionary.

        Converts the dataclass instance into a dictionary representation containing
        all field names and their current values.

        Returns:
            dict[str, Any]: Dictionary containing all member attributes and their values.
        """
        return asdict(self)

    def add_submember(
        self,
        node_i: Node,
        node_j: Node,
        i_release: list[int],
        j_release: list[int],
        E: float,
        Ixx: float,
        Iyy: float,
        A: float,
        G: float,
        J: float
    ) -> None:
        """Add a submember to the member collection.

        Creates a new submember element connecting two nodes with specified
        boundary conditions and material properties. The submember is stored
        in the submembers dictionary using an auto-incremented counter.

        Args:
            node_i (Node): Start node of the submember.
            node_j (Node): End node of the submember.
            i_release (list[int]): Release conditions at start node.
            j_release (list[int]): Release conditions at end node.
            E (float): Young's modulus in ksi.
            Ixx (float): Strong axis moment of inertia in in^4.
            Iyy (float): Weak axis moment of inertia in in^4.
            A (float): Cross-sectional area in in^2.
            G (float): Shear modulus in ksi.
            J (float): Polar moment of inertia in in^4.

        Returns:
            None
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
        """Calculate the lateral-torsional buckling coefficient (Cb) for the member.

        Computes Cb based on moment variation along unbraced spans using the
        standard AISC formula: Cb = 12.5*Mmax / (2.5*Mmax + 3*Ma + 4*Mb + 3*Mc).
        The calculation accounts for lateral bracing locations and interpolates
        moments at quarter-span points. The result is limited to a maximum of
        3.0.

        Returns:
            float: The lateral-torsional buckling coefficient, limited to 3.0 maximum.
        """
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

        if self.bracing == 'continuous':
            bracePoints = discretize(self.length, int(f'{self.length:.0f}'))
        elif self.bracing == 'quarter':
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
        """Apply a concentrated point load to the member as a nodal load.

        Ensures a node exists at the load location, creating one if the load
        does not land on an existing node, and applies the load directly to
        that node.

        Args:
            mag (float): Magnitude of the load in kips.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            location (float): Load location as percentage of member span (0-100%).

        Raises:
            ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """
        # Create (or reuse) a node at the load location along the member.
        node = self._node_at_fraction(location/100)

        # Resolve the load into global X, Y, Z components.
        if direction in ('X', 'Y', 'Z'):
            fg = np.array([
                mag if direction == 'X' else 0.0,
                mag if direction == 'Y' else 0.0,
                mag if direction == 'Z' else 0.0,
            ])
        elif direction in ('x', 'y', 'z'):
            local = np.array([
                mag if direction == 'x' else 0.0,
                mag if direction == 'y' else 0.0,
                mag if direction == 'z' else 0.0,
            ])
            fg = self._local_axes() @ local
        else:
            raise ValueError(
                "Load direction must be global ('X', 'Y', 'Z') or local ('x', 'y', 'z')."
            )

        # Apply the load directly to the node as a nodal load.
        node.Fx += fg[0]
        node.Fy += fg[1]
        node.Fz += fg[2]

        # Mirror the load into the node's equivalent-action accumulators so the
        # solver recovers the correct reaction if the load lands on a support.
        node.eFx += fg[0]
        node.eFy += fg[1]
        node.eFz += fg[2]

        # Record the load for reference.
        self.point_loads.append((mag, direction, location, node))

    def add_distributed_load(self, Mag1: float, Mag2: float, direction: str, loc1: float, loc2: float):
        """Apply a trapezoidal distributed load along the member.

        Creates nodes at the start and end of the loaded region (if they do not
        already exist) so the load aligns with element boundaries, then defers
        the load until the member is meshed at solve time. The load remains a
        member (distributed) load applied via equivalent nodal actions in
        :meth:`_apply_distributed_load`.

        Args:
            Mag1 (float): Start magnitude of the distributed load in kips.
            Mag2 (float): End magnitude of the distributed load in kips.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            loc1 (float): Start location of load along member span as percentage
                (0-100%).
            loc2 (float): End location of load along member span as percentage
                (0-100%).
        """
        # Ensure nodes exist at the start and end of the loaded region.
        self._node_at_fraction(loc1/100)
        self._node_at_fraction(loc2/100)

        # Defer application until the member has been meshed at solve time.
        self.distributed_loads.append((Mag1, Mag2, direction, loc1, loc2))

    def _apply_distributed_load(self, Mag1: float, Mag2: float, direction: str, loc1: float, loc2: float):
        """Distribute a trapezoidal load onto the member's submembers.

        Computes equivalent nodal actions for each affected submember. Called by
        :meth:`prepare` after the member has been meshed.

        Args:
            Mag1 (float): Start magnitude of the distributed load in kips.
            Mag2 (float): End magnitude of the distributed load in kips.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            loc1 (float): Start location of load along member span as percentage
                (0-100%).
            loc2 (float): End location of load along member span as percentage
                (0-100%).

        Raises:
            ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
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

            # Instantiate a local force vector
            f_local: np.ndarray = np.zeros([12, 1])

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

            # Transform the local force vector to the global reference plane
            transformation_matrix = np.asarray(submbr.rotation_matrix)
            f_global: np.ndarray = inv(transformation_matrix) @ f_local

            # Add the equivalent nodal forces and moments to each node
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

            # Record the local distributed-load intensities at the submember
            # ends so exact internal forces can be evaluated along the span.
            # Each loaded submember is fully covered (nodes are placed at the
            # load extents), so v1/t1 act at node i and v2/t2 act at node j.
            submbr.w_major[0] += v1
            submbr.w_major[1] += v2
            submbr.w_minor[0] += t1
            submbr.w_minor[1] += t2

            l1 = l2

    def _locate(self, location: float) -> tuple[SubMember, float]:
        """Map a span location to the parent submember and a local position.

        Args:
            location (float): Position along the member span as a percentage
                (0-100%).

        Returns:
            tuple[SubMember, float]: The submember containing the location and the
            distance (in inches) from that submember's i-node.
        """
        target = self.length*(location/100)*12  # inches from node i
        run = 0.0
        submbr = None
        for submbr in self.submembers.values():
            sub_length = submbr.length*12
            if run - 1e-6 <= target <= run + sub_length + 1e-6:
                return submbr, min(max(target - run, 0.0), sub_length)
            run += sub_length
        # Location is beyond the last submember; clamp to its far end.
        return submbr, submbr.length*12

    def moment(self, location: float, axis: str = 'major') -> float:
        """Internal bending moment at an arbitrary location along the member.

        Calculates exact moments between mesh nodes by evaluating the parent
        submember's closed-form moment expression.

        Args:
            location (float): Position along the span as a percentage (0-100%).
            axis (str, optional): 'major' (about local z) or 'minor' (about local
                y). Defaults to 'major'.

        Returns:
            float: Bending moment in kip-inches.
        """
        submbr, x = self._locate(location)
        if axis == 'minor':
            return submbr.moment_minor(x)
        return submbr.moment_major(x)

    def shear(self, location: float, axis: str = 'major') -> float:
        """Internal shear force at an arbitrary location along the member.

        Args:
            location (float): Position along the span as a percentage (0-100%).
            axis (str, optional): 'major' (local y) or 'minor' (local z).
                Defaults to 'major'.

        Returns:
            float: Shear force in kips.
        """
        submbr, x = self._locate(location)
        if axis == 'minor':
            return submbr.shear_minor(x)
        return submbr.shear_major(x)

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
