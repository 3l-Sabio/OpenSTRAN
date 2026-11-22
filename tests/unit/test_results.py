"""The Results object returned by Model.solve().

Each test builds its own model, mostly a cantilever along X fixed at the
origin, in kips and inches. Members along X have local x, y, z along
global X, Y, Z.
"""
import dataclasses
import math

import numpy as np
import pytest

from OpenSTRAN import Model
from OpenSTRAN.Members import Members
from OpenSTRAN.Nodes import Nodes
from OpenSTRAN.Results import Results
from OpenSTRAN.Solver import Solver

L = 120.0     # in
E = 29000.0   # ksi
I = 100.0     # in^4
P = 2.0       # kips
MESH = 4


def test_solve_returns_the_results_and_keeps_them():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    assert model.results is None
    results = model.solve()
    assert results is model.results
    assert results.second_order is False
    assert results.iterations == 0


def test_node_results():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    results = model.solve()
    assert results.node(tip).Uy == pytest.approx(-P*L**3/(3*E*I))
    assert results.node(tip).phi_z == pytest.approx(-P*L**2/(2*E*I))
    assert results.node(base).Ry == pytest.approx(P)
    assert results.node(base).Rmz == pytest.approx(P*L)
    assert results.node(base).Uy == 0.0


def test_reactions_are_zero_at_unrestrained_degrees_of_freedom():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    r = model.solve().node(tip)
    assert (r.Rx, r.Ry, r.Rz, r.Rmx, r.Rmy, r.Rmz) == (0, 0, 0, 0, 0, 0)


def test_reaction_at_a_support_on_a_load_node(
        capsys: pytest.CaptureFixture[str]):
    # A support on the node a point load created. Before the results
    # object, its reaction was dropped from the node, the maxima and the
    # printed reactions.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=2)
    member.add_point_load(-P, 'Y', 50)
    assert len(model.nodes.nodes) == 3       # the load created a node
    prop = model.nodes.add_node(L/2, 0, 0)   # returns the load's node
    assert len(model.nodes.nodes) == 3
    assert not prop.mesh_node                # now a user node
    prop.restraint = [0, 1, 0, 0, 0, 0]

    results = model.solve()
    assert results.node(prop).Ry == pytest.approx(P)
    assert results.node(base).Ry == pytest.approx(0.0, abs=1e-12)
    assert results.Ry_max == pytest.approx(P)
    model.reactions()
    assert (f'\tNode {prop.node_ID}:\n\t\tRx = 0.00 kips\n\t\tRy = 2.00 kips'
            in capsys.readouterr().out)


def test_maxima_need_no_extra_call():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    results = model.solve()
    # No max_deflection() call is needed, unlike the model attributes.
    assert results.Uy_max == pytest.approx(P*L**3/(3*E*I))
    assert results.Ux_max == 0.0
    assert results.Ry_max == pytest.approx(P)
    assert results.Rmz_max == pytest.approx(P*L)
    assert results.Mzz_max == pytest.approx(P*L)
    assert results.Vy_max == pytest.approx(P)
    assert results.axial_max == pytest.approx(0.0, abs=1e-12)


