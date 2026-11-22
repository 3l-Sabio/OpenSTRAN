import math

import numpy as np
import pytest

from OpenSTRAN import Model
from OpenSTRAN.Solver import Solver
from OpenSTRAN.Submember import SubMember


# Second-order (P-Delta) analysis and elastic critical loads checked against
# exact beam-column theory (Timoshenko and Gere, "Theory of Elastic
# Stability", Ch. 1). Units are kips and inches.
#
# A cantilever of length L carries an axial load P and a lateral load H at
# its tip. With k = sqrt(|P| / EI), the exact tip deflection and base moment
# are
#
#     compression:  H (tan kL - kL) / (|P| k)     and  H tan(kL) / k
#     tension:      H (kL - tanh kL) / (|P| k)    and  H tanh(kL) / k
#
# and the critical load is pi^2 EI / 4L^2. The geometric stiffness matrix
# uses cubic shape functions, so the error falls with the fourth power of
# the element length. With eight elements it is at most 6.6e-6, for the tip
# deflection at 0.8 P_cr in compression (the amplification magnifies it;
# at 0.4 P_cr it is 5.5e-7), and 2.1e-6 for the critical load. The
# tolerances leave about 2x headroom.

E = 29000.0
I = 100.0
A = 10.0
L = 120.0
MESH = 8
P_CR = math.pi**2 * E * I / (4 * L**2)  # 496.9 kips

RTOL = 1.5e-5
RTOL_CRITICAL = 5e-6


