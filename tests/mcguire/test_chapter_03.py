import math

import numpy as np
import pytest

from OpenSTRAN import Model


# Worked examples from Chapter 3 of W. McGuire, R. H. Gallagher and
# R. D. Ziemian, "Matrix Structural Analysis", 2nd edition. Each class
# rebuilds one example and checks OpenSTRAN against the values printed in the
# book. Units are those of the book (kN and mm).
#
# Each class sets its own RTOL and ATOL to match how precisely its source
# values are printed. The book works to three or four figures throughout.
#
# The examples are pin-jointed plane trusses. Each bar is a frame member with
# bending released at both ends, so it carries axial force only. Restraints
# are [Ux, Uy, Uz, phi_x, phi_y, phi_z]. Every joint has its rotations and
# out-of-plane movement restrained: a pin joint has no meaningful rotation,
# so the bars' I, G and J do not enter the results, and the released bar
# ends pass the supports no moment.


# Examples 3.1 to 3.3 share this truss:
#
#                    a
#                  /   \
#        ac      /       \     ab
#              /           \
#            c ------------- b
#                   cb
#
# ac is 8 m long at 30 degrees to cb; ab is at 45 degrees; a is 4 m above cb.
# So c is at the origin, a at (4 sqrt(3), 4) m and b at (4 + 4 sqrt(3), 0) m;
# the book prints cb as 10.928 m. A = 15e3 mm^2 (ac), 20e3 mm^2 (ab) and
# 18e3 mm^2 (cb). A 500 kN load acts at a, 40 degrees above the horizontal;
# the book uses its components 383.0 kN and 321.4 kN.


