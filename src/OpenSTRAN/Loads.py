from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Nodes and members add their loads here, so these modules import this
    # one; the names are needed only for the annotations.
    from .Member import Member
    from .Node import Node


@dataclass(frozen=True, slots=True, eq=False)
class NodalLoad:
    """A force or moment applied to a node along a global axis.

    Parameters:
        node (Node): The loaded node.
        magnitude (float): In kips for a force, kip-inches for a moment.
        kind (str): 'force' or 'moment'.
        direction (str): Global axis, 'X', 'Y' or 'Z'.
    """
    node: Node
    magnitude: float
    kind: str
    direction: str


@dataclass(frozen=True, slots=True, eq=False)
class PointLoad:
    """A concentrated force on a member, applied to the node at its location.

    Parameters:
        member (Member): The loaded member.
        magnitude (float): In kips.
        direction (str): Global ('X', 'Y', 'Z') or member local ('x', 'y',
            'z') axis.
        location (float): Position along the span as a percentage (0-100%).
        node (Node): The node at the location.
    """
    member: Member
    magnitude: float
    direction: str
    location: float
    node: Node


@dataclass(frozen=True, slots=True, eq=False)
class DistributedLoad:
    """A linearly varying distributed force on part of a member.

    Parameters:
        member (Member): The loaded member.
        w1, w2 (float): Intensities at the start and end of the load, in
            kips per inch.
        direction (str): Global ('X', 'Y', 'Z') or member local ('x', 'y',
            'z') axis.
        loc1, loc2 (float): Start and end of the load along the span, as
            percentages (0-100%).
    """
    member: Member
    w1: float
    w2: float
    direction: str
    loc1: float
    loc2: float


type Load = NodalLoad | PointLoad | DistributedLoad


class Loads:
    """The loads applied to a model, kept as ``Model.loads``.

    ``Node.add_load``, ``Member.add_point_load`` and
    ``Member.add_distributed_load`` record their loads here, in the order of
    the calls, and each solve builds the force vector and the span loads of
    the submembers from these records.

    Not a dataclass: nodes refer to it, so ``dataclasses.asdict`` of a node
    would loop between the two.
    """

    def __init__(self) -> None:
        self._loads: list[Load] = []

    def __repr__(self) -> str:
        return (f"<Loads: {len(self.nodal)} nodal, {len(self.point)} point, "
                f"{len(self.distributed)} distributed>")

    def __iter__(self) -> Iterator[Load]:
        """Every load, in the order it was added."""
        return iter(tuple(self._loads))

    def __len__(self) -> int:
        return len(self._loads)

    @property
    def nodal(self) -> tuple[NodalLoad, ...]:
        """The nodal loads, in the order they were added."""
        return tuple(x for x in self._loads if isinstance(x, NodalLoad))

    @property
    def point(self) -> tuple[PointLoad, ...]:
        """The point loads on members, in the order they were added."""
        return tuple(x for x in self._loads if isinstance(x, PointLoad))

    @property
    def distributed(self) -> tuple[DistributedLoad, ...]:
        """The distributed loads on members, in the order they were added."""
        return tuple(
            x for x in self._loads if isinstance(x, DistributedLoad))

    def add_nodal_load(
        self, node: Node, magnitude: float, kind: str, direction: str
    ) -> NodalLoad:
        """Record a nodal load; see ``Node.add_load``."""
        load = NodalLoad(node, magnitude, kind, direction)
        self._loads.append(load)
        return load

    def add_point_load(
        self,
        member: Member,
        magnitude: float,
        direction: str,
        location: float,
        node: Node
    ) -> PointLoad:
        """Record a point load on a member; see ``Member.add_point_load``."""
        load = PointLoad(member, magnitude, direction, location, node)
        self._loads.append(load)
        return load

    def add_distributed_load(
        self,
        member: Member,
        w1: float,
        w2: float,
        direction: str,
        loc1: float,
        loc2: float
    ) -> DistributedLoad:
        """Record a distributed load on a member; see
        ``Member.add_distributed_load``."""
        load = DistributedLoad(member, w1, w2, direction, loc1, loc2)
        self._loads.append(load)
        return load