def cantilever(P: float, H: float, mesh: int = MESH):
    """Build a vertical cantilever with tip loads P (up) and H (along X)."""
    model = Model(plane='xy')
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(0, L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(
        base, tip, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=mesh)
    tip.add_load(H, 'force', 'X')
    if P:
        tip.add_load(P, 'force', 'Y')
    return model, base, tip


@pytest.mark.parametrize("ratio", [0.2, 0.4, 0.8])
@pytest.mark.parametrize("compression", [True, False])
def test_cantilever_tip_deflection_and_base_moment(ratio: float, compression: bool):
    P = ratio * P_CR
    H = 1.0
    k = math.sqrt(P / (E * I))
    if compression:
        deflection = H * (math.tan(k * L) - k * L) / (P * k)
        moment = H * math.tan(k * L) / k
    else:
        deflection = H * (k * L - math.tanh(k * L)) / (P * k)
        moment = H * math.tanh(k * L) / k

    model, base, tip = cantilever(-P if compression else P, H)
    results = model.solve(second_order=True)

    assert results.node(tip).Ux == pytest.approx(deflection, rel=RTOL)
    # The base reaction moment balances H L plus the P-Delta moment.
    assert results.node(base).Rmz == pytest.approx(moment, rel=RTOL)


def pinned_beam_column(P: float, w: float, mesh: int):
    """Build a pinned beam of length 2L along X with an axial compression P
    and a uniform load w (down) over its whole length."""
    model = Model(plane='xy')
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(2 * L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 0]
    b.restraint = [0, 1, 1, 1, 1, 0]
    member = model.members.add_member(
        a, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=mesh)
    member.add_distributed_load(-w, -w, 'Y', 0, 100)
    b.add_load(-P, 'force', 'X')
    return model, member


@pytest.mark.parametrize("ratio", [0.3, 0.6])
def test_beam_column_maximum_moment(ratio: float):
    # Exact maximum moment of a pinned beam-column of length l under a
    # uniform load w and axial compression P (Timoshenko and Gere, Sec. 1.10):
    #     w / k^2 (sec(kl/2) - 1),  k = sqrt(P / EI).
    # An odd number of elements puts midspan inside a submember, so the
    # maximum is found by the in-span P-delta moment and its extremum
    # search. With nine elements the error is at most 4.0e-5 (at 0.6 P_e).
    w = 0.05
    l = 2 * L
    P = ratio * math.pi**2 * E * I / l**2
    k = math.sqrt(P / (E * I))
    exact = w / k**2 * (1 / math.cos(k * l / 2) - 1)

    model, member = pinned_beam_column(P, w, mesh=9)
    results = model.solve(second_order=True)

    assert results.Mzz_max == pytest.approx(exact, rel=1e-4)
    assert abs(results.member(member).moment(50)) == pytest.approx(
        exact, rel=1e-4)


def test_in_span_moments_match_the_end_moments():
    # After a second-order analysis the end forces include the geometric
    # stiffness, whose end moments sum to N times the relative transverse
    # displacement. The in-span moment carries that P-delta term, so it is
    # continuous across mesh nodes and equals the recovered end moments.
    model, member = pinned_beam_column(0.6 * math.pi**2 * E * I / (2 * L)**2,
                                       0.05, mesh=3)
    results = model.solve(second_order=True)

    for sub in results.member(member).submembers:
        ends = sub.forces['major axis moments']
        assert sub.moment(0.0) == pytest.approx(ends[0], abs=1e-9)
        assert sub.moment(sub.submember.length) == pytest.approx(
            -ends[1], abs=1e-9)


def test_in_span_moments_match_the_end_moments_about_both_axes():
    # As above, for a 3D cantilever bent about both axes, so the minor-axis
    # P-delta term (with its opposite sign convention) is checked too.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(0, L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        base, tip, E=E, A=A, Ixx=I, Iyy=0.4 * I, G=11200.0, J=1.0, mesh=2)
    tip.add_load(1.0, 'force', 'X')
    tip.add_load(0.5, 'force', 'Z')
    tip.add_load(-30.0, 'force', 'Y')
    results = model.solve(second_order=True)

    for sub in results.member(member).submembers:
        l = sub.submember.length
        major = sub.forces['major axis moments']
        minor = sub.forces['minor axis moments']
        assert sub.moment(l) == pytest.approx(-major[1], abs=1e-9)
        assert sub.moment(l, 'minor') == pytest.approx(-minor[1], abs=1e-9)
        # The P-delta term is not negligible here.
        assert abs(sub._p_delta_moment(l, 'major')) > 1.0
        assert abs(sub._p_delta_moment(l, 'minor')) > 1.0


@pytest.mark.parametrize("mesh", [1, 3])
def test_moment_extrema_with_an_asymmetric_load(mesh: int):
    # Under a triangular load the P-delta moment moves the peak away from the
    # point of zero shear, so the extremum search must include it. The
    # extrema are compared with a dense sampling of the in-span moment,
    # which they match to about 1e-12 (dropping the P-delta terms from the
    # search gives errors of 4e-3 and more).
    model = Model(plane='xy')
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(2 * L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 0]
    b.restraint = [0, 1, 1, 1, 1, 0]
    member = model.members.add_member(
        a, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=mesh)
    member.add_distributed_load(0.0, -0.1, 'Y', 0, 100)
    b.add_load(-0.6 * math.pi**2 * E * I / (2 * L)**2, 'force', 'X')
    results = model.solve(second_order=True)

    for sub in results.member(member).submembers:
        x = np.linspace(0.0, sub.submember.length, 20001)
        sampled = np.array([sub.moment(xi) for xi in x])
        largest, smallest = sub.force_extrema()['major axis moments']
        scale = float(np.abs(sampled).max())
        assert largest == pytest.approx(sampled.max(), abs=1e-7 * scale)
        assert smallest == pytest.approx(sampled.min(), abs=1e-7 * scale)


def test_without_axial_load_second_order_equals_first_order():
    first_model, _, tip_first = cantilever(0.0, 1.0)
    first = first_model.solve()
    second_model, _, tip_second = cantilever(0.0, 1.0)
    second = second_model.solve(second_order=True)

    assert second.node(tip_second).Ux == pytest.approx(
        first.node(tip_first).Ux, rel=1e-12)
    assert second.iterations == 1


def test_cantilever_critical_load():
    model, _, _ = cantilever(-1.0, 0.0)
    assert model.critical_load_factor() == pytest.approx(P_CR, rel=RTOL_CRITICAL)


def test_cantilever_critical_load_about_the_weak_axis():
    # A 3D model, free to bend about either axis, buckles about the weak
    # axis (Iyy = Ixx / 10) at pi^2 E Iyy / 4L^2. The plane models above
    # only exercise the strong-axis block of the geometric stiffness.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(0, L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(
        base, tip, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=MESH)
    tip.add_load(-1.0, 'force', 'Y')
    assert model.critical_load_factor() == pytest.approx(
        P_CR / 10, rel=RTOL_CRITICAL)


