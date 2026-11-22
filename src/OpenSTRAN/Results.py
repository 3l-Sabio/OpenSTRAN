from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .Member import Member
from .Node import Node
from .Submember import SubMember


# End force components of a submember, in local coordinates.
FORCE_KEYS = (
    'axial',
    'shear',
    'transverse shear',
    'torsional moments',
    'minor axis moments',
    'major axis moments',
)


@dataclass(frozen=True, slots=True)
class NodeResult:
    """Displacements and reactions of one node.

    Parameters:
        Ux, Uy, Uz (float): Translations in the global X, Y and Z directions.
        phi_x, phi_y, phi_z (float): Rotations about the global X, Y and Z
            axes, in radians.
        Rx, Ry, Rz (float): Reaction forces in the global X, Y and Z
            directions; zero at an unrestrained degree of freedom.
        Rmx, Rmy, Rmz (float): Reaction moments about the global X, Y and Z
            axes; zero at an unrestrained degree of freedom.
    """
    Ux: float
    Uy: float
    Uz: float
    phi_x: float
    phi_y: float
    phi_z: float
    Rx: float
    Ry: float
    Rz: float
    Rmx: float
    Rmy: float
    Rmz: float


@dataclass(frozen=True, slots=True, eq=False)
class SubMemberResult:
    """End displacements and end forces of one submember.

    Compared by identity, like the submember it belongs to.

    Parameters:
        submember (SubMember): The submember, as meshed for the analysis.
        displacements (np.ndarray): The 12 end displacements in the
            submember's local coordinates (a read-only copy).
        forces (Mapping[str, tuple[float, float]]): End forces in local
            coordinates, (i end, j end), for each key of ``FORCE_KEYS``
            (read-only). They are the forces the nodes apply to the
            submember's ends, including the fixed-end forces of span loads,
            so the axial force at the j end is positive in tension.
        second_order_axial (float): Axial force (j end, tension positive)
            whose geometric stiffness was included in the analysis; zero
            after a first-order analysis.
    """
    submember: SubMember
    displacements: np.ndarray
    forces: Mapping[str, tuple[float, float]]
    second_order_axial: float

    def __post_init__(self) -> None:
        # Keep read-only copies, so that neither a later solve nor the
        # caller can change the results.
        displacements = np.array(self.displacements, dtype=float).reshape(-1)
        displacements.setflags(write=False)
        object.__setattr__(self, 'displacements', displacements)
        object.__setattr__(
            self, 'forces', MappingProxyType(dict(self.forces)))


@dataclass(frozen=True, slots=True, eq=False)
class MemberResult:
    """Results of one member.

    Compared by identity, like the member it belongs to.

    Parameters:
        member (Member): The member.
        submembers (tuple[SubMemberResult, ...]): Results of the member's
            submembers, from its i end to its j end, as meshed for the
            analysis.
    """
    member: Member
    submembers: tuple[SubMemberResult, ...]


