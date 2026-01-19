from dataclasses import dataclass, field, asdict

from .Coordinates import Coordinate
from .Node import Node

from typing import Any


@dataclass(slots=True)
class Nodes():
    """
    A container class for managing user-defined node objects in the structural model.

    Attributes:
        plane (str or None): The plane associated with the nodes.
        count (int): The total number of nodes added.
        nodes (dict[int, Node]): Dictionary mapping node IDs to Node objects.
        x (list[float]): List of x-coordinates.
        y (list[float]): List of y-coordinates.
        z (list[float]): List of z-coordinates.
    """
    plane: str | None = None
    count: int = 0
    nodes: dict[int, Node] = field(default_factory=dict[int, Node])
    x: list[float] = field(default_factory=list[float])
    y: list[float] = field(default_factory=list[float])
    z: list[float] = field(default_factory=list[float])

    def properties(self) -> dict[str, Any]:
        return asdict(self)

    def addNode(self, x: float, y: float, z: float, mesh_node: bool = False) -> Node:
        """
        Add a node to the model at the specified coordinates.

        Args:
            x (float): x coordinate in feet
            y (float): y coordinate in feet
            z (float): z coordinate in feet
            mesh_node (bool, optional): Whether this is a mesh node. Defaults to False.

        Returns:
            Node: The added or existing node object.

        Examples:
            N1 = frame.nodes.addNode(0,0,0)
            N2 = frame.nodes.addNode(0,10,0)
            N3 = frame.nodes.addNode(10,10,0)
            N4 = frame.nodes.addNode(10,0,0)
        """
        node: Node | None = self.findNode(x, y, z)
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

    def findNode(self, x: float, y: float, z: float) -> Node | None:
        """
        Find a node in the model at the specified coordinates.

        Args:
            x (float): x coordinate in feet
            y (float): y coordinate in feet
            z (float): z coordinate in feet

        Returns:
            Node or None: The matching node object if found, None otherwise.
        """

        # define a floating point error
        pointError: float = 1*10**-6

        # iterate through the model nodes
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