def test_critical_load_without_compression_raises():
    model, _, _ = cantilever(1.0, 1.0)
    with pytest.raises(ValueError, match="no member in compression"):
        model.critical_load_factor()


@pytest.mark.parametrize("mesh", [1, 8, 50])
def test_critical_load_of_a_hanging_rod_raises(mesh: int):
    # Every member is in tension, so all the eigenvalues are zero or
    # negative. Rounding can make the largest slightly positive (with eight
    # elements it gave a factor of 9e16), so the absence of compression is
    # checked before the eigenproblem.
    model = Model()
    support = model.nodes.add_node(0, 0, 0)
    end = model.nodes.add_node(0, -L, 0)
    support.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(
        support, end, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0,
        mesh=mesh)
    end.add_load(-5.0, 'force', 'Y')
    end.add_load(0.3, 'force', 'X')
    end.add_load(0.2, 'force', 'Z')

    with pytest.raises(ValueError, match="no member in compression"):
        model.critical_load_factor()


@pytest.mark.parametrize("mesh", [2, 20])
def test_critical_load_of_a_beam_in_tension_raises(mesh: int):
    # A simply supported beam pulled along its axis and loaded across it
    # (factors of 1e18 and 3e17 before the check).
    model = Model(plane='xy')
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(2 * L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 0]
    b.restraint = [0, 1, 1, 1, 1, 0]
    beam = model.members.add_member(
        a, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=mesh)
    beam.add_distributed_load(-0.05, -0.05, 'Y', 0, 100)
    b.add_load(10.0, 'force', 'X')

    with pytest.raises(ValueError, match="no member in compression"):
        model.critical_load_factor()


def test_load_above_critical_raises():
    model, _, _ = cantilever(-1.2 * P_CR, 1.0)
    with pytest.raises(RuntimeError, match="critical load"):
        model.solve(second_order=True)


def test_iteration_limit_raises():
    # The axial force needs one iteration to reach the tangent stiffness and
    # a second to confirm convergence.
    model, _, _ = cantilever(-0.4 * P_CR, 1.0)
    with pytest.raises(RuntimeError, match="did not converge in 1 iterations"):
        model.solve(second_order=True, max_iterations=1)


@pytest.mark.parametrize("mesh, rtol", [(200, RTOL), (500, 1e-3)])
def test_fine_mesh_converges_near_the_critical_load(mesh: int, rtol: float):
    # With 200 elements at 0.9 P_cr the tangent stiffness has a condition
    # number of about 6e10. The axial force is fixed by statics, so the
    # second iteration finds no change in it and stops. Testing the
    # displacement increment as well would never pass: rounding keeps it
    # near 1e-7 of the displacements, and forming the unbalanced load as
    # F - Kt U would leave 3e-8 of the loads with 500 elements. With 500
    # elements accuracy is limited by conditioning: the tip deflection is off
    # by 8e-5 (a first-order solve loses 8e-6, which the axial load
    # amplifies), so the tolerance is looser.
    P = 0.9 * P_CR
    k = math.sqrt(P / (E * I))
    model, _, tip = cantilever(-P, 1.0, mesh=mesh)
    results = model.solve(second_order=True)

    assert results.iterations == 2
    assert results.node(tip).Ux == pytest.approx(
        (math.tan(k * L) - k * L) / (P * k), rel=rtol)