class Results:
    """Results of one analysis, as returned by ``Model.solve()``.

    The results do not change after the analysis: a later solve of the same
    model returns a new object.

    Parameters:
        members (tuple[MemberResult, ...]): Results of each member, in the
            order the members were added.
        second_order (bool): Whether the analysis was second order.
        iterations (int): Number of iterations of a second-order analysis;
            0 for a first-order analysis.

    Maxima, each the largest absolute value over the model: reactions
    ``Rx_max``, ``Ry_max``, ``Rz_max``, ``Rmx_max``, ``Rmy_max``,
    ``Rmz_max``; translations ``Ux_max``, ``Uy_max``, ``Uz_max``; member
    forces ``axial_max``, ``torque_max``, ``Vy_max``, ``Vz_max``,
    ``Mzz_max``, ``Myy_max``. Member force maxima include the peaks between
    the ends of each submember.
    """

    def __init__(
        self,
        nodes: list[Node],
        displacements: np.ndarray,
        reactions: np.ndarray,
        members: list[MemberResult],
        force_extrema: dict[str, tuple[float, float]],
        second_order: bool,
        iterations: int,
    ) -> None:
        """Store the results of an analysis.

        Args:
            nodes: The nodes of the model, in degree-of-freedom order.
            displacements: Global displacement vector (6 per node).
            reactions: Global reaction vector (6 per node), zero at the
                unrestrained degrees of freedom.
            members: Results of each member.
            force_extrema: (max, min) of each member force component over
                the whole model, keyed as ``FORCE_KEYS``.
            second_order: Whether the analysis was second order.
            iterations: Iterations of a second-order analysis.
        """
        self._nodes = tuple(nodes)
        self._U = np.array(displacements, dtype=float).reshape(-1)
        self._R = np.array(reactions, dtype=float).reshape(-1)
        self._U.setflags(write=False)
        self._R.setflags(write=False)
        self._members = {id(m.member): m for m in members}
        self._force_extrema = dict(force_extrema)
        self._second_order = second_order
        self._iterations = iterations

    def __repr__(self) -> str:
        kind = 'second-order' if self.second_order else 'first-order'
        return (f"<Results: {kind}, {len(self._nodes)} nodes, "
                f"{len(self._members)} members>")

    @property
    def second_order(self) -> bool:
        return self._second_order

    @property
    def iterations(self) -> int:
        return self._iterations

    @property
    def members(self) -> tuple[MemberResult, ...]:
        return tuple(self._members.values())

    def node(self, node: Node) -> NodeResult:
        """Displacements and reactions of a node.

        Args:
            node (Node): A node of the analysed model.

        Returns:
            NodeResult: The node's results.

        Raises:
            KeyError: If the node was not part of the analysis.
        """
        k = node.node_ID - 1
        if not (0 <= k < len(self._nodes) and self._nodes[k] is node):
            raise KeyError(
                f"Node {node.node_ID} was not part of this analysis.")
        U = self._U[6*k:6*k + 6]
        R = self._R[6*k:6*k + 6]
        return NodeResult(*(float(v) for v in U), *(float(v) for v in R))

    def member(self, member: Member) -> MemberResult:
        """Results of a member.

        Args:
            member (Member): A member of the analysed model.

        Returns:
            MemberResult: The member's results.

        Raises:
            KeyError: If the member was not part of the analysis.
        """
        result = self._members.get(id(member))
        if result is None or result.member is not member:
            raise KeyError("The member was not part of this analysis.")
        return result

    def _max_abs(self, values: np.ndarray) -> float:
        return float(np.max(np.abs(values), initial=0.0))

    def _force_max(self, key: str) -> float:
        return max((abs(v) for v in self._force_extrema[key]), default=0.0)

    @property
    def Rx_max(self) -> float:
        return self._max_abs(self._R[0::6])

    @property
    def Ry_max(self) -> float:
        return self._max_abs(self._R[1::6])

    @property
    def Rz_max(self) -> float:
        return self._max_abs(self._R[2::6])

    @property
    def Rmx_max(self) -> float:
        return self._max_abs(self._R[3::6])

    @property
    def Rmy_max(self) -> float:
        return self._max_abs(self._R[4::6])

    @property
    def Rmz_max(self) -> float:
        return self._max_abs(self._R[5::6])

    @property
    def Ux_max(self) -> float:
        return self._max_abs(self._U[0::6])

    @property
    def Uy_max(self) -> float:
        return self._max_abs(self._U[1::6])

    @property
    def Uz_max(self) -> float:
        return self._max_abs(self._U[2::6])

    @property
    def axial_max(self) -> float:
        return self._force_max('axial')

    @property
    def torque_max(self) -> float:
        return self._force_max('torsional moments')

    @property
    def Vy_max(self) -> float:
        return self._force_max('shear')

    @property
    def Vz_max(self) -> float:
        return self._force_max('transverse shear')

    @property
    def Mzz_max(self) -> float:
        return self._force_max('major axis moments')

    @property
    def Myy_max(self) -> float:
        return self._force_max('minor axis moments')
