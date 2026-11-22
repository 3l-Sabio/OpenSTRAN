"""The loads of a model, kept as Model.loads and applied at each solve.

Each test builds its own model, mostly a cantilever along X fixed at the
origin, in kips and inches.
"""
import dataclasses

import pytest

from OpenSTRAN import Model
from OpenSTRAN.Coordinates import Coordinate
from OpenSTRAN.Loads import DistributedLoad, Loads, NodalLoad, PointLoad
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

    added = [
        tip.add_load(-P, 'force', 'Y'),
        member.add_distributed_load(-0.1, -0.2, 'z', 25, 75),
        member.add_point_load(P, 'X', 50),
        tip.add_load(10.0, 'moment', 'Z'),
    ]

    loads = model.loads
    assert loads is model.nodes.loads
    assert list(loads) == added   # each method returns the load it recorded
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


def test_clearing_the_loads_lets_the_model_take_new_ones():
    # add_load adds to the loads already on a node, so a script that loads
    # the model differently removes them first.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=4)
    tip.add_load(-P, 'force', 'Y')
    first = model.solve()

    # The load set itself cannot be replaced: the nodes keep adding to it.
    with pytest.raises(AttributeError):
        model.loads = Loads()  # type: ignore[misc]
    model.loads.clear()
    assert len(model.loads) == 0
    tip.add_load(-2*P, 'force', 'Z')
    second = model.solve()

    assert first.node(base).Ry == pytest.approx(P)
    assert first.node(base).Rz == pytest.approx(0.0, abs=1e-9)
    assert second.node(base).Ry == pytest.approx(0.0, abs=1e-9)
    assert second.node(base).Rz == pytest.approx(2*P)
    assert second.node(tip).Uz == pytest.approx(-2*P*L**3/(3*E*I))


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
    with pytest.raises(ValueError, match='global'):
        member.add_distributed_load(-0.1, -0.1, 'Q', 25, 75)
    with pytest.raises(ValueError, match='global'):
        model.loads.add_point_load(member, -P, 'Q', 50)
    with pytest.raises(ValueError, match='global'):
        model.loads.add_distributed_load(member, -0.1, -0.1, 'Q', 25, 75)
    assert len(model.nodes.nodes) == 2
    assert len(model.loads) == 0


def test_an_unknown_nodal_load_kind_or_direction_raises():
    # These used to be applied as a force ('Moment') or dropped ('y', and
    # the default direction of add_load, which is now required).
    model = Model()
    tip = model.nodes.add_node(L, 0, 0)

    with pytest.raises(ValueError, match="'force' or 'moment'"):
        tip.add_load(10.0, 'Moment', 'Z')
    with pytest.raises(ValueError, match="'X', 'Y' or 'Z'"):
        tip.add_load(-P, 'force', 'y')
    with pytest.raises(ValueError, match="'force' or 'moment'"):
        model.loads.add_nodal_load(tip, 10.0, 'Moment', 'Z')
    with pytest.raises(ValueError, match="'X', 'Y' or 'Z'"):
        model.loads.add_nodal_load(tip, -P, 'force', 'y')
    with pytest.raises(TypeError):
        tip.add_load(-P)  # type: ignore[call-arg]
    assert len(model.loads) == 0


def test_loads_added_through_the_model_match_the_member_and_node_methods():
    # model.loads.add_* create the nodes at a member load's location and
    # extents, as the member methods do: without the nodes at its extents,
    # a partial distributed load gives wrong moments within the span.
    models = []
    for through_loads in (False, True):
        model = Model()
        base = model.nodes.add_node(0, 0, 0)
        tip = model.nodes.add_node(L, 0, 0)
        base.restraint = [1, 1, 1, 1, 1, 1]
        member = model.members.add_member(
            base, tip, E=E, Ixx=I, Iyy=I, J=50.0, mesh=4)
        if through_loads:
            model.loads.add_distributed_load(
                member, -0.1, -0.05, 'Y', 15, 55)
            model.loads.add_point_load(member, P, 'z', 80)
            model.loads.add_nodal_load(tip, -10.0, 'moment', 'X')
        else:
            member.add_distributed_load(-0.1, -0.05, 'Y', 15, 55)
            member.add_point_load(P, 'z', 80)
            tip.add_load(-10.0, 'moment', 'X')
        models.append((model, member, model.solve()))

    (a, member_a, first), (b, member_b, second) = models
    # The two ends, the three nodes of the loads and three of the mesh.
    assert len(b.nodes.nodes) == len(a.nodes.nodes) == 8
    assert [type(load) for load in b.loads] == [type(load) for load in a.loads]
    for node_a, node_b in zip(a.nodes.nodes.values(), b.nodes.nodes.values(),
                              strict=True):
        assert node_b.coordinates.coordinates == node_a.coordinates.coordinates
        assert second.node(node_b) == first.node(node_a)
    for location in (10, 15, 35, 55, 80, 90):
        assert second.member(member_b).moment(location) == \
            first.member(member_a).moment(location)
    w_bar = 0.075*0.4*L   # resultant of the distributed load, kips
    assert first.node(a.nodes.nodes[1]).Ry == pytest.approx(w_bar)


def test_a_load_on_another_models_node_or_member_raises():
    # The solver finds a node by its number, so a load on a node of another
    # model would act on whichever node of this model has the same number.
    first = Model()
    base = first.nodes.add_node(0, 0, 0)
    tip = first.nodes.add_node(L, 0, 0)
    member = first.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=4)
    second = Model()
    second.nodes.add_node(0, 0, 0)
    second.nodes.add_node(L, 0, 0)
    outside = Node(Coordinate(L, 0, 0), node_ID=2)

    with pytest.raises(ValueError, match='not part of this model'):
        second.loads.add_nodal_load(tip, -P, 'force', 'Y')
    with pytest.raises(ValueError, match='not part of this model'):
        second.loads.add_nodal_load(outside, -P, 'force', 'Y')
    with pytest.raises(ValueError, match='not part of this model'):
        second.loads.add_point_load(member, -P, 'Y', 50)
    with pytest.raises(ValueError, match='not part of this model'):
        second.loads.add_distributed_load(member, -0.1, -0.1, 'Y', 25, 75)
    assert len(first.nodes.nodes) == len(second.nodes.nodes) == 2
    assert len(first.loads) == len(second.loads) == 0


def test_a_node_outside_a_model_cannot_take_a_load():
    node = Node(Coordinate(0, 0, 0), node_ID=1)
    with pytest.raises(RuntimeError, match='add_node'):
        node.add_load(-P, 'force', 'Y')