def test_end_forces_of_every_submember():
    # Tip loads that give all six end force components: tension N, shear P
    # along Y, shear Q along Z and a torque T about X.
    N, Q, T = 30.0, 1.5, 40.0
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, J=50.0, mesh=MESH)
    tip.add_load(N, 'force', 'X')
    tip.add_load(-P, 'force', 'Y')
    tip.add_load(-Q, 'force', 'Z')
    tip.add_load(T, 'moment', 'X')

    subs = model.solve().member(member).submembers
    assert len(subs) == MESH
    for k, sub in enumerate(subs):
        # From the i end to the j end of the member.
        a, b = k*L/MESH, (k + 1)*L/MESH
        assert sub.submember.node_i.coordinates.x == pytest.approx(a)
        # The forces the nodes apply to each end; statics of the part of
        # the cantilever beyond each end.
        f = sub.forces
        assert f['axial'] == pytest.approx((-N, N))
        assert f['shear'] == pytest.approx((P, -P))
        assert f['transverse shear'] == pytest.approx((Q, -Q))
        assert f['torsional moments'] == pytest.approx((-T, T))
        assert f['major axis moments'] == pytest.approx(((L - a)*P,
                                                         -(L - b)*P))
        assert f['minor axis moments'] == pytest.approx((-(L - a)*Q,
                                                         (L - b)*Q))
        assert sub.second_order_axial == 0.0
        assert sub.displacements.shape == (12,)
        # Constant along the span, in the sign convention of the i end.
        extrema = sub.force_extrema()
        assert extrema['axial'] == pytest.approx((-N, -N))
        assert extrema['torsional moments'] == pytest.approx((-T, -T))


def test_results_do_not_change_when_the_model_is_solved_again():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    first = model.solve()
    uy = first.node(tip).Uy
    moment = first.member(member).submembers[0].forces['major axis moments']
    displacements = first.member(member).submembers[-1].displacements.copy()

    tip.add_load(-P, 'force', 'Y')
    second = model.solve()

    assert second is not first
    assert second.node(tip).Uy == pytest.approx(2*uy)
    assert first.node(tip).Uy == uy
    assert first.Mzz_max == pytest.approx(P*L)
    assert second.Mzz_max == pytest.approx(2*P*L)
    assert first.member(member).submembers[0].forces[
        'major axis moments'] == moment
    np.testing.assert_array_equal(
        first.member(member).submembers[-1].displacements, displacements)


def test_results_keep_the_mesh_they_were_solved_with():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    results = model.solve()
    solved = [sub.submember for sub in results.member(member).submembers]
    member.generate_mesh()   # replaces member.submembers with new objects
    assert [sub.submember for sub in results.member(member).submembers] \
        == solved
    assert all(a is not b for a, b in
               zip(solved, member.submembers.values()))


