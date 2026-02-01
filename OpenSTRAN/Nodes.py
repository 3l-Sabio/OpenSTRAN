from dataclasses import dataclass, field, asdict

from .Coordinates import Coordinate
from .Node import Node

from typing import Any


@dataclass(slots=True)
class Nodes():
    """A container class for managing user-defined node objects in the structural model.

    :ivar plane: The plane constraint associated with the nodes
    :type plane: str | None
    :ivar count: The total number of nodes added
    :type count: int
    :ivar nodes: Dictionary mapping node IDs to Node objects
    :type nodes: dict[int, Node]
    :ivar x: List of x-coordinates
    :type x: list[float]
    :ivar y: List of y-coordinates
    :type y: list[float]
    :ivar z: List of z-coordinates
    :type z: list[float]
    """
    plane: str | None = None
    count: int = 0
    nodes: dict[int, Node] = field(default_factory=dict[int, Node])
    x: list[float] = field(default_factory=list[float])
    y: list[float] = field(default_factory=list[float])
    z: list[float] = field(default_factory=list[float])

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        :returns: Dictionary of this instance's fields
        :rtype: dict[str, Any]
        """
        return asdict(self)

    def add_node(self, x: float, y: float, z: float, mesh_node: bool = False) -> Node:
        """Add a node to the model at the specified coordinates.

        :param x: x-coordinate in feet
        :type x: float
        :param y: y-coordinate in feet
        :type y: float
        :param z: z-coordinate in feet
        :type z: float
        :param mesh_node: Whether this is a mesh node. Defaults to False.
        :type mesh_node: bool
        :returns: The added or existing node object
        :rtype: Node

        :Example:

            >>> N1 = frame.nodes.add_node(0, 0, 0)
            >>> N2 = frame.nodes.add_node(0, 10, 0)
            >>> N3 = frame.nodes.add_node(10, 10, 0)
            >>> N4 = frame.nodes.add_node(10, 0, 0)
        """
        node: Node | None = self.find_node(x, y, z)
        if node is None:
            self.count += 1
            self.x.append(x)
            self.y.append(y)
            self.z.append(z)
            coordinates: Coordinate = Coordinate(x, y, z)
            node = Node(
                coordinates=coordinates,
                node_ID=self.count,
                plane=self.plane,
                mesh_node=mesh_node
            )
            self.nodes[self.count] = node
        return node

    def find_node(self, x: float, y: float, z: float) -> Node | None:
        """Find a node in the model at the specified coordinates.

        :param x: x-coordinate in feet
        :type x: float
        :param y: y-coordinate in feet
        :type y: float
        :param z: z-coordinate in feet
        :type z: float
        :returns: The matching node object if found, None otherwise
        :rtype: Node | None
        """
        # Define a floating point error tolerance.
        pointError: float = 1*10**-6

        # Iterate through the model nodes.
        for node in self.nodes.values():
            x_e: float = node.coordinates.x
            y_e: float = node.coordinates.y
            z_e: float = node.coordinates.z
            if ((x_e - pointError) < x < (x_e + pointError) and (
                y_e - pointError) < y < (y_e + pointError) and (
                    z_e - pointError) < z < (z_e + pointError)):
                return node
            else:
                continue
        return None