@pytest.mark.parametrize("ratio, max_iterations, message", [
    (1.2, 50, "limit load"),      # fails before the displacements change
    (0.4, 1, "did not converge"),  # fails after one iteration
])
def test_failed_analysis_leaves_the_previous_results(
        ratio: float, max_iterations: int, message: str):
    # A failed analysis raises and leaves the model with the results of the
    # analysis before it, rather than a mixture of iterations.
    model, _, _ = cantilever(-ratio * P_CR, 1.0)
    first = model.solve()

    with pytest.raises(RuntimeError, match=message):
        model.solve(second_order=True, max_iterations=max_iterations)

    assert model.results is first


@pytest.mark.parametrize("P", [1e-10, 1.0, 1e6])
def test_critical_load_does_not_depend_on_the_reference_load(P: float):
    # The geometric stiffness is formed directly, not as a difference of two
    # nearly equal matrices, so a tiny reference load keeps its precision.
    model, _, _ = cantilever(-P, 0.0)
    assert model.critical_load_factor() * P == pytest.approx(
        P_CR, rel=RTOL_CRITICAL)


def test_critical_load_with_a_release_does_not_depend_on_the_reference_load():
    # A released submember's geometric stiffness is condensed with its
    # elastic stiffness, which keeps it linear in the axial force. The
    # column is released at its base and slides vertically at its top.
    # (With one element it buckles 25% above the same column on a pinned
    # support, a known issue of releases at one end only.)
    critical_loads = []
    for P in [1e-6, 1.0, 1e3]:
        model = Model(plane='xy')
        base = model.nodes.add_node(0, 0, 0)
        top = model.nodes.add_node(0, L, 0)
        base.restraint = [1, 1, 1, 1, 1, 1]
        top.restraint = [1, 0, 1, 1, 1, 0]
        model.members.add_member(
            base, top, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1,
            i_release=[0, 0, 0, 0, 0, 1])
        top.add_load(-P, 'force', 'Y')
        critical_loads.append(model.critical_load_factor() * P)

    assert critical_loads == pytest.approx([critical_loads[1]] * 3, rel=1e-9)


