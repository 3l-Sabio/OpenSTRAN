from dataclasses import dataclass, field, asdict

from .Coordinates import Coordinate
from .Loads import Loads

from typing import Any


# The restraints that keep the nodes of a two-dimensional model in its plane.
PLANE_RESTRAINTS: dict[str, tuple[int, ...]] = {
    'xy': (0, 0, 1, 1, 1, 0),
    'yz': (1, 0, 0, 0, 1, 1),
    'zx': (0, 1, 0, 1, 0, 1),
}


@dataclass(slots=True)
class Node():
    """A class representing a node in the structural analysis model.

    Parameters:
        coordinates (Coordinate): The coordinate object defining the node's position.
        node_ID (int): Unique identifier for the node.
        mesh_node (bool): Indicates if this is a mesh node. Defaults to False.
        restraint (list[int]): List of 6 integers indicating restrained degrees of freedom
            [Ux, Uy, Uz, φx, φy, φz]. Defaults to [0, 0, 0, 0, 0, 0].
        plane (str | None): The plane associated with the node. Defaults to None.
    """
    coordinates: Coordinate
    node_ID: int
    mesh_node: bool = False
    plane: str | None = None
    restraint: list[int] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0])
    # The model's loads, which add_load adds to; set by Nodes.add_node.
    _loads: Loads | None = field(
        default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Set default restraints based on the plane constraint.

        If a plane is specified, sets the appropriate out-of-plane restraints.
        """
        if self.plane in PLANE_RESTRAINTS:
            self.restraint = list(PLANE_RESTRAINTS[self.plane])

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        Returns:
            dict[str, Any]: Dictionary of this instance's fields.
        """
        return asdict(self)

    def add_restraint(self, restraint: list[int]) -> None:
        """Add restraint to the nodal degrees of freedom.

        Args:
            restraint (list[int]): List of 6 integers (0 or 1) indicating which degrees
                of freedom are restrained. Format: [Ux, Uy, Uz, φx, φy, φz], where 1
                means restrained and 0 means free. Examples:

                * Pinned node: [1, 1, 1, 0, 0, 0]
                * Fixed node: [1, 1, 1, 1, 1, 1]
                * Roller in x-direction: [0, 1, 1, 0, 0, 0]

        Raises:
            ValueError: If restraint is not a list of exactly 6 integers, each being 0 or 1.
        """        # check the user defined list is properly formatted
        if type(restraint) == list and len(restraint) == 6 and restraint == [n for n in restraint if n in [0, 1]]:
            # restrain the node
            self.restraint = restraint
        else:
            raise ValueError('{msg1}\n{msg2}\n{msg3}\n{msg4}\n{msg5}\n{msg6}'.format(
                msg1=str('restraint: "{r}" not recognized.'.format(
                    r=restraint
                )
                ),
                msg2=str('restraint must be a list of 0s and 1s:'),
                msg3=str('Degrees of Freedom: [Ux, Uy, Uz, φx, φy, φz]'),
                msg4=str("Pinned Node: [1,1,1,0,0,0]"),
                msg5=str("Fixed Node: [1,1,1,1,1,1]"),
                msg6=str("Roller in the x direction: [0,1,1,0,0,0]")
            ))

    def add_load(self, mag: float, lType: str = 'moment', direction: str = 'y') -> None:
        """Add a load to the node.

        The load is recorded in the model's loads (``Model.loads``) and
        applied when the model is solved.

        Args:
            mag (float): Magnitude of the load. Units are kips for forces and kip-in for moments.
            lType (str, optional): Type of load. Either 'moment' or 'force'. Defaults to 'moment'.
            direction (str, optional): Direction of the load. 'X', 'Y', or 'Z'. Defaults to 'y'.

        Raises:
            RuntimeError: If the node was not added to a model with
                ``Nodes.add_node``.
        """
        if direction not in ('X', 'Y', 'Z'):
            return
        if self._loads is None:
            raise RuntimeError(
                "The node belongs to no model: add nodes with "
                "Nodes.add_node.")
        self._loads.add_nodal_load(
            self, mag, 'moment' if lType == 'moment' else 'force', direction)
