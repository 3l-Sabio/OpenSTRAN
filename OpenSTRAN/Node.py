from dataclasses import dataclass, field, asdict

from .Coordinates import Coordinate

from typing import Any


@dataclass(slots=True)
class Node():
    """A class representing a node in the structural analysis model.

    :ivar coordinates: The coordinate object defining the node's position
    :type coordinates: Coordinate
    :ivar node_ID: Unique identifier for the node
    :type node_ID: int
    :ivar mesh_node: Indicates if this is a mesh node. Defaults to False
    :type mesh_node: bool
    :ivar Fx: Applied force in the x-direction in kips. Defaults to 0.0
    :type Fx: float
    :ivar Fy: Applied force in the y-direction in kips. Defaults to 0.0
    :type Fy: float
    :ivar Fz: Applied force in the z-direction in kips. Defaults to 0.0
    :type Fz: float
    :ivar Mx: Applied moment about the x-axis in kip-ft. Defaults to 0.0
    :type Mx: float
    :ivar My: Applied moment about the y-axis in kip-ft. Defaults to 0.0
    :type My: float
    :ivar Mz: Applied moment about the z-axis in kip-ft. Defaults to 0.0
    :type Mz: float
    :ivar restraint: List of 6 integers indicating restrained degrees of freedom [Ux, Uy, Uz, φx, φy, φz]. Defaults to [0, 0, 0, 0, 0, 0]
    :type restraint: list[int]
    :ivar plane: The plane associated with the node. Defaults to None
    :type plane: str | None
    """
    coordinates: Coordinate
    node_ID: int
    mesh_node: bool = False
    Fx: float = 0.0
    Fy: float = 0.0
    Fz: float = 0.0
    Mx: float = 0.0
    My: float = 0.0
    Mz: float = 0.0
    Ux: float = 0.0
    Uy: float = 0.0
    Uz: float = 0.0
    phi_x: float = 0.0
    phi_y: float = 0.0
    phi_z: float = 0.0
    eFx: float = 0.0
    eFy: float = 0.0
    eFz: float = 0.0
    eMx: float = 0.0
    eMy: float = 0.0
    eMz: float = 0.0
    Rx: float = 0.0
    Ry: float = 0.0
    Rz: float = 0.0
    Rmx: float = 0.0
    Rmy: float = 0.0
    Rmz: float = 0.0
    plane: str | None = None
    restraint: list[int] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0])

    def __post_init__(self) -> None:
        """Set default restraints based on the plane constraint.

        If a plane is specified, sets the appropriate out-of-plane restraints.
        """
        if self.plane is None:
            return
        elif self.plane == 'xy':
            self.restraint = [0, 0, 1, 1, 1, 0]
        elif self.plane == 'yz':
            self.restraint = [1, 0, 0, 0, 1, 1]
        elif self.plane == 'zx':
            self.restraint = [0, 1, 0, 1, 0, 1]

    def properties(self) -> dict[str, Any]:
        """Return the dataclass properties as a dictionary.

        :returns: Dictionary of this instance's fields
        :rtype: dict[str, Any]
        """
        return asdict(self)

    def add_restraint(self, restraint: list[int]) -> None:
        """Add restraint to the nodal degrees of freedom.

        :param restraint: List of 6 integers (0 or 1) indicating which degrees of freedom are restrained.
            Format: [Ux, Uy, Uz, φx, φy, φz], where 1 means restrained and 0 means free.
            Examples:
            
            - Pinned node: [1, 1, 1, 0, 0, 0]
            - Fixed node: [1, 1, 1, 1, 1, 1]
            - Roller in x-direction: [0, 1, 1, 0, 0, 0]
        :type restraint: list[int]
        :raises ValueError: If restraint is not a list of exactly 6 integers, each being 0 or 1
        """
        # check the user defined list is properly formatted
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

        :param mag: Magnitude of the load. Units are kips for forces and kip-ft for moments.
        :type mag: float
        :param lType: Type of load. Either 'moment' or 'force'. Defaults to 'moment'.
        :type lType: str
        :param direction: Direction of the load. 'X', 'Y', or 'Z'. Defaults to 'y'.
        :type direction: str
        :note: For moments, the magnitude is multiplied by 12 (kip-in to kip-ft conversion)
        """

        if lType == 'moment':
            if direction == 'X':
                self.Mx += mag*12
            if direction == 'Y':
                self.My += mag*12
            if direction == 'Z':
                self.Mz += mag*12
        else:
            if direction == 'X':
                self.Fx += mag
            if direction == 'Y':
                self.Fy += mag
            if direction == 'Z':
                self.Fz += mag
