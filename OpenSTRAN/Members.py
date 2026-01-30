from .Member import Member
from .Nodes import Nodes
from .Node import Node

from dataclasses import dataclass, field, asdict

from typing import Any


@dataclass(slots=True)
class Members():
    """
    Object that holds the member objects

    Attributes:
        nodes (Nodes): Reference to the global `Nodes` collection.
        count (int): Number of members added to the collection.
        members (Dict[int, Member]): Mapping of member id to `Member`.
    """
    nodes: Nodes
    count: int = 0
    members: dict[int, Member] = field(default_factory=dict[int, Member])

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        Returns:
            Dict[str, Any]: Dictionary of this instance's fields.
        """
        return asdict(self)

    def addMember(
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
        shape: str = "W12x14",
    ) -> Member:
        """Method to add member objects to the model.

        :param node_i: Start `Node` of the member.
        :type node_i: Node
        :param node_j: End `Node` of the member.
        :type node_j: Node
        :param i_release: True if start node is released (pinned).
        :type i_release: bool
        :param j_release: True if end node is released (pinned).
        :type j_release: bool
        :param E: Young's Modulus [ksi].
        :type E: float
        :param Ixx: Moment of inertia about the strong axis [in^4].
        :type Ixx: float
        :param Iyy: Moment of inertia about the weak axis [in^4].
        :type Iyy: float
        :param A: Cross-sectional area [in^2].
        :type A: float
        :param G: Shear Modulus [ksi].
        :type G: float
        :param J: Polar moment of inertia [in^4].
        :type J: float
        :param mesh: Number of discretizations per member.
        :type mesh: int
        :param bracing: Bracing type (e.g., "continuous").
        :type bracing: str
        :param shape: Section shape name (e.g., "W12x14").
        :type shape: str

        :returns: The created `Member` instance.
        :rtype: Member

        Usage example::

            M1 = frame.members.addMember(N1, N2)
            M2 = frame.members.addMember(N2, N3)
        """
        self.count += 1

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