def test_critical_load_without_a_free_buckling_mode_raises():
    # The column's top is held against sway and rotation, so with one
    # element no bending mode is free. Without the axial terms left out of
    # the geometric stiffness the factor would be EA/P = 290,000.
    model = Model(plane='xy')
    base = model.nodes.add_node(0, 0, 0)
    top = model.nodes.add_node(0, L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    top.restraint = [1, 0, 1, 1, 1, 1]
    model.members.add_member(
        base, top, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1)
    top.add_load(-1.0, 'force', 'Y')

    with pytest.raises(ValueError, match="no elastic critical load"):
        model.critical_load_factor()


def test_critical_load_of_a_member_loaded_across_its_axis_raises():
    # A load at right angles to an inclined cantilever leaves axial forces
    # of about 1e-13 kips, from rounding. They are treated as zero rather
    # than giving a factor near 1e13.
    model = Model(plane='xy')
    base = model.nodes.add_node(0, 0, 0)
    tip = model.nodes.add_node(0.6 * L, 0.8 * L, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(
        base, tip, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=4)
    tip.add_load(0.8, 'force', 'X')
    tip.add_load(-0.6, 'force', 'Y')

    with pytest.raises(ValueError, match="no elastic critical load"):
        model.critical_load_factor()


@pytest.mark.filterwarnings("ignore::scipy.linalg.LinAlgWarning")
@pytest.mark.parametrize("second_order", [False, True])
def test_rotation_without_stiffness_raises(second_order: bool):
    # Both bars are released at both ends and the joint's rotation is left
    # free, so nothing resists it. The first-order analysis inside each call
    # still solves, with a warning; the second-order analysis and the
    # critical load raise.
    model = Model(plane='xy')
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(L, 0, 0)
    c = model.nodes.add_node(L, L, 0)
    a.restraint = [1, 1, 1, 1, 1, 1]
    c.restraint = [1, 1, 1, 1, 1, 1]
    b.restraint = [0, 0, 1, 1, 1, 0]
    for support in [a, c]:
        model.members.add_member(
            support, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0,
            mesh=1, i_release=[0, 0, 0, 0, 1, 1], j_release=[0, 0, 0, 0, 1, 1])
    b.add_load(-1.0, 'force', 'Y')

    with pytest.raises(ValueError, match="Node 2 .* no stiffness against phi_z"):
        if second_order:
            model.solve(second_order=True)
        else:
            model.critical_load_factor()


@pytest.mark.parametrize("second_order", [False, True])
def test_rotation_without_stiffness_about_an_inclined_axis_raises(
        second_order: bool):
    # Two inclined bars of a space truss meet at a joint with free
    # rotations. Each resists twisting about its own axis, so every diagonal
    # entry of the joint's stiffness is positive, but nothing resists
    # rotation about the axis normal to both bars, (1, -1, 1)/sqrt(3).
    model = Model()
    joint = model.nodes.add_node(0, 0, 0)
    a = model.nodes.add_node(L, L, 0)
    b = model.nodes.add_node(0, L, L)
    a.restraint = [1, 1, 1, 1, 1, 1]
    b.restraint = [1, 1, 1, 1, 1, 1]
    joint.restraint = [0, 0, 1, 0, 0, 0]
    for support in [a, b]:
        model.members.add_member(
            support, joint, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0,
            mesh=1, i_release=[0, 0, 0, 0, 1, 1], j_release=[0, 0, 0, 0, 1, 1])
    joint.add_load(-1.0, 'force', 'Y')

    with pytest.raises(ValueError, match=(
            r"Node 1 .* no stiffness against 0.577 phi_x - 0.577 phi_y "
            r"\+ 0.577 phi_z")):
        if second_order:
            model.solve(second_order=True)
        else:
            model.critical_load_factor()


@pytest.mark.filterwarnings("ignore::scipy.linalg.LinAlgWarning")
@pytest.mark.parametrize("second_order", [False, True])
def test_instability_raises(second_order: bool):
    # A pin-jointed frame of three bars, inclined so that the condensed
    # releases leave a rounding residue, sways freely. Every joint has
    # stiffness of its own, so only the factorization of the whole
    # structure finds the instability.
    model = Model(plane='xy')
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(30, L, 0)
    c = model.nodes.add_node(30 + L, L, 0)
    d = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 1]
    d.restraint = [1, 1, 1, 1, 1, 1]
    b.restraint = [0, 0, 1, 1, 1, 1]
    c.restraint = [0, 0, 1, 1, 1, 1]
    for i, j in [(a, b), (b, c), (d, c)]:
        model.members.add_member(
            i, j, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1,
            i_release=[0, 0, 0, 0, 1, 1], j_release=[0, 0, 0, 0, 1, 1])
    b.add_load(-1.0, 'force', 'Y')
    c.add_load(-1.0, 'force', 'Y')

    with pytest.raises(ValueError, match="unstable"):
        if second_order:
            model.solve(second_order=True)
        else:
            model.critical_load_factor()


@pytest.mark.parametrize("P", [-50.0, 50.0])
def test_axial_force_changes_torsional_stiffness(P: float):
    # The torsional terms of the geometric stiffness (McGuire et al.,
    # Eq. 9.17) add P Ip / A to GJ, so a bar under torque T twists by
    # T L / (GJ + P Ip / A), with Ip = Ixx + Iyy and P positive in tension.
    G, J, Ixx, Iyy, T = 11200.0, 2.0, 100.0, 40.0, 10.0
    model = Model()
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 1]
    model.members.add_member(
        a, b, E=E, A=A, Ixx=Ixx, Iyy=Iyy, G=G, J=J, mesh=4)
    b.add_load(T, 'moment', 'X')
    b.add_load(P, 'force', 'X')
    results = model.solve(second_order=True)

    assert results.node(b).phi_x == pytest.approx(
        T * L / (G * J + P * (Ixx + Iyy) / A), rel=1e-9)


