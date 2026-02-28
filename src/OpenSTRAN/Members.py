from .Member import Member
from .Nodes import Nodes
from .Node import Node
from .Database.Shape import Shape

from dataclasses import dataclass, field, asdict

from typing import Any


@dataclass(slots=True)
class Members():
    """Container class for managing member (element) objects.

    Parameters:
        nodes (Nodes): Reference to the global Nodes collection.
        count (int): Number of members added to the collection.
        members (dict[int, Member]): Mapping of member ID to Member object.
    """
    nodes: Nodes
    count: int = 0
    members: dict[int, Member] = field(default_factory=dict[int, Member])

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        Returns:
            dict[str, Any]: Dictionary of this instance's fields.
        """
        return asdict(self)

    def add_member(
        self,
        node_i: Node,
        node_j: Node,
        i_release: bool = False,
        j_release: bool = False,
        E: float = 29000.0,
        Ixx: float = 88.6,
        Iyy: float = 2.36,
        A: float = 4.16,
        G: float = 12000.0,
        J: float = 0.0704,
        mesh: int = 50,
        bracing: str = "continuous",
        shape: Shape | None = None,
    ) -> Member:
        """Add a member to the model.

        Args:
            node_i (Node): Start node of the member.
            node_j (Node): End node of the member.
            i_release (bool, optional): True if start node is released (pinned).
                Defaults to False.
            j_release (bool, optional): True if end node is released (pinned).
                Defaults to False.
            E (float, optional): Young's modulus in ksi. Defaults to 29000.0.
            Ixx (float, optional): Moment of inertia about the strong axis in
                in^4. Defaults to 88.6.
            Iyy (float, optional): Moment of inertia about the weak axis in
                in^4. Defaults to 2.36.
            A (float, optional): Cross-sectional area in in^2. Defaults to
                4.16.
            G (float, optional): Shear modulus in ksi. Defaults to 12000.0.
            J (float, optional): Polar moment of inertia in in^4. Defaults to
                0.0704.
            mesh (int, optional): Number of discretizations per member. Defaults
                to 50.
            bracing (str, optional): Bracing type (e.g., "continuous"). Defaults
                to "continuous".
            shape (Shape | None, optional): Shape class with section properties.
                Defaults to None.

        Returns:
            Member: The created Member instance.

        Example:

            >>> M1 = frame.members.add_member(N1, N2)
            >>> M2 = frame.members.add_member(N2, N3)
        """
        self.count += 1

        if isinstance(shape, Shape):
            Ixx = shape.Ix
            Iyy = shape.Iy
            A = shape.A
            J = shape.J

        member = Member(
            self.nodes,
            node_i,
            node_j,
            i_release,
            j_release,
            E,
            Ixx,
            Iyy,
            A,
            G,
            J,
            mesh,
            bracing,
            shape
        )

        self.members[self.count] = member
        return member