# Example 3.2 (pp. 36-38): the truss of Example 3.1 on a pin at c and a
# roller at b.
class TestExample3_2_TriangularTruss:
    E = 200.0  # kN/mm^2

    # The book's worst gap from an exact solve is 1.3e-3 (bar ab, 90.0 kN
    # against 89.89 kN). RTOL = 3e-3 leaves 2x headroom.
    RTOL = 3e-3
    ATOL = 1e-6

    # The 500 kN load at a, 40 degrees above the horizontal (kN).
    PX = 500 * math.cos(math.radians(40))
    PY = 500 * math.sin(math.radians(40))

    BOOK_DISPLACEMENTS = [0.871, 1.244, -0.193]  # u_a, v_a, u_b (mm)
    BOOK_REACTIONS = [-63.6, -383.4, -258.1]  # R_yb, R_xc, R_yc (kN)
    BOOK_BAR_FORCES = [90.0, -63.6, 516.2]  # ab, bc, ac (kN, tension +)

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        r3 = math.sqrt(3)

        cls.a = cls.model.nodes.add_node(4000 * r3, 4000, 0)
        cls.b = cls.model.nodes.add_node(4000 * (1 + r3), 0, 0)
        cls.c = cls.model.nodes.add_node(0, 0, 0)
        cls.a.restraint = [0, 0, 1, 1, 1, 1]
        cls.b.restraint = [0, 1, 1, 1, 1, 1]  # roller
        cls.c.restraint = [1, 1, 1, 1, 1, 1]  # pin

        pin = [0, 0, 0, 0, 1, 1]
        cls.ab = cls.model.members.add_member(
            cls.a, cls.b, i_release=pin, j_release=pin, E=cls.E, A=20e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.bc = cls.model.members.add_member(
            cls.b, cls.c, i_release=pin, j_release=pin, E=cls.E, A=18e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.ac = cls.model.members.add_member(
            cls.a, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)

        cls.a.add_load(cls.PX, 'force', 'X')
        cls.a.add_load(cls.PY, 'force', 'Y')

        cls.model.solve()

    def test_displacements(self):
        np.testing.assert_allclose(
            [self.a.Ux, self.a.Uy, self.b.Ux], self.BOOK_DISPLACEMENTS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions(self):
        np.testing.assert_allclose(
            [self.b.Ry, self.c.Rx, self.c.Ry], self.BOOK_REACTIONS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_bar_forces(self):
        # With one element per bar, the axial result at the j end of the
        # bar's only submember is its tension.
        forces = [next(iter(bar.submembers.values())).results['axial'][1]
                  for bar in (self.ab, self.bc, self.ac)]
        np.testing.assert_allclose(
            forces, self.BOOK_BAR_FORCES, rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Only the
        # support reactions are summed, against the load as written in this
        # class, so a load that the solver lost or misapplied fails here.
        # Moments are taken about c, the origin; the load acts at a.
        sum_fx = self.PX
        sum_fy = self.PY
        sum_mz = (self.a.coordinates.x * self.PY
                  - self.a.coordinates.y * self.PX)
        for node in (self.b, self.c):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 500)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 500)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 500 * 10000)


# Example 3.3 (pp. 38-39): the truss of Example 3.2 with a horizontal tie ad
# from a to a pin at d, 6.928 m to the left of a (so d is directly above c).
# A = 20e3 mm^2 for ad.
class TestExample3_3_TriangularTrussWithTie:
    E = 200.0  # kN/mm^2

    # The book's worst gap from an exact solve is 4.1e-3 (R_xc, -163.2 kN
    # against -162.53 kN). RTOL = 1e-2 leaves 2x headroom.
    RTOL = 1e-2
    ATOL = 1e-6

    # The 500 kN load at a, 40 degrees above the horizontal (kN).
    PX = 500 * math.cos(math.radians(40))
    PY = 500 * math.sin(math.radians(40))

    BOOK_DISPLACEMENTS = [0.383, 1.228, -0.437]  # u_a, v_a, u_b (mm)
    # R_yb, R_xc, R_yc, R_xd (kN)
    BOOK_REACTIONS = [-144.3, -163.2, -177.4, -221.1]

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        r3 = math.sqrt(3)

        cls.a = cls.model.nodes.add_node(4000 * r3, 4000, 0)
        cls.b = cls.model.nodes.add_node(4000 * (1 + r3), 0, 0)
        cls.c = cls.model.nodes.add_node(0, 0, 0)
        cls.d = cls.model.nodes.add_node(0, 4000, 0)
        cls.a.restraint = [0, 0, 1, 1, 1, 1]
        cls.b.restraint = [0, 1, 1, 1, 1, 1]  # roller
        cls.c.restraint = [1, 1, 1, 1, 1, 1]  # pin
        cls.d.restraint = [1, 1, 1, 1, 1, 1]  # pin

        pin = [0, 0, 0, 0, 1, 1]
        cls.model.members.add_member(
            cls.a, cls.b, i_release=pin, j_release=pin, E=cls.E, A=20e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.b, cls.c, i_release=pin, j_release=pin, E=cls.E, A=18e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.a, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.a, cls.d, i_release=pin, j_release=pin, E=cls.E, A=20e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)

        cls.a.add_load(cls.PX, 'force', 'X')
        cls.a.add_load(cls.PY, 'force', 'Y')

        cls.model.solve()

    def test_displacements(self):
        np.testing.assert_allclose(
            [self.a.Ux, self.a.Uy, self.b.Ux], self.BOOK_DISPLACEMENTS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions(self):
        np.testing.assert_allclose(
            [self.b.Ry, self.c.Rx, self.c.Ry, self.d.Rx],
            self.BOOK_REACTIONS, rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Only the
        # support reactions are summed, against the load as written in this
        # class, so a load that the solver lost or misapplied fails here.
        # Moments are taken about c, the origin; the load acts at a.
        sum_fx = self.PX
        sum_fy = self.PY
        sum_mz = (self.a.coordinates.x * self.PY
                  - self.a.coordinates.y * self.PX)
        for node in (self.b, self.c, self.d):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 500)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 500)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 500 * 10000)


# Examples 3.4 to 3.6 share this truss:
#
#                c ------- d
#              / |   cd   /
#        ac  /   |      /
#          /  bc |    /  bd
#        /       |  /
#      a ------- b
#          ab
#
# ab and cd are horizontal and 5 m long; ac and bd are at 60 degrees, so they
# are 10 m long and c is directly above b, 5 sqrt(3) m up; bc is vertical.
# A = 10e3 mm^2 (ab, cd) and 15e3 mm^2 (ac, bd, bc). A 400 kN load acts at d,
# 45 degrees below the horizontal, to the right: 282.84 kN in each
# direction.


# Example 3.5 (pp. 44-46): the truss of Example 3.4 on a pin at a and a
# roller at b. (The p. 43 misprint in Example 3.4's member ac matrix does not
# reach the assembled equations used here.)
class TestExample3_5_TrussOnPinAndRoller:
    E = 200.0  # kN/mm^2

    # The book's worst gap from an exact solve is 3.1e-3 (u_b, -0.407 mm
    # against -0.40825 mm, and bar ab). RTOL = 7e-3 leaves 2x headroom.
    RTOL = 7e-3
    ATOL = 1e-6

    # The 400 kN load at d, 45 degrees below the horizontal (kN).
    PX = 200 * math.sqrt(2)
    PY = -200 * math.sqrt(2)

    # u_b, u_c, v_c, u_d, v_d (mm)
    BOOK_DISPLACEMENTS = [-0.407, 9.809, -2.232, 10.926, -7.801]
    BOOK_REACTIONS = [-282.9, -772.0, 1056.2]  # R_xa, R_ya, R_yb (kN)
    # ab, cd, ac, bd, bc (kN, tension +)
    BOOK_BAR_FORCES = [-162.8, 446.8, 891.4, -326.8, -773.2]

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        h = 5000 * math.sqrt(3)

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.b = cls.model.nodes.add_node(5000, 0, 0)
        cls.c = cls.model.nodes.add_node(5000, h, 0)
        cls.d = cls.model.nodes.add_node(10000, h, 0)
        cls.a.restraint = [1, 1, 1, 1, 1, 1]  # pin
        cls.b.restraint = [0, 1, 1, 1, 1, 1]  # roller
        cls.c.restraint = [0, 0, 1, 1, 1, 1]
        cls.d.restraint = [0, 0, 1, 1, 1, 1]

        pin = [0, 0, 0, 0, 1, 1]
        cls.ab = cls.model.members.add_member(
            cls.a, cls.b, i_release=pin, j_release=pin, E=cls.E, A=10e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.cd = cls.model.members.add_member(
            cls.c, cls.d, i_release=pin, j_release=pin, E=cls.E, A=10e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.ac = cls.model.members.add_member(
            cls.a, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.bd = cls.model.members.add_member(
            cls.b, cls.d, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.bc = cls.model.members.add_member(
            cls.b, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)

        cls.d.add_load(cls.PX, 'force', 'X')
        cls.d.add_load(cls.PY, 'force', 'Y')

        cls.model.solve()

    def test_displacements(self):
        b, c, d = self.b, self.c, self.d
        np.testing.assert_allclose(
            [b.Ux, c.Ux, c.Uy, d.Ux, d.Uy], self.BOOK_DISPLACEMENTS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions(self):
        np.testing.assert_allclose(
            [self.a.Rx, self.a.Ry, self.b.Ry], self.BOOK_REACTIONS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_bar_forces(self):
        # With one element per bar, the axial result at the j end of the
        # bar's only submember is its tension.
        bars = (self.ab, self.cd, self.ac, self.bd, self.bc)
        forces = [next(iter(bar.submembers.values())).results['axial'][1]
                  for bar in bars]
        np.testing.assert_allclose(
            forces, self.BOOK_BAR_FORCES, rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Only the
        # support reactions are summed, against the load as written in this
        # class, so a load that the solver lost or misapplied fails here.
        # Moments are taken about a, the origin; the load acts at d.
        sum_fx = self.PX
        sum_fy = self.PY
        sum_mz = (self.d.coordinates.x * self.PY
                  - self.d.coordinates.y * self.PX)
        for node in (self.a, self.b):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 400)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 400)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 400 * 10000)


# Example 3.6 (p. 46): the truss of Example 3.5 with b also held
# horizontally and c held horizontally (free to move vertically). The book
# prints only the displacements at c and d.
class TestExample3_6_TrussWithExtraRestraints:
    E = 200.0  # kN/mm^2

    # The book's worst gap from an exact solve is 1.2e-3 (u_d, 1.114 mm
    # against 1.1154 mm). RTOL = 3e-3 leaves 2x headroom. v_c is printed as
    # 0, which ATOL covers.
    RTOL = 3e-3
    ATOL = 1e-6

    # The 400 kN load at d, 45 degrees below the horizontal (kN).
    PX = 200 * math.sqrt(2)
    PY = -200 * math.sqrt(2)

    BOOK_DISPLACEMENTS = [0.0, 1.114, -1.901]  # v_c, u_d, v_d (mm)

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        cls.model = Model(plane='xy')
        h = 5000 * math.sqrt(3)

        cls.a = cls.model.nodes.add_node(0, 0, 0)
        cls.b = cls.model.nodes.add_node(5000, 0, 0)
        cls.c = cls.model.nodes.add_node(5000, h, 0)
        cls.d = cls.model.nodes.add_node(10000, h, 0)
        cls.a.restraint = [1, 1, 1, 1, 1, 1]  # pin
        cls.b.restraint = [1, 1, 1, 1, 1, 1]  # pin
        cls.c.restraint = [1, 0, 1, 1, 1, 1]  # held horizontally
        cls.d.restraint = [0, 0, 1, 1, 1, 1]

        pin = [0, 0, 0, 0, 1, 1]
        cls.model.members.add_member(
            cls.a, cls.b, i_release=pin, j_release=pin, E=cls.E, A=10e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.c, cls.d, i_release=pin, j_release=pin, E=cls.E, A=10e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.a, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.b, cls.d, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)
        cls.model.members.add_member(
            cls.b, cls.c, i_release=pin, j_release=pin, E=cls.E, A=15e3,
            Ixx=1e6, Iyy=1e6, G=80.0, J=1e6, mesh=1)

        cls.d.add_load(cls.PX, 'force', 'X')
        cls.d.add_load(cls.PY, 'force', 'Y')

        cls.model.solve()

    def test_displacements(self):
        np.testing.assert_allclose(
            [self.c.Uy, self.d.Ux, self.d.Uy], self.BOOK_DISPLACEMENTS,
            rtol=self.RTOL, atol=self.ATOL)

    def test_reactions_balance_the_loads(self):
        # Statics holds exactly, independent of the book's rounding. Only the
        # support reactions are summed, against the load as written in this
        # class, so a load that the solver lost or misapplied fails here.
        # Moments are taken about a, the origin; the load acts at d.
        sum_fx = self.PX
        sum_fy = self.PY
        sum_mz = (self.d.coordinates.x * self.PY
                  - self.d.coordinates.y * self.PX)
        for node in (self.a, self.b, self.c):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 400)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 400)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 400 * 10000)