def test_results_are_read_only():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    results = model.solve()
    sub = results.member(member).submembers[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        results.node(tip).Uy = 0.0  # type: ignore[misc]
    with pytest.raises(ValueError):
        sub.displacements[0] = 1.0
    with pytest.raises(TypeError):
        sub.forces['axial'] = (1.0, 1.0)  # type: ignore[index]
    with pytest.raises(AttributeError):
        results.second_order = True  # type: ignore[misc]
    with pytest.raises(AttributeError):
        results.iterations = 1  # type: ignore[misc]


def test_results_compare_by_identity():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    first = model.solve()
    second = model.solve()   # the same mesh and the same values
    sub = first.member(member).submembers[1]
    assert sub != second.member(member).submembers[1]
    assert first.member(member).submembers.index(sub) == 1
    assert first.member(member) != second.member(member)
    assert {sub: 1, first.member(member): 2}[sub] == 1   # hashable


def test_results_list_the_members_of_the_analysis():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    knee = model.nodes.add_node(L, 0, 0)
    tip = model.nodes.add_node(L, L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    beam = model.members.add_member(
        base, knee, E=E, Ixx=I, Iyy=I, mesh=MESH)
    post = model.members.add_member(
        knee, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(P, 'force', 'X')

    results = model.solve()
    assert len(results.members) == 2
    assert results.members[0].member is beam
    assert results.members[1].member is post
    assert all(m is results.member(m.member) for m in results.members)

    # A member added after the solve is not part of these results.
    later = model.members.add_member(
        tip, model.nodes.add_node(0, L, 0), E=E, Ixx=I, Iyy=I, mesh=MESH)
    assert len(results.members) == 2
    with pytest.raises(KeyError):
        results.member(later)
    model.maxMbrForces()   # the model maxima still come from the results
    assert model.Mzz_max == pytest.approx(P*L)


def test_node_or_member_outside_the_analysis_raises():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')
    results = model.solve()

    other = Model()
    other_base = other.nodes.add_node(0, 0, 0)   # same node ID as base
    other_tip = other.nodes.add_node(L, 0, 0)
    other_member = other.members.add_member(other_base, other_tip)

    with pytest.raises(KeyError):
        results.node(other_base)
    with pytest.raises(KeyError):
        results.member(other_member)
    later = model.nodes.add_node(0, 50, 0)
    with pytest.raises(KeyError):
        results.node(later)


def test_second_order_results():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, A=10.0, J=50.0, mesh=8)
    tip.add_load(-P, 'force', 'Y')
    tip.add_load(-50.0, 'force', 'X')   # compression

    first = model.solve()
    second = model.solve(second_order=True)
    assert second.second_order is True
    assert second.iterations == model.solver.iterations > 0
    assert first.second_order is False and first.iterations == 0
    # P-Delta amplifies the tip deflection.
    assert abs(second.node(tip).Uy) > abs(first.node(tip).Uy)
    for sub in second.member(member).submembers:
        assert sub.second_order_axial == pytest.approx(-50.0)
    for sub in first.member(member).submembers:
        assert sub.second_order_axial == 0.0


def test_interrupt_while_collecting_second_order_results(
        monkeypatch: pytest.MonkeyPatch):
    # Ctrl-C after the iterations converged, while the results are being
    # collected, still leaves the first-order solution, not a mixture.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, A=10.0, J=50.0, mesh=8)
    tip.add_load(-P, 'force', 'Y')
    tip.add_load(-50.0, 'force', 'X')   # compression
    first = model.solve()

    collect = Solver._results

    def interrupt(self: Solver, nodes: Nodes, members: Members,
                  second_order: bool) -> Results:
        if second_order:
            raise KeyboardInterrupt
        return collect(self, nodes, members, second_order)
    monkeypatch.setattr(Solver, '_results', interrupt)

    with pytest.raises(KeyboardInterrupt):
        model.solve(second_order=True)
    results = model.results
    assert results is not None and results is not first
    assert results.second_order is False and results.iterations == 0
    assert results.node(tip).Uy == pytest.approx(first.node(tip).Uy,
                                                 rel=1e-12)
    assert tip.Uy == pytest.approx(first.node(tip).Uy, rel=1e-12)
    assert model.solver.iterations == 0 and model.solver.Kt is None
    for sub in results.member(member).submembers:
        assert sub.second_order_axial == 0.0
    for submember in member.submembers.values():
        assert submember.second_order_axial == 0.0


def test_moments_and_shears_along_a_member():
    # A simply supported beam under uniform loads in both planes. Midspan
    # falls inside the middle of three submembers, so the peak moments lie
    # between mesh nodes.
    wy, wz = 0.1, 0.05   # kips per inch, in -Y and -Z
    model = Model()
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 0, 0]
    b.restraint = [0, 1, 1, 0, 0, 0]
    member = model.members.add_member(a, b, E=E, Ixx=I, Iyy=I, mesh=3)
    member.add_distributed_load(-wy, -wy, 'Y', 0, 100)
    member.add_distributed_load(-wz, -wz, 'Z', 0, 100)

    results = model.solve()
    beam = results.member(member)
    for location in [0, 10, 30, 50, 75, 90, 100]:
        x = L*location/100
        assert beam.moment(location) == pytest.approx(
            -wy*x*(L - x)/2, abs=1e-9)
        assert beam.moment(location, 'minor') == pytest.approx(
            wz*x*(L - x)/2, abs=1e-9)
        assert beam.shear(location) == pytest.approx(wy*(L/2 - x), abs=1e-9)
        assert beam.shear(location, 'minor') == pytest.approx(
            wz*(L/2 - x), abs=1e-9)

    middle = beam.submembers[1]   # from L/3 to 2L/3
    x = L/2 - L/3
    assert middle.moment(x) == pytest.approx(-wy*L**2/8)
    assert middle.moment(x, 'minor') == pytest.approx(wz*L**2/8)
    assert middle.shear(x) == pytest.approx(0.0, abs=1e-9)
    assert middle.w_major == pytest.approx((-wy, -wy))
    assert middle.w_minor == pytest.approx((-wz, -wz))
    extrema = middle.force_extrema()
    assert extrema['major axis moments'] == pytest.approx(
        (-wy*L**2/9, -wy*L**2/8))
    assert extrema['minor axis moments'] == pytest.approx(
        (wz*L**2/8, wz*L**2/9))
    assert extrema['shear'] == pytest.approx((wy*L/6, -wy*L/6))
    assert results.Mzz_max == pytest.approx(wy*L**2/8)
    assert results.Myy_max == pytest.approx(wz*L**2/8)
    assert results.Vy_max == pytest.approx(wy*L/2)
    assert results.Vz_max == pytest.approx(wz*L/2)


def test_unknown_axis_raises():
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, mesh=MESH)
    tip.add_load(-P, 'force', 'Y')

    beam = model.solve().member(member)
    with pytest.raises(ValueError):
        beam.moment(50, 'y')
    with pytest.raises(ValueError):
        beam.shear(50, 'Major')
    with pytest.raises(ValueError):
        beam.submembers[0].moment(1.0, 'z')
    with pytest.raises(ValueError):
        beam.submembers[0].shear(1.0, 'minor axis')


