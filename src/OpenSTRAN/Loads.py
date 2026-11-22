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

    Loads are added with ``add_nodal_load``, ``add_point_load`` and
    ``add_distributed_load``, or with ``Node.add_load``,
    ``Member.add_point_load`` and ``Member.add_distributed_load``, which call
    them. They are kept in the order they were added, and each solve builds
    the force vector and the span loads of the submembers from them.
    ``clear`` removes them all.

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

    def clear(self) -> None:
        """Remove every load, for example to load the model differently.

        The nodes that member loads created stay in the model.
        """
        self._loads.clear()

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
        """Add a force or moment to a node of the model.

        ``node.add_load(magnitude, kind, direction)`` does the same.

        Args:
            node (Node): A node of this model.
            magnitude (float): In kips for a force, kip-inches for a moment.
            kind (str): 'force' or 'moment'.
            direction (str): Global axis, 'X', 'Y' or 'Z'.

        Returns:
            NodalLoad: The load as recorded.

        Raises:
            ValueError: If the node is not part of this model, or the kind or
                direction is not one of those above.
        """
        if node.loads is not self:
            raise ValueError("The node is not part of this model.")
        if kind not in ('force', 'moment'):
            raise ValueError(
                f"Nodal load kind {kind!r} must be 'force' or 'moment'.")
        if direction not in ('X', 'Y', 'Z'):
            raise ValueError(
                f"Nodal load direction {direction!r} must be a global axis, "
                "'X', 'Y' or 'Z'.")
        load = NodalLoad(node, magnitude, kind, direction)
        self._loads.append(load)
        return load

    def add_point_load(
        self,
        member: Member,
        magnitude: float,
        direction: str,
        location: float
    ) -> PointLoad:
        """Add a concentrated force to a member of the model.

        The force is applied to the node at its location, which is created
        (see ``Member.add_node``) if no node is there.
        ``member.add_point_load(magnitude, direction, location)`` does the
        same.

        Args:
            member (Member): A member of this model.
            magnitude (float): In kips.
            direction (str): Global ('X', 'Y', 'Z') or member local ('x', 'y',
                'z') axis.
            location (float): Position along the span as a percentage
                (0-100%).

        Returns:
            PointLoad: The load as recorded.

        Raises:
            ValueError: If the member is not part of this model, or the
                direction is not one of those above. No node is created.
        """
        self._check_member_load(member, direction)
        node = member.add_node(location)
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
        """Add a linearly varying distributed force to part of a member of
        the model.

        Nodes are created at the start and end of the load (see
        ``Member.add_node``) where there are none, so that the mesh has
        submembers that end there. ``member.add_distributed_load(w1, w2,
        direction, loc1, loc2)`` does the same.

        Args:
            member (Member): A member of this model.
            w1, w2 (float): Intensities at the start and end of the load, in
                kips per inch.
            direction (str): Global ('X', 'Y', 'Z') or member local ('x', 'y',
                'z') axis.
            loc1, loc2 (float): Start and end of the load along the span, as
                percentages (0-100%).

        Returns:
            DistributedLoad: The load as recorded.

        Raises:
            ValueError: If the member is not part of this model, or the
                direction is not one of those above. No node is created.
        """
        self._check_member_load(member, direction)
        member.add_node(loc1)
        member.add_node(loc2)
        load = DistributedLoad(member, w1, w2, direction, loc1, loc2)
        self._loads.append(load)
        return load

    def _check_member_load(self, member: Member, direction: str) -> None:
        """Raise ValueError unless the member is part of this model and the
        direction is a global or local axis."""
        if member.nodes.loads is not self:
            raise ValueError("The member is not part of this model.")
        if direction not in ('X', 'Y', 'Z', 'x', 'y', 'z'):
            raise ValueError(
                f"Load direction {direction!r} must be global ('X', 'Y', "
                "'Z') or local ('x', 'y', 'z').")
