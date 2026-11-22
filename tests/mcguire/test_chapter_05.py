import math
from typing import Any

import numpy as np
import pytest

from OpenSTRAN import Model
from OpenSTRAN.Node import Node


# Worked examples from Chapter 5 of W. McGuire, R. H. Gallagher and
# R. D. Ziemian, "Matrix Structural Analysis", 2nd edition. Each class
# rebuilds one example and checks OpenSTRAN against the values printed in the
# book. Units are those of the book (kN and mm).
#
# Each class sets its own RTOL and ATOL to match how precisely its source
# values are printed. ATOL covers the entries that are printed as zero.


def in_plane_stiffness(model: Model, nodes: list[Node]) -> np.ndarray:
    """Return the assembled X-Y stiffness of the given nodes, in their order.

    Rows and columns are u, v and theta_z for each node, the order the book
    uses for planar frames. Read after ``model.solve()``; the matrix includes
    the restrained degrees of freedom.
    """
    kp = model.solver.Kp
    assert kp is not None, "call model.solve() first"
    index = [6 * (node.node_ID - 1) +
             dof for node in nodes for dof in (0, 1, 5)]
    return kp[np.ix_(index, index)]


def from_upper_triangle(rows: list[list[float]]) -> np.ndarray:
    """Build a symmetric matrix from rows that start at the diagonal."""
    n = len(rows)
    matrix = np.zeros((n, n))
    for i, row in enumerate(rows):
        matrix[i, i:] = row
    return matrix + np.triu(matrix, 1).T