def test_second_order_results_do_not_change_after_the_critical_load():
    # critical_load_factor() solves the model again to first order. The
    # moments along the span of the earlier second-order results, with
    # their P-delta part, must not change.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(L, 0, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, Ixx=I, Iyy=I, A=10.0, J=50.0, mesh=8)
    member.add_distributed_load(-0.01, -0.01, 'Y', 0, 100)
    tip.add_load(-P, 'force', 'Y')
    tip.add_load(-50.0, 'force', 'X')   # compression

    first = model.solve()
    second = model.solve(second_order=True)
    beam = second.member(member)
    sub = beam.submembers[3]
    moment, shear = beam.moment(45), beam.shear(45)
    extrema = sub.force_extrema()
    peak = second.Mzz_max
    assert abs(moment) > abs(first.member(member).moment(45)) + 1.0

    assert model.critical_load_factor() > 1.0
    assert beam.moment(45) == moment
    assert beam.shear(45) == shear
    assert sub.force_extrema() == extrema
    assert second.Mzz_max == peak
    assert sub.second_order_axial == pytest.approx(-50.0)


def test_second_order_moments_inside_the_span_about_both_axes():
    # A pinned beam-column under compression and uniform loads in both
    # planes. The exact midspan moment about each axis is
    # w/k^2 (sec(kL/2) - 1), with k^2 = P/(E I) for that axis. Nine
    # elements put midspan inside a submember, so the moment there comes
    # from the P-delta deflected shape between the mesh nodes.
    wy, wz = 0.05, 0.03
    Iyy = 0.4*I
    Pc = 0.3*math.pi**2*E*Iyy/L**2   # 30% of the minor-axis Euler load
    model = Model()
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 0, 0]
    b.restraint = [0, 1, 1, 0, 0, 0]
    member = model.members.add_member(
        a, b, E=E, Ixx=I, Iyy=Iyy, A=10.0, J=50.0, mesh=9)
    member.add_distributed_load(-wy, -wy, 'Y', 0, 100)
    member.add_distributed_load(-wz, -wz, 'Z', 0, 100)
    b.add_load(-Pc, 'force', 'X')

    beam = model.solve(second_order=True).member(member)
    for axis, w, inertia in [('major', wy, I), ('minor', wz, Iyy)]:
        k = math.sqrt(Pc/(E*inertia))
        exact = w/k**2*(1/math.cos(k*L/2) - 1)
        assert abs(beam.moment(50, axis)) == pytest.approx(exact, rel=1e-4)
