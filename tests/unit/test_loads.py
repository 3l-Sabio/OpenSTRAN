"""The loads of a model, kept as Model.loads and applied at each solve.

Each test builds its own model, mostly a cantilever along X fixed at the
origin, in kips and inches.
"""
import dataclasses

import pytest

from OpenSTRAN import Model
from OpenSTRAN.Coordinates import Coordinate
from OpenSTRAN.Loads import DistributedLoad, NodalLoad, PointLoad
from OpenSTRAN.Node import Node

L = 120.0     # in
E = 29000.0   # ksi
I = 100.0     # in^4
P = 2.0       # kips


def test_loads_are_recorded_as_given():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=4)

    tip.add_load(-P, 'force', 'Y')
    member.add_distributed_load(-0.1, -0.2, 'z', 25, 75)
    member.add_point_load(P, 'X', 50)
    tip.add_load(10.0, 'moment', 'Z')

    loads = model.loads
    assert len(loads) == 4
    assert [type(load) for load in loads] == [
        NodalLoad, DistributedLoad, PointLoad, NodalLoad]
    force, moment = loads.nodal
    assert force.node is tip
    assert (force.magnitude, force.kind, force.direction) == (
        -P, 'force', 'Y')
    assert moment.node is tip
    assert (moment.magnitude, moment.kind, moment.direction) == (
        10.0, 'moment', 'Z')
    (point,) = loads.point
    assert point.member is member
    assert point.node is model.nodes.find_node(L/2, 0, 0)
    assert (point.magnitude, point.direction, point.location) == (P, 'X', 50)
    (span,) = loads.distributed
    assert span.member is member
    assert (span.w1, span.w2, span.direction, span.loc1, span.loc2) == (
        -0.1, -0.2, 'z', 25, 75)
    with pytest.raises(dataclasses.FrozenInstanceError):
        force.magnitude = 0.0  # type: ignore[misc]


def test_solving_twice_gives_identical_results():
    # Each solve builds the force vector and the span loads afresh, so no
    # load is applied twice.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, J=50.0, mesh=4)
    tip.add_load(-P, 'force', 'Y')
    tip.add_load(-10.0, 'moment', 'X')
    member.add_point_load(-P, 'Z', 50)
    member.add_distributed_load(-0.1, -0.05, 'Y', 0, 100)

    first = model.solve()
    second = model.solve()

    assert first.node(base).Ry == pytest.approx(P + 0.075*L)
    assert first.node(base).Rz == pytest.approx(P)
    assert first.node(base).Rmx == pytest.approx(10.0)
    for node in model.nodes.nodes.values():
        assert second.node(node) == first.node(node)
    for a, b in zip(first.member(member).submembers,
                    second.member(member).submembers, strict=True):
        assert dict(b.forces) == dict(a.forces)
        assert (b.w_major, b.w_minor) == (a.w_major, a.w_minor)


def test_point_load_in_a_local_direction():
    # A cantilever inclined in the XY plane, with local x along (0.6, 0.8)
    # and local y along (-0.8, 0.6), loaded at the tip across its axis.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(72.0, 96.0, 0)   # 120 in long
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=2)
    member.add_point_load(-P, 'y', 100)

    results = model.solve()
    deflection = P*L**3/(3*E*I)   # along local -y
    assert results.node(base).Rx == pytest.approx(-0.8*P)
    assert results.node(base).Ry == pytest.approx(0.6*P)
    assert results.node(base).Rmz == pytest.approx(P*L)
    assert results.node(tip).Ux == pytest.approx(0.8*deflection)
    assert results.node(tip).Uy == pytest.approx(-0.6*deflection)
    assert results.member(member).submembers[0].forces['axial'] == \
        pytest.approx((0.0, 0.0), abs=1e-9)


def test_an_unknown_load_direction_raises_before_creating_nodes():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    member = model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=4)

    with pytest.raises(ValueError, match='global'):
        member.add_point_load(-P, 'Q', 50)
    with pytest.raises(ValueError, match='global or local axis'):
        member.add_distributed_load(-0.1, -0.1, 'Q', 25, 75)
    assert len(model.nodes.nodes) == 2
    assert len(model.loads) == 0


def test_a_node_outside_a_model_cannot_take_a_load():
    node = Node(Coordinate(0, 0, 0), node_ID=1)
    with pytest.raises(RuntimeError, match='add_node'):
        node.add_load(-P, 'force', 'Y')