# Example 5.3 (pp. 102-104): global stiffness of a plane rigid frame.
#
#                      c
#                    /   \
#            bc    /       \   cd
#                /           \
#             b                d
#             |                |
#         ab  |                |  ed
#             |                |
#             a                e
#
# a and e are fixed. ab and ed are vertical, 5 m long. bc is 8 m long and
# rises 3 m; cd is 5 m long and drops 3 m. The book labels the horizontal
# distance from a to c as 7.416 m, which is sqrt(55) m rounded; the exact
# value is used here because the book's matrices are computed for
# L_bc = 8 m exactly.
#
# E = 200,000 MPa (200 kN/mm^2). ab, cd and ed have A = 4e3 mm^2 and
# I = 50e6 mm^4; bc has A = 6e3 mm^2 and I = 200e6 mm^4. The example does not
# load the frame; its result is the assembled stiffness matrix on p. 104.
class TestExample5_3_PlaneFrameStiffness:
    E = 200.0  # kN/mm^2

    # The book prints four or five significant figures and truncates rather
    # than rounds; the largest deviation from an exact assembly is 9.6e-5.
    # 3e-4 leaves about 3x headroom while a wrong third figure still fails.
    RTOL = 3e-4
    ATOL = 1e-6

    # The matrix printed on p. 104 divided by E, upper triangle, in the order
    # u, v, theta_z at a, b, c, d and e.
    BOOK_K_OVER_E = from_upper_triangle([
        # a
        [0.0048, 0, -12.00, -0.0048, 0, -12.00, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0.800, 0, 0, -0.800, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0.4e5, 12.00, 0, 0.2e5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # b
        [0.6500, 0.2591, 4.969, -0.6452, -0.2591, -7.0313, 0, 0, 0, 0, 0, 0],
        [0.9095, 17.381, -0.2591, -0.1095, 17.381, 0, 0, 0, 0, 0, 0],
        [1.4e5, 7.0313, -17.381, 0.5e5, 0, 0, 0, 0, 0, 0],
        # c
        [1.1589, -0.1226, 14.231, -0.5137, 0.3817, 7.200, 0, 0, 0],
        [0.4006, -7.781, 0.3817, -0.2911, 9.600, 0, 0, 0],
        [1.4e5, -7.200, -9.600, 0.2e5, 0, 0, 0],
        # d
        [0.5185, -0.3817, 4.80, -0.0048, 0, 12.00],
        [1.0911, -9.60, 0, -0.800, 0],
        [0.8e5, -12.00, 0, 0.2e5],
        # e
        [0.00480, 0, -12.00],
        [0.800, 0],
        [0.4e5],
    ])

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        cx = 1000 * math.sqrt(55)

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.b = cls.model.nodes.add_node(0, 5000, 0)
        cls.c = cls.model.nodes.add_node(cx, 8000, 0)
        cls.d = cls.model.nodes.add_node(cx + 4000, 5000, 0)
        cls.e = cls.model.nodes.add_node(cx + 4000, 0, 0)
        cls.a.restraint = [1, 1, 1, 1, 1, 1]
        cls.e.restraint = [1, 1, 1, 1, 1, 1]

        # One element per member, so the joints are the only nodes. Iyy is
        # set well away from Ixx so that a member bending about the wrong
        # axis changes the in-plane matrix. G and J do not enter it.
        light: dict[str, Any] = dict(
            E=cls.E, A=4e3, Ixx=50e6, Iyy=5e6, G=80.0, J=1e6, mesh=1)
        heavy: dict[str, Any] = dict(
            E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(cls.a, cls.b, **light)
        cls.model.members.add_member(cls.b, cls.c, **heavy)
        cls.model.members.add_member(cls.c, cls.d, **light)
        cls.model.members.add_member(cls.e, cls.d, **light)

        cls.model.solve()

    def test_global_stiffness_matrix(self):
        nodes = [self.a, self.b, self.c, self.d, self.e]
        k = in_plane_stiffness(self.model, nodes) / self.E
        np.testing.assert_allclose(
            k, self.BOOK_K_OVER_E, rtol=self.RTOL, atol=self.ATOL)

    def test_global_stiffness_matrix_is_symmetric(self):
        k = self.model.solver.Kp
        assert k is not None, "call model.solve() first"
        atol = 1e-9 * float(np.abs(k).max())
        np.testing.assert_allclose(k, k.T, rtol=0, atol=atol)


# Example 5.4 (pp. 104-106): displacement and reactions of a pin-jointed
# space truss.
#
#   Four bars run from the free joint a, at the origin, down to pinned
#   supports b, c, d and e, which lie in the plane z = -8 m:
#
#       e (-2, 2, -8) m  ------  d (6, 2, -8) m
#          |                         |
#       b (-2, -4, -8) m ------  c (6, -4, -8) m
#
# A = 20e3 mm^2 (ab), 30e3 mm^2 (ac), 40e3 mm^2 (ad) and 30e3 mm^2 (ae);
# E = 200,000 MPa. a carries 200 kN along x, 600 kN along y and -800 kN
# along z.
#
# Each bar is a frame member with bending released at both ends, so it
# carries axial force only. The supports are fully fixed, but the released
# bar ends pass them no moment. a's rotations are restrained, since a pin
# joint has no meaningful rotation; the bars' I, G and J then do not enter
# the result.
class TestExample5_4_SpaceTruss:
    E = 200.0  # kN/mm^2
    LOAD_A = (200.0, 600.0, -800.0)  # kN

    # The book works with four-figure direction cosines. u_a is a small
    # component and is printed as 0.1783 mm against an exact 0.17787 mm
    # (2.4e-3); every other value is within 7.5e-4. RTOL = 5e-3 leaves 2x
    # headroom on u_a, and the equilibrium test checks the reactions tightly.
    RTOL = 5e-3
    ATOL = 1e-6

    # Support coordinates (mm) and bar areas (mm^2).
    SUPPORTS = {
        'b': ((-2000, -4000, -8000), 20e3),
        'c': ((6000, -4000, -8000), 30e3),
        'd': ((6000, 2000, -8000), 40e3),
        'e': ((-2000, 2000, -8000), 30e3),
    }

    supports: dict[str, Node]  # filled in by setup_model

    BOOK_DISPLACEMENT_A = [0.1783, 2.722, -0.4863]  # mm
    BOOK_REACTIONS = {  # kN
        'b': [-76.4, -152.8, -305.6],
        'c': [170.8, -113.8, -227.7],
        'd': [-470.7, -156.9, 627.8],
        'e': [176.3, -176.3, 705.5],
    }

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model()

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.a.restraint = [0, 0, 0, 1, 1, 1]

        pinned = [0, 0, 0, 0, 1, 1]
        cls.supports = {}
        for name, (xyz, area) in cls.SUPPORTS.items():
            node = cls.model.nodes.add_node(*xyz)
            node.restraint = [1, 1, 1, 1, 1, 1]
            cls.supports[name] = node
            cls.model.members.add_member(
                cls.a, node, i_release=pinned, j_release=pinned, E=cls.E,
                A=area, Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)

        px, py, pz = cls.LOAD_A
        cls.a.add_load(px, 'force', 'X')
        cls.a.add_load(py, 'force', 'Y')
        cls.a.add_load(pz, 'force', 'Z')

        cls.results = cls.model.solve()

    def test_displacement_at_a(self):
        a = self.results.node(self.a)
        np.testing.assert_allclose(
            [a.Ux, a.Uy, a.Uz], self.BOOK_DISPLACEMENT_A,
            rtol=self.RTOL, atol=self.ATOL)

    @pytest.mark.parametrize("name", ['b', 'c', 'd', 'e'])
    def test_reactions(self, name: str):
        node = self.results.node(self.supports[name])
        np.testing.assert_allclose(
            [node.Rx, node.Ry, node.Rz], self.BOOK_REACTIONS[name],
            rtol=self.RTOL, atol=self.ATOL)

    @pytest.mark.parametrize("name", ['b', 'c', 'd', 'e'])
    def test_supports_carry_no_moment(self, name: str):
        node = self.results.node(self.supports[name])
        np.testing.assert_allclose(
            [node.Rmx, node.Rmy, node.Rmz], 0, atol=1e-6)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Every
        # bar force passes through a, so the reactions also have no net
        # moment about a.
        forces = np.zeros(3)
        moments = np.zeros(3)
        for node in self.supports.values():
            reaction = self.results.node(node)
            r = np.array([reaction.Rx, reaction.Ry, reaction.Rz])
            xyz = np.array([node.coordinates.x, node.coordinates.y,
                            node.coordinates.z])
            forces += r
            moments += np.cross(xyz, r)

        np.testing.assert_allclose(
            forces + self.LOAD_A, 0, atol=1e-9 * 1000)
        np.testing.assert_allclose(moments, 0, atol=1e-9 * 1000 * 10000)


# Example 5.7 (pp. 115-116): displacements and reactions of a two-member
# rigid frame under a joint load and a uniform load.
#
#                   50 kN
#                     \     4 kN/m
#                      v  v v v v v v v
#                       b ------------- c
#                     /        bc        (fixed)
#              ab   /
#                 /
#               a (fixed)
#
# ab is member bc of Example 5.3: 8 m long, rising 3 m, so b is sqrt(55) m
# (printed 7.416 m) to the right of a. bc is horizontal and 8 m long. Both
# members have A = 6e3 mm^2 and I = 200e6 mm^4, E = 200,000 MPa. The 50 kN
# load at b acts at right angles to ab, down and to the right; the book uses
# its components 18.75 kN and -46.35 kN. bc carries 4 kN/m downward.
class TestExample5_7_FrameJointAndUniformLoad:
    E = 200.0  # kN/mm^2
    W = 0.004  # kN/mm, the uniform load on bc

    # The book solves a hand-rounded 3x3 system (stiffnesses to three or four
    # figures, e.g. 0.109 for 0.1095), so its answers differ from an exact
    # solve by up to 5.0e-3 (R_ya, which is a small difference of two
    # terms). RTOL = 1e-2 leaves 2x headroom. That only catches gross errors,
    # so the equilibrium test below checks the reactions tightly instead.
    RTOL = 1e-2
    ATOL = 1e-6

    # u_b is printed as 0.09982 mm on p. 115, which is a misprint: the
    # reaction calculation on p. 116 uses 0.9982, and solving the book's own
    # printed 3x3 system gives 0.9982.
    BOOK_DISPLACEMENT_B = [0.9982, -4.996, -0.000534]  # mm, mm, rad
    BOOK_REACTIONS_A = [131.0, 55.4, 13.43e3]  # kN, kN, kN*mm
    BOOK_REACTIONS_C = [-149.7, 22.7, -45.41e3]  # kN, kN, kN*mm

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        # The exact sqrt(55) is used for consistency with Example 5.3; the
        # printed 7.416 m changes the results by about 1e-5.
        bx = 1000 * math.sqrt(55)

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.b = cls.model.nodes.add_node(bx, 3000, 0)
        cls.c = cls.model.nodes.add_node(bx + 8000, 3000, 0)
        cls.a.restraint = [1, 1, 1, 1, 1, 1]
        cls.c.restraint = [1, 1, 1, 1, 1, 1]

        # As in Example 5.3, Iyy differs from Ixx so that bending about the
        # wrong axis would show up.
        cls.model.members.add_member(
            cls.a, cls.b, E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=80.0, J=1e6,
            mesh=1)
        cls.bc = cls.model.members.add_member(
            cls.b, cls.c, E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=80.0, J=1e6,
            mesh=1)

        # The 50 kN load is perpendicular to ab, whose direction cosines are
        # (sqrt(55)/8, 3/8).
        cls.Px = 50 * 3 / 8
        cls.Py = -50 * math.sqrt(55) / 8
        cls.b.add_load(cls.Px, 'force', 'X')
        cls.b.add_load(cls.Py, 'force', 'Y')
        cls.bc.add_distributed_load(-cls.W, -cls.W, 'Y', 0, 100)

        cls.results = cls.model.solve()

    def test_displacement_at_b(self):
        b = self.results.node(self.b)
        np.testing.assert_allclose(
            [b.Ux, b.Uy, b.phi_z], self.BOOK_DISPLACEMENT_B,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_at_a(self):
        a = self.results.node(self.a)
        np.testing.assert_allclose(
            [a.Rx, a.Ry, a.Rmz], self.BOOK_REACTIONS_A,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_at_c(self):
        c = self.results.node(self.c)
        np.testing.assert_allclose(
            [c.Rx, c.Ry, c.Rmz], self.BOOK_REACTIONS_C,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Moments
        # are taken about a; the uniform load's resultant acts at mid-span.
        b, c = self.b, self.c
        xb, yb = b.coordinates.x, b.coordinates.y
        xc, yc = c.coordinates.x, c.coordinates.y
        w_total = self.W * 8000
        ra, rc = (self.results.node(x) for x in (self.a, self.c))

        sum_fx = ra.Rx + rc.Rx + self.Px
        sum_fy = ra.Ry + rc.Ry + self.Py - w_total
        sum_mz = (ra.Rmz + rc.Rmz + xc * rc.Ry - yc * rc.Rx
                  + xb * self.Py - yb * self.Px - (xb + 4000) * w_total)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 50)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 50)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 50 * 20000)


# Example 5.8 (pp. 116-119): displacements and reactions of a horizontal
# grid under vertical loads.
#
#                 5 kN
#      3 kN/m      |
#   a v v v v v v  v
#   +------------- b          plan view, looking down on the grid
#        ab        |
#                  | bc
#                  |
#                  + c
#
# a and c are fixed. ab is 5 m long and carries 3 kN/m; bc is 8 m long, at
# right angles to ab. ab has A = 4e3 mm^2, I = 50e6 mm^4, J = 100e3 mm^4;
# bc has A = 6e3 mm^2, I = 200e6 mm^4, J = 300e3 mm^4 (the members of
# Example 4.8). E = 200,000 MPa and nu = 0.3, so G = E / 2.6.
#
# The book draws the grid with z vertical. OpenSTRAN treats Y as vertical
# (a member's strong axis bends in the vertical plane), so the grid is built
# in the X-Z plane the way a user would model a floor: the book's axes
# (x, y, z) become (X, -Z, Y). The book's w, theta_x and theta_y are then
# Uy, phi_x and -phi_z, and its M_x and M_y are Rmx and -Rmz.
class TestExample5_8_GridUnderVerticalLoad:
    E = 200.0  # kN/mm^2
    G = E / 2.6  # kN/mm^2, from nu = 0.3
    P = 5.0  # kN, downward at b
    W = 0.003  # kN/mm, downward on ab

    # The book solves a hand-rounded 3x3 system, so its answers differ from
    # an exact solve by up to 1.0e-3 (the torque at a). RTOL = 2e-3 leaves
    # 2x headroom.
    RTOL = 2e-3
    ATOL = 1e-6

    # In the book's axes: w_b, theta_xb, theta_yb.
    BOOK_DISPLACEMENT_B = [-22.37, 4.195e-3, 5.931e-3]  # mm, rad, rad
    # In the book's axes: R_z, R_mx, R_my.
    BOOK_REACTIONS_A = [14.74, -6.45, -36.21e3]  # kN, kN*mm, kN*mm
    BOOK_REACTIONS_C = [5.25, -41.94e3, -17.11]  # kN, kN*mm, kN*mm

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model()

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.b = cls.model.nodes.add_node(5000, 0, 0)
        cls.c = cls.model.nodes.add_node(5000, 0, -8000)
        cls.a.restraint = [1, 1, 1, 1, 1, 1]
        cls.c.restraint = [1, 1, 1, 1, 1, 1]
        # b is left free in all six directions rather than held in the plane
        # of the grid, so that any in-plane response to the vertical loads
        # shows up (see test_grid_responds_only_out_of_plane).
        cls.b.restraint = [0, 0, 0, 0, 0, 0]

        # Iyy differs from Ixx so that bending about the wrong axis would
        # show up.
        cls.ab = cls.model.members.add_member(
            cls.a, cls.b, E=cls.E, A=4e3, Ixx=50e6, Iyy=5e6, G=cls.G,
            J=100e3, mesh=1)
        cls.model.members.add_member(
            cls.b, cls.c, E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=cls.G,
            J=300e3, mesh=1)

        cls.b.add_load(-cls.P, 'force', 'Y')
        cls.ab.add_distributed_load(-cls.W, -cls.W, 'Y', 0, 100)

        cls.results = cls.model.solve()

    def test_displacement_at_b(self):
        b = self.results.node(self.b)
        np.testing.assert_allclose(
            [b.Uy, b.phi_x, -b.phi_z], self.BOOK_DISPLACEMENT_B,
            rtol=self.RTOL, atol=self.ATOL)

    def test_grid_responds_only_out_of_plane(self):
        # Vertical loads on a grid cause no movement in its plane and no
        # in-plane reactions. A coupling error between the members' axial,
        # torsional and bending terms would show up here.
        b = self.results.node(self.b)
        np.testing.assert_allclose([b.Ux, b.Uz, b.phi_y], 0, atol=1e-9)
        for node in (self.a, self.c):
            r = self.results.node(node)
            np.testing.assert_allclose([r.Rx, r.Rz, r.Rmy], 0, atol=1e-9)

    def test_reactions_at_a(self):
        a = self.results.node(self.a)
        np.testing.assert_allclose(
            [a.Ry, a.Rmx, -a.Rmz], self.BOOK_REACTIONS_A,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_at_c(self):
        c = self.results.node(self.c)
        np.testing.assert_allclose(
            [c.Ry, c.Rmx, -c.Rmz], self.BOOK_REACTIONS_C,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Moments
        # are taken about a; the uniform load's resultant acts at the middle
        # of ab. A vertical force Fy at (x, 0, z) has a moment of -z * Fy
        # about X and x * Fy about Z.
        b, c = self.b, self.c
        xb = b.coordinates.x
        xc, zc = c.coordinates.x, c.coordinates.z
        w_total = self.W * 5000
        ra, rc = (self.results.node(x) for x in (self.a, self.c))

        sum_fy = ra.Ry + rc.Ry - self.P - w_total
        sum_mx = ra.Rmx + rc.Rmx - zc * rc.Ry
        sum_mz = (ra.Rmz + rc.Rmz + xc * rc.Ry - xb * self.P
                  - 2500 * w_total)

        assert sum_fy == pytest.approx(0, abs=1e-9 * 20)
        assert sum_mx == pytest.approx(0, abs=1e-9 * 20 * 10000)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 20 * 10000)