# The 0.02 in submember is stiff enough that the first-order solve warns of
# ill-conditioning; it is accurate enough for the test.
@pytest.mark.filterwarnings("ignore::scipy.linalg.LinAlgWarning")
@pytest.mark.parametrize("gap", [0.05, 0.02])
def test_short_submember_converges_to_the_fixed_point(gap: float):
    # A point load close to a joint makes a short, stiff submember that moves
    # almost as a rigid body. In F - Kt U its stiffness leaves rounding error
    # far above the tolerance; the unbalanced load is therefore formed from
    # the change in axial forces. (A rounding allowance used in its place
    # stopped the 0.05 in case while the deflection was still 1.2e-3 from
    # converged.) The stiffness check compares each node with its own
    # unreleased stiffness, so the short submember no longer makes a column
    # node elsewhere look unrestrained (the 0.02 in case raised). At
    # convergence, the axial force each submember's tangent stiffness was
    # formed with is the axial force it carries: they differ by 5e-11 of the
    # largest, against 5e-7 and 6e-4 when the rounding allowance stopped the
    # two cases early.
    model = Model()
    base = model.nodes.add_node(0, 0, 0)
    top = model.nodes.add_node(0, 288, 0)
    tip = model.nodes.add_node(240, 288, 0)
    base.restraint = [1, 1, 1, 1, 1, 1]
    tip.restraint = [0, 1, 1, 1, 0, 0]
    model.members.add_member(
        base, top, E=E, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
        mesh=4)
    beam = model.members.add_member(
        top, tip, E=E, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0, J=2.81,
        mesh=4)
    top.add_load(-20.0, 'force', 'Y')
    top.add_load(1.0, 'force', 'X')
    top.add_load(0.5, 'force', 'Z')
    beam.add_point_load(-1.0, 'Y', gap / 240 * 100)
    results = model.solve(second_order=True)

    submembers = [sub for member in results.members
                  for sub in member.submembers]
    used = np.array([s.second_order_axial for s in submembers])
    carried = np.array([s.forces['axial'][1] for s in submembers])
    assert carried == pytest.approx(used, rel=0, abs=1e-8 * np.abs(used).max())
    assert model.critical_load_factor() > 1.0


def test_bar_released_at_both_ends_stays_straight():
    # The geometry of McGuire et al., Example 9.1, with a lateral load: two
    # bars released for bending at both ends meet at a joint whose rotation
    # is restrained. A bar's own end rotations, not the joint's, shape its
    # P-delta moment, so it stays straight and carries no moment anywhere.
    # Taking the joint's zero rotation bent it into an S, with moments of
    # about 10% of N times the sway.
    bar = [0, 0, 0, 0, 1, 1]
    model = Model(plane='xy')
    a = model.nodes.add_node(0, L, 0)
    b = model.nodes.add_node(L, L, 0)
    c = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 1]
    c.restraint = [1, 1, 1, 1, 1, 1]
    b.restraint = [0, 0, 1, 1, 1, 1]
    model.members.add_member(
        a, b, E=E, A=0.1, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1,
        i_release=bar, j_release=bar)
    bc = model.members.add_member(
        c, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1,
        i_release=bar, j_release=bar)
    b.add_load(-100.0, 'force', 'Y')
    b.add_load(1.0, 'force', 'X')
    results = model.solve(second_order=True)

    assert 100.0 * results.node(b).Ux > 1.0  # N times the sway, in kip-in
    for x in [10, 21.1, 50, 78.9, 90]:
        assert results.member(bc).moment(x) == pytest.approx(0.0, abs=1e-9)
    assert results.Mzz_max == pytest.approx(0.0, abs=1e-9)


def test_in_span_moments_next_to_a_release_match_a_support():
    # A column pinned at its base, by a pinned support or by a release at a
    # fixed support, carries half its Euler load and a lateral point load.
    # The released submember has no span load, so the two models are the
    # same structure and their moments along the span agree. The base node
    # of the released model does not rotate; the submember does.
    moments = []
    for release in [False, True]:
        model = Model(plane='xy')
        base = model.nodes.add_node(0, 0, 0)
        top = model.nodes.add_node(0, L, 0)
        base.restraint = [1, 1, 1, 1, 1, 1 if release else 0]
        top.restraint = [1, 0, 1, 1, 1, 0]
        column = model.members.add_member(
            base, top, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0,
            mesh=3, i_release=[0, 0, 0, 0, 0, 1 if release else 0])
        column.add_point_load(1.0, 'X', 40)
        top.add_load(-0.5 * 4 * P_CR, 'force', 'Y')
        results = model.solve(second_order=True)
        moments.append(np.array([results.member(column).moment(x)
                                 for x in [5, 10, 20, 30, 50, 80]]))

    assert moments[1] == pytest.approx(
        moments[0], rel=1e-9, abs=1e-9 * np.abs(moments[0]).max())


