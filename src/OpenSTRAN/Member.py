from .Nodes import Nodes
from .Node import Node
from .Submember import SubMember
from .Database.Shape import Shape
from .Coordinates import Coordinate
from .Loads import DistributedLoad, PointLoad
from .Units import (
    COLLINEAR_TOLERANCE,
    LOAD_OVERLAP_TOLERANCE,
    VERTICAL_TOLERANCE,
)
import numpy as np

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
            locations along the span in inches.
        shape (str | Shape | None): Cross-sectional shape identifier.
        length (float): Calculated length of the member in inches.
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
    count: int = 0
    submembers: dict[int, SubMember] = field(
        default_factory=dict[int, SubMember])
    _prepared: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Initialize the member after dataclass instantiation to calculate
        the member's length based on the i (start) and j (end) nodes.
        """
        # Calculate the member length based on the node coordinates
        self.length = self.calculate_length(self.node_i, self.node_j)

    def prepare(self) -> None:
        """Generate the member mesh, once.

        Called by :meth:`OpenSTRAN.Model.Model.solve` prior to assembling the
        global stiffness matrix. Meshing is deferred until this point so that
        nodes created by loads (point load locations and distributed load
        extents) are included when the member is discretized into submembers.
        """
        if self._prepared:
            return
        self.generate_mesh()
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
        for k in range(1, self.mesh):
            self._node_at_fraction(k/self.mesh)

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
        if not np.allclose(np.cross(v, w), 0.0, atol=COLLINEAR_TOLERANCE):
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
        # Offset to define the local x-y plane; vertical members are
        # special-cased.
        if abs(dx) < VERTICAL_TOLERANCE and abs(dz) < VERTICAL_TOLERANCE:
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

    def add_node(self, location: float) -> Node:
        """Add a node at a location along the member, or return the node
        already there.

        The member is meshed through every node along it when the model is
        first solved, so a node added after that is not connected to it.

        Args:
            location (float): Position along the span as a percentage
                (0-100%).

        Returns:
            Node: The node at the location; a mesh node if it was created.
        """
        return self._node_at_fraction(location/100)

    def _node_at_fraction(self, frac: float) -> Node:
        """The node at a fraction (0 to 1) of the span, created as a mesh
        node if there is none; used by ``add_node`` and the mesh."""
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

    def add_point_load(self, mag: float, direction: str, location: float) -> PointLoad:
        """Apply a concentrated point load to the member as a nodal load.

        Adds the load to the model's loads (``Model.loads``); see
        :meth:`OpenSTRAN.Loads.Loads.add_point_load`. A node is created at
        the load location if the load does not land on an existing node, and
        the load is applied to that node when the model is solved.

        Args:
            mag (float): Magnitude of the load in kips.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            location (float): Load location as percentage of member span (0-100%).

        Returns:
            PointLoad: The load as recorded.

        Raises:
            ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """
        return self.nodes.loads.add_point_load(self, mag, direction, location)

    def point_load_vector(self, mag: float, direction: str) -> np.ndarray:
        """Global X, Y and Z components of a point load on the member.

        Args:
            mag (float): Magnitude of the load in kips.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').

        Returns:
            np.ndarray: The three global components, in kips.
        """
        if direction in ('X', 'Y', 'Z'):
            return np.array([
                mag if direction == 'X' else 0.0,
                mag if direction == 'Y' else 0.0,
                mag if direction == 'Z' else 0.0,
            ])
        local = np.array([
            mag if direction == 'x' else 0.0,
            mag if direction == 'y' else 0.0,
            mag if direction == 'z' else 0.0,
        ])
        return self._local_axes() @ local

    def add_distributed_load(self, Mag1: float, Mag2: float, direction: str, loc1: float, loc2: float) -> DistributedLoad:
        """Apply a trapezoidal distributed load along the member.

        Adds the load to the model's loads (``Model.loads``); see
        :meth:`OpenSTRAN.Loads.Loads.add_distributed_load`. Nodes are created
        at the start and end of the loaded region (if they do not already
        exist) so the load aligns with element boundaries. Each solve applies
        it to the submembers of the mesh through equivalent nodal actions (see
        :meth:`distributed_load_actions`).

        Args:
            Mag1 (float): Start magnitude of the distributed load in kips per
                inch.
            Mag2 (float): End magnitude of the distributed load in kips per
                inch.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            loc1 (float): Start location of load along member span as percentage
                (0-100%).
            loc2 (float): End location of load along member span as percentage
                (0-100%).

        Returns:
            DistributedLoad: The load as recorded.

        Raises:
            ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """
        return self.nodes.loads.add_distributed_load(
            self, Mag1, Mag2, direction, loc1, loc2)

    def distributed_load_actions(
        self, Mag1: float, Mag2: float, direction: str, loc1: float, loc2: float
    ) -> list[tuple[SubMember, np.ndarray, tuple[float, float], tuple[float, float]]]:
        """Equivalent nodal actions of a trapezoidal load on the submembers.

        Called by the solver at each solve, after the member has been meshed.

        Args:
            Mag1 (float): Start magnitude of the distributed load in kips per
                inch.
            Mag2 (float): End magnitude of the distributed load in kips per
                inch.
            direction (str): Load direction - global ('X', 'Y', 'Z') or local
                ('x', 'y', 'z').
            loc1 (float): Start location of load along member span as percentage
                (0-100%).
            loc2 (float): End location of load along member span as percentage
                (0-100%).

        Returns:
            list: For each submember the load lands on, a tuple of the
            submember; its 12 equivalent nodal actions in local coordinates
            (the fixed-end forces reversed, with any released ends condensed
            out), as a 12x1 array; and the load intensities (i end, j end), in
            kips per inch, in the major (local y) and minor (local z) planes.

        Raises:
            ValueError: If direction is not one of 'X', 'Y', 'Z', 'x', 'y', 'z'.
        """
        actions: list[tuple[SubMember, np.ndarray, tuple[float, float], tuple[float, float]]] = []

        # Convert the start and end locations to absolute distance
        loc1 = self.length*(loc1/100)
        loc2 = self.length*(loc2/100)

        # Calculate the slope of the trapezoidal load
        m = (Mag2-Mag1)/(loc2-loc1)

        # Instantiate a variable to measure distance along the member
        l1 = 0

        # A submember that the load barely overlaps is treated as unloaded.
        tolerance = LOAD_OVERLAP_TOLERANCE

        # Iterate through the member's submembers
        for _, submbr in self.submembers.items():
            # Calculate the end location of the current submember
            l2 = l1+submbr.length

            # Rotation matrix for the current submember.
            local_to_global = submbr.rotation_matrix[0:3, 0:3]

            if l2 <= loc1 + tolerance or l1 >= loc2 - tolerance:
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
                fg1 = np.matmul(local_to_global, np.array([w1, 0, 0]))
                fg2 = np.matmul(local_to_global, np.array([w2, 0, 0]))

            elif direction == 'Y':
                fg1 = np.array([0, w1, 0])
                fg2 = np.array([0, w2, 0])

            elif direction == 'y':
                fg1 = np.matmul(local_to_global, np.array([0, w1, 0]))
                fg2 = np.matmul(local_to_global, np.array([0, w2, 0]))

            elif direction == 'Z':
                fg1 = np.array([0, 0, w1])
                fg2 = np.array([0, 0, w2])

            elif direction == 'z':
                fg1 = np.matmul(local_to_global, np.array([0, 0, w1]))
                fg2 = np.matmul(local_to_global, np.array([0, 0, w2]))
            else:
                raise ValueError(
                    "Force vector must be bound to a global or local axis."
                )

            # Transform the global force vector to local coordinates
            FL1 = np.matmul(local_to_global.T, fg1)
            FL2 = np.matmul(local_to_global.T, fg2)

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

            # Axial load: the resultant acts at the centroid of the loaded
            # length and is shared between the nodes in proportion to its
            # distance from each.
            axial_total = (a1+a2)*lw/2
            axial_j = (a*axial_total+lw**2*(a1+2*a2)/6)/l

            # forces at node j
            f_local[6, 0] = axial_j  # axial
            f_local[7, 0] = (lw*(s1*vm+s2*vd))/(20*l**3)  # normal shear
            f_local[8, 0] = (lw*(s1*tm+s2*td)) / \
                (20*l**3)  # transverse shear
            f_local[10, 0] = (lw*(s3*tm+s4*td)) / \
                (120*l**2)  # minor axis moment
            f_local[11, 0] = -(lw*(s3*vm+s4*vd)) / \
                (120*l**2)  # major axis moment

            # Forces at node i
            vj = f_local[7, 0]  # Normal shear force at node j
            tj = f_local[8, 0]  # Transverse shear force at node j
            mj = f_local[10, 0]  # Minor axis moment at node j
            Mj = f_local[11, 0]  # Major axis moment at node j

            f_local[0, 0] = axial_total-axial_j  # axial
            f_local[1, 0] = lw*vm-vj  # normal shear
            f_local[2, 0] = lw*tm-tj  # transverse shear
            f_local[4, 0] = tj*l-mj-a*lw*tm - \
                (lw**2*(2*t2+t1))/6  # minor axis moment
            f_local[5, 0] = a*lw*vm+(lw**2*(2*v2+v1))/6 - \
                Mj-vj*l  # major axis moment

            # The actions above assume both ends of the submember are fixed.
            # Condense the released ends out, as SubMember.pin condenses the
            # stiffness matrix.
            f_local = submbr.pin_vector(f_local)

            # The local distributed-load intensities at the submember ends,
            # from which the results evaluate exact internal forces along the
            # span. Each loaded submember is fully covered (nodes are placed
            # at the load extents), so v1/t1 act at node i and v2/t2 at node j.
            actions.append((submbr, f_local, (v1, v2), (t1, t2)))

            l1 = l2

        return actions
