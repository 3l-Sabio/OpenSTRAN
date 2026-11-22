from dataclasses import dataclass, field, asdict

from .Coordinates import Coordinate
from .Loads import Loads
from .Node import Node
from .Units import NODE_SNAP_TOLERANCE

from typing import Any


@dataclass(slots=True)
class Nodes():
    """A container class for managing user-defined node objects in the structural model.

    Parameters:
        plane (str | None): The plane constraint associated with the nodes.
        count (int): The total number of nodes added.
        nodes (dict[int, Node]): Dictionary mapping node IDs to Node objects.
        x (list[float]): List of x-coordinates in inches.
        y (list[float]): List of y-coordinates in inches.
        z (list[float]): List of z-coordinates in inches.
        loads (Loads): The model's loads, to which the nodes, and the
            members that connect them, add their loads.
    """
    plane: str | None = None
    count: int = 0
    nodes: dict[int, Node] = field(default_factory=dict[int, Node])
    x: list[float] = field(default_factory=list[float])
    y: list[float] = field(default_factory=list[float])
    z: list[float] = field(default_factory=list[float])
    loads: Loads = field(default_factory=Loads)

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        Returns:
            dict[str, Any]: Dictionary of this instance's fields.
        """
        return asdict(self)

    def add_node(self, x: float, y: float, z: float, mesh_node: bool = False) -> Node:
        """Add a node to the model at the specified coordinates.

        Args:
            x (float): x-coordinate in inches.
            y (float): y-coordinate in inches.
            z (float): z-coordinate in inches.
            mesh_node (bool, optional): Whether this is a mesh node. Defaults to False.

        Returns:
            Node: The added or existing node object.

        Example:

            >>> N1 = frame.nodes.add_node(0, 0, 0)
            >>> N2 = frame.nodes.add_node(0, 120, 0)
            >>> N3 = frame.nodes.add_node(120, 120, 0)
            >>> N4 = frame.nodes.add_node(120, 0, 0)
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
                mesh_node=mesh_node,
                loads=self.loads
            )
            self.nodes[self.count] = node
        return node

    def find_node(self, x: float, y: float, z: float) -> Node | None:
        """Find a node in the model at the specified coordinates.

        Args:
            x (float): x-coordinate in inches.
            y (float): y-coordinate in inches.
            z (float): z-coordinate in inches.

        Returns:
            Node | None: The matching node object if found, None otherwise.
        """
        pointError: float = NODE_SNAP_TOLERANCE

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