@pytest.mark.parametrize("i_release, j_release", [
    ([0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]),
    ([0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0]),
    ([0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 1, 1]),
])
def test_tangent_difference_is_the_difference_of_tangents(
        i_release: list[int], j_release: list[int]):
    # The change in tangent stiffness between two axial forces is formed
    # without subtracting the elastic stiffness. For a submember of ordinary
    # length the plain difference is accurate, and the two must agree.
    model = Model()
    a = model.nodes.add_node(0, 0, 0)
    b = model.nodes.add_node(L, 0, 0)
    a.restraint = [1, 1, 1, 1, 1, 1]
    b.restraint = [0, 1, 1, 1, 1, 1]
    member = model.members.add_member(
        a, b, E=E, A=A, Ixx=I, Iyy=I / 10, G=11200.0, J=1.0, mesh=1,
        i_release=i_release, j_release=j_release)
    b.add_load(1.0, 'force', 'X')
    model.solve()
    submember = next(iter(member.submembers.values()))

    expected = (submember.tangent_stiffness(-30.0)
                - submember.tangent_stiffness(20.0))
    assert submember.tangent_difference(-30.0, 20.0) == pytest.approx(
        expected, rel=0, abs=1e-12 * np.abs(submember.Kl_unreleased).max())


@pytest.mark.parametrize("call", ["solve", "critical_load_factor"])
def test_failed_first_order_solve_keeps_its_error(
        monkeypatch: pytest.MonkeyPatch, call: str):
    # When the first-order solve fails there are no results, so the model
    # does not look for maxima, and the original error reaches the caller.
    # (It used to be replaced by an IndexError from the empty results.)
    def fail(self: Solver, K: np.ndarray) -> np.ndarray:
        raise ValueError("first-order failure")
    monkeypatch.setattr(Solver, "_solve_free", fail)
    model, _, _ = cantilever(-0.4 * P_CR, 1.0)

    with pytest.raises(ValueError, match="first-order failure"):
        getattr(model, call)()


def test_any_error_during_the_iteration_leaves_the_previous_results(
        monkeypatch: pytest.MonkeyPatch):
    # Whether the model keeps its results does not depend on the type of
    # the error: a LinAlgError raised during the iteration leaves them too.
    model, _, _ = cantilever(-0.4 * P_CR, 1.0)
    first = model.solve()

    def fail(self: Solver, *args: object) -> None:
        raise np.linalg.LinAlgError("second-order failure")
    monkeypatch.setattr(Solver, "_second_order", fail)

    with pytest.raises(np.linalg.LinAlgError):
        model.solve(second_order=True)
    assert model.results is first


def test_interrupted_analysis_leaves_the_previous_results(
        monkeypatch: pytest.MonkeyPatch):
    # Ctrl-C raises KeyboardInterrupt, which is not an Exception. An
    # analysis interrupted in its second iteration, after the first changed
    # the displacements, still leaves the results of the analysis before it.
    model, _, _ = cantilever(-0.4 * P_CR, 1.0)
    first = model.solve()

    tangent_stiffness = SubMember.tangent_stiffness
    calls: list[float] = []

    def interrupt(self: SubMember, Fx2: float) -> np.ndarray:
        calls.append(Fx2)
        if len(calls) > MESH:
            raise KeyboardInterrupt
        return tangent_stiffness(self, Fx2)
    monkeypatch.setattr(SubMember, "tangent_stiffness", interrupt)

    with pytest.raises(KeyboardInterrupt):
        model.solve(second_order=True)
    assert len(calls) == MESH + 1
    assert model.results is first
