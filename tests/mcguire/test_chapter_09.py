import pytest

from OpenSTRAN import Model
from OpenSTRAN.Member import Member
from OpenSTRAN.Node import Node


# Worked examples from Chapter 9 of W. McGuire, R. H. Gallagher and
# R. D. Ziemian, "Matrix Structural Analysis", 2nd edition: elastic critical
# loads (Equation 8.7) and second-order elastic analysis (Equation 8.3). Each
# class rebuilds one example and checks OpenSTRAN against the values printed
# in the book, in the book's units.
#
# The critical loads are the precise check of the geometric stiffness: the
# book prints them to three or four figures and OpenSTRAN agrees within
# rounding. The book's second-order results were computed by MASTAN2 with
# the geometry updated as the load is applied, whereas OpenSTRAN's
# second-order analysis keeps the undeformed geometry (P-Delta). Its
# second-order moments are therefore compared at a loose tolerance, and the
# second-order solution is checked tightly by equilibrium on the deformed
# geometry instead.
#
# The book prints moments as magnitudes on its diagrams. The values here
# carry OpenSTRAN's signs: the major-axis moment at the named end of a
# submember. Each class sets its own RTOL, about twice the largest gap
# between the book and an exact solution of the same model; where one
# example has values of very different precision (critical load, first- and
# second-order moments), each kind of check is a class of its own.


# Example 9.1 (pp. 246-248), part 1: critical load of a two-bar system.
#
#      a o-----------------o b
#                ab        |  P (down)
#                          |
#                          |  bc
#                          |
#                          o c
#
# Both members are axial force members, 4 m long. A_ab = 2 mm^2,
# A_bc = 5,000 mm^2, E = 200,000 MPa; a and c are pinned. Under the vertical
# load alone the system buckles sideways at b when P = kL = 400 kN, k being
# the axial stiffness of ab. The bars are frame members released for bending
# at both ends, so the geometric stiffness of bc must be condensed with its
# elastic stiffness to give the axial-force-member form of Equation 9.9.
class TestExample9_1_TwoBarCriticalLoad:
    # The critical load is exactly 400 kN: ab carries no axial force, and the
    # book's result does not depend on rounding.
    RTOL = 1e-6
    BOOK_PCR = 400.0  # kN

    critical_load: float

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        a = model.nodes.add_node(0, 4000, 0)
        b = model.nodes.add_node(4000, 4000, 0)
        c = model.nodes.add_node(4000, 0, 0)
        # Supports are fully restrained; the free joint's rotation is
        # restrained too, since no bar resists it.
        a.restraint = [1, 1, 1, 1, 1, 1]
        c.restraint = [1, 1, 1, 1, 1, 1]
        b.restraint = [0, 0, 1, 1, 1, 1]

        bar = [0, 0, 0, 0, 1, 1]
        model.members.add_member(
            a, b, E=200.0, A=2.0, Ixx=1.0, Iyy=1.0, G=80.0, J=1.0,
            i_release=bar, j_release=bar, mesh=1)
        model.members.add_member(
            c, b, E=200.0, A=5e3, Ixx=1.0, Iyy=1.0, G=80.0, J=1.0,
            i_release=bar, j_release=bar, mesh=1)

        # A 1 kN reference load, so the critical load factor is P_cr in kN.
        b.add_load(-1.0, 'force', 'Y')
        cls.critical_load = model.critical_load_factor()

    def test_critical_load(self):
        assert self.critical_load == pytest.approx(
            self.BOOK_PCR, rel=self.RTOL)


# Example 9.3 (pp. 249-250), part 1: critical load of a pinned column.
#
#      b o  <- slides vertically, P (down)
#        |
#        |  8 m, two elements
#        |
#      a o  pinned
#
# A = 1.27e4 mm^2, I = 3.66e7 mm^4, E = 200,000 MPa. The two-element model
# gives 1,137 kN against the exact pi^2 EI / L^2 = 1,129 kN.
class TestExample9_3_PinnedColumnCriticalLoad:
    # OpenSTRAN gives 1137.33 kN, 2.9e-4 from the book's 1,137.
    RTOL = 6e-4
    BOOK_PCR = 1137.0  # kN

    critical_load: float

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        a = model.nodes.add_node(0, 0, 0)
        b = model.nodes.add_node(0, 8000, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        b.restraint = [1, 0, 1, 1, 1, 0]

        # As in Example 5.3, Iyy differs from Ixx so that buckling about the
        # wrong axis would show up.
        model.members.add_member(
            a, b, E=200.0, A=1.27e4, Ixx=3.66e7, Iyy=3.66e6, G=80.0, J=1e6,
            mesh=2)

        b.add_load(-1.0, 'force', 'Y')
        cls.critical_load = model.critical_load_factor()

    def test_critical_load(self):
        assert self.critical_load == pytest.approx(
            self.BOOK_PCR, rel=self.RTOL)


# Example 9.4 (p. 250), part 1: critical load of a cantilever column.
#
#      b o  free, P (down)
#        |
#        |  4 m, two elements
#        |
#      a o  fixed
#
# The section is that of Example 9.3. The two-element model gives 1,129 kN,
# the exact pi^2 EI / 4L^2 to four figures.
class TestExample9_4_CantileverCriticalLoad:
    # OpenSTRAN gives 1129.41 kN, 3.7e-4 from the book's 1,129.
    RTOL = 8e-4
    BOOK_PCR = 1129.0  # kN

    critical_load: float

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        a = model.nodes.add_node(0, 0, 0)
        b = model.nodes.add_node(0, 4000, 0)
        a.restraint = [1, 1, 1, 1, 1, 1]

        model.members.add_member(
            a, b, E=200.0, A=1.27e4, Ixx=3.66e7, Iyy=3.66e6, G=80.0, J=1e6,
            mesh=2)

        b.add_load(-1.0, 'force', 'Y')
        cls.critical_load = model.critical_load_factor()

    def test_critical_load(self):
        assert self.critical_load == pytest.approx(
            self.BOOK_PCR, rel=self.RTOL)


# Example 9.5 (p. 251): critical load and first- and second-order analysis
# of a two-story frame.
#
#      P (down), aP ->  c o---------------o e  roller
#                         |      ce
#                    bc   |  4 m
#                         |
#              aP ->    b o---------------o d  roller
#                         |      bd
#                    ab   |  6 m
#                         |
#                       a o  pinned
#
# Columns ab and bc: A = 2.5e4 mm^2, I = 6.36e8 mm^4. Girders bd and ce, 4 m
# long: A = 1.76e4 mm^2, I = 8.61e8 mm^4. E = 200,000 MPa. One element per
# member. Part 1 finds P_cr under P alone (a = 0); part 2 analyzes the frame
# under P = 0.6 P_cr = 3,978 kN with a = 0.01, by first- and second-order
# analysis. Each of the three is a class of its own, with its own tolerance.
class TestExample9_5_TwoStoryFrameCriticalLoad:
    # OpenSTRAN gives 6629.62 kN, 5.7e-5 from the book's 6,630.
    RTOL = 2e-4
    BOOK_PCR = 6630.0  # kN

    critical_load: float

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        a = model.nodes.add_node(0, 0, 0)
        b = model.nodes.add_node(0, 6000, 0)
        c = model.nodes.add_node(0, 10000, 0)
        d = model.nodes.add_node(4000, 6000, 0)
        e = model.nodes.add_node(4000, 10000, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        d.restraint = [0, 1, 1, 1, 1, 0]
        e.restraint = [0, 1, 1, 1, 1, 0]

        model.members.add_member(
            a, b, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        model.members.add_member(
            b, c, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        model.members.add_member(
            b, d, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)
        model.members.add_member(
            c, e, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)

        c.add_load(-1.0, 'force', 'Y')
        cls.critical_load = model.critical_load_factor()

    def test_critical_load(self):
        assert self.critical_load == pytest.approx(
            self.BOOK_PCR, rel=self.RTOL)


class TestExample9_5_TwoStoryFrameFirstOrder:
    # OpenSTRAN's first-order moments are within 8.7e-4 of the book (461 at
    # b, which OpenSTRAN gives as 461.40).
    RTOL = 2e-3
    P = 3978.0  # kN
    ALPHA = 0.01

    # Moments (kN m): top of bc at c, top of ab at b, end b of girder bd.
    BOOK_MOMENTS = [175.0, 477.0, -461.0]

    a: Node
    b: Node
    c: Node
    d: Node
    e: Node
    ab: Member
    bc: Member
    bd: Member

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        cls.a = a = model.nodes.add_node(0, 0, 0)
        cls.b = b = model.nodes.add_node(0, 6000, 0)
        cls.c = c = model.nodes.add_node(0, 10000, 0)
        cls.d = d = model.nodes.add_node(4000, 6000, 0)
        cls.e = e = model.nodes.add_node(4000, 10000, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        d.restraint = [0, 1, 1, 1, 1, 0]
        e.restraint = [0, 1, 1, 1, 1, 0]

        cls.ab = model.members.add_member(
            a, b, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        cls.bc = model.members.add_member(
            b, c, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        cls.bd = model.members.add_member(
            b, d, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)
        model.members.add_member(
            c, e, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)

        c.add_load(-cls.P, 'force', 'Y')
        c.add_load(cls.ALPHA * cls.P, 'force', 'X')
        b.add_load(cls.ALPHA * cls.P, 'force', 'X')
        model.solve()

    def test_moments(self):
        moments = [
            next(iter(self.bc.submembers.values())
                 ).results['major axis moments'][1],
            next(iter(self.ab.submembers.values())
                 ).results['major axis moments'][1],
            next(iter(self.bd.submembers.values())
                 ).results['major axis moments'][0],
        ]
        assert [m / 1000 for m in moments] == pytest.approx(
            self.BOOK_MOMENTS, rel=self.RTOL)

    def test_reactions_balance_the_loads(self):
        # Statics on the undeformed geometry holds exactly in a first-order
        # analysis. Only the support reactions are summed, against the loads
        # as written here. Moments are taken about a, the origin.
        sum_fx = 2 * self.ALPHA * self.P
        sum_fy = -self.P
        sum_mz = (-self.c.coordinates.y * self.ALPHA * self.P
                  - self.b.coordinates.y * self.ALPHA * self.P)
        for node in (self.a, self.d, self.e):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-6)
        assert sum_fy == pytest.approx(0, abs=1e-6)
        assert sum_mz == pytest.approx(0, abs=1e-6 * self.P * 10000)


class TestExample9_5_TwoStoryFrameSecondOrder:
    # OpenSTRAN's P-Delta moments are 3.0% to 4.4% above the book's (907.1
    # against 869 at b in bd), which an independent P-Delta solve confirms
    # to all digits. The difference is the book's updated geometry, so this
    # tolerance only catches gross errors; the deformed-equilibrium test
    # checks the second-order solution tightly.
    RTOL = 0.1
    P = 3978.0  # kN
    ALPHA = 0.01

    # Moments (kN m): top of bc at c, top of ab at b, end b of girder bd.
    BOOK_MOMENTS = [272.0, 932.0, -869.0]

    a: Node
    b: Node
    c: Node
    d: Node
    e: Node
    ab: Member
    bc: Member
    bd: Member

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        cls.a = a = model.nodes.add_node(0, 0, 0)
        cls.b = b = model.nodes.add_node(0, 6000, 0)
        cls.c = c = model.nodes.add_node(0, 10000, 0)
        cls.d = d = model.nodes.add_node(4000, 6000, 0)
        cls.e = e = model.nodes.add_node(4000, 10000, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        d.restraint = [0, 1, 1, 1, 1, 0]
        e.restraint = [0, 1, 1, 1, 1, 0]

        cls.ab = model.members.add_member(
            a, b, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        cls.bc = model.members.add_member(
            b, c, E=200.0, A=2.5e4, Ixx=6.36e8, Iyy=6.36e7, G=80.0, J=1e6,
            mesh=1)
        cls.bd = model.members.add_member(
            b, d, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)
        model.members.add_member(
            c, e, E=200.0, A=1.76e4, Ixx=8.61e8, Iyy=8.61e7, G=80.0, J=1e6,
            mesh=1)

        c.add_load(-cls.P, 'force', 'Y')
        c.add_load(cls.ALPHA * cls.P, 'force', 'X')
        b.add_load(cls.ALPHA * cls.P, 'force', 'X')
        model.solve(second_order=True)

    def test_moments(self):
        moments = [
            next(iter(self.bc.submembers.values())
                 ).results['major axis moments'][1],
            next(iter(self.ab.submembers.values())
                 ).results['major axis moments'][1],
            next(iter(self.bd.submembers.values())
                 ).results['major axis moments'][0],
        ]
        assert [m / 1000 for m in moments] == pytest.approx(
            self.BOOK_MOMENTS, rel=self.RTOL)

    def test_equilibrium_on_deformed_geometry(self):
        # Forces balance exactly. Moments are summed about the origin with
        # every joint at its displaced position: the second-order solution
        # balances there, to within the accuracy of the P-Delta
        # approximation (0.09% of the P-Delta moment here). A first-order
        # solution would be out by the whole P-Delta moment.
        loads = [(self.c, self.ALPHA * self.P, -self.P),
                 (self.b, self.ALPHA * self.P, 0.0)]

        sum_fx = sum_fy = sum_mz = p_delta = 0.0
        for node, fx, fy in loads:
            x = node.coordinates.x + node.Ux
            y = node.coordinates.y + node.Uy
            sum_fx += fx
            sum_fy += fy
            sum_mz += x * fy - y * fx
            p_delta += abs(node.Ux * fy) + abs(node.Uy * fx)
        for node in (self.a, self.d, self.e):
            x = node.coordinates.x + node.Ux
            y = node.coordinates.y + node.Uy
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += node.Rmz + x * node.Ry - y * node.Rx

        assert sum_fx == pytest.approx(0, abs=1e-6)
        assert sum_fy == pytest.approx(0, abs=1e-6)
        assert abs(sum_mz) < 0.01 * p_delta


# Example 9.6 (p. 252): critical load and first- and second-order analysis
# of a portal frame.
#
#              6 k ->  b o--------o----------------o d  <- 120 k (down)
#                        |  bc    c       cd       |
#                        |      60 k (down)        |
#                   ab   |  24 ft                  |  ed
#                        |                         |
#                      a o  pinned                 o e  pinned
#
# Columns ab and ed (W10x45): A = 13.3 in^2, I = 248 in^4, two elements
# each. Girder (W27x84): A = 24.8 in^2, I = 2850 in^4, with bc = 20 ft and
# cd = 40 ft, one element each. E = 29,000 ksi. Units are kips and inches.
# As in Example 9.5, each analysis is a class of its own.
class TestExample9_6_PortalFrameCriticalLoad:
    # OpenSTRAN gives 2.1990, 4.6e-4 from the book's 2.20.
    RTOL = 1e-3
    BOOK_LAMBDA = 2.20

    critical_load: float

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        a = model.nodes.add_node(0, 0, 0)
        b = model.nodes.add_node(0, 288, 0)
        c = model.nodes.add_node(240, 288, 0)
        d = model.nodes.add_node(720, 288, 0)
        e = model.nodes.add_node(720, 0, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        e.restraint = [1, 1, 1, 1, 1, 0]

        model.members.add_member(
            a, b, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)
        model.members.add_member(
            b, c, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        model.members.add_member(
            c, d, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        model.members.add_member(
            e, d, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)

        b.add_load(6.0, 'force', 'X')
        c.add_load(-60.0, 'force', 'Y')
        d.add_load(-120.0, 'force', 'Y')
        cls.critical_load = model.critical_load_factor()

    def test_critical_load_factor(self):
        assert self.critical_load == pytest.approx(
            self.BOOK_LAMBDA, rel=self.RTOL)


class TestExample9_6_PortalFrameFirstOrder:
    # OpenSTRAN's first-order moments are within 9.5e-4 of the book (316 at
    # b, which OpenSTRAN gives as 316.3).
    RTOL = 2e-3

    # Moments (in-kips): girder at b, at c and at d.
    BOOK_MOMENTS = [316.0, 8708.0, -2044.0]

    a: Node
    b: Node
    c: Node
    d: Node
    e: Node
    bc: Member
    cd: Member

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        cls.a = a = model.nodes.add_node(0, 0, 0)
        cls.b = b = model.nodes.add_node(0, 288, 0)
        cls.c = c = model.nodes.add_node(240, 288, 0)
        cls.d = d = model.nodes.add_node(720, 288, 0)
        cls.e = e = model.nodes.add_node(720, 0, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        e.restraint = [1, 1, 1, 1, 1, 0]

        model.members.add_member(
            a, b, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)
        cls.bc = model.members.add_member(
            b, c, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        cls.cd = model.members.add_member(
            c, d, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        model.members.add_member(
            e, d, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)

        b.add_load(6.0, 'force', 'X')
        c.add_load(-60.0, 'force', 'Y')
        d.add_load(-120.0, 'force', 'Y')
        model.solve()

    def test_girder_moments(self):
        bc_end = next(iter(self.bc.submembers.values())
                      ).results['major axis moments']
        cd_end = next(iter(self.cd.submembers.values())
                      ).results['major axis moments']
        assert [bc_end[0], bc_end[1], cd_end[1]] == pytest.approx(
            self.BOOK_MOMENTS, rel=self.RTOL)

    def test_reactions_balance_the_loads(self):
        # Statics on the undeformed geometry, about a (the origin), with the
        # loads as written here.
        loads = [(self.b, 6.0, 0.0), (self.c, 0.0, -60.0),
                 (self.d, 0.0, -120.0)]
        sum_fx = sum_fy = sum_mz = 0.0
        for node, fx, fy in loads:
            sum_fx += fx
            sum_fy += fy
            sum_mz += node.coordinates.x * fy - node.coordinates.y * fx
        for node in (self.a, self.e):
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += (node.Rmz + node.coordinates.x * node.Ry
                       - node.coordinates.y * node.Rx)

        assert sum_fx == pytest.approx(0, abs=1e-9 * 180)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 180)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 180 * 720)


class TestExample9_6_PortalFrameSecondOrder:
    # OpenSTRAN's P-Delta moments are 0.1% to 6.0% above the book's (550.1
    # against 519 at b), which an independent P-Delta solve confirms to all
    # digits. As in Example 9.5 the difference is the book's updated
    # geometry.
    RTOL = 0.12

    # Moments (in-kips): girder at b, at c and at d. The moment at b changes
    # sign from the first-order analysis, as the book notes.
    BOOK_MOMENTS = [-519.0, 9078.0, -2661.0]
    # Moment at mid-height of column ed (in-kips); the book prints no
    # first-order value here. The transcription of the figure places 1660
    # "in the right column below d", read here as the mid-height node;
    # OpenSTRAN gives 1667.3. Not re-checked against the page.
    BOOK_MID_ED = 1660.0

    a: Node
    b: Node
    c: Node
    d: Node
    e: Node
    bc: Member
    cd: Member
    ed: Member

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls):
        model = Model(plane='xy')
        cls.a = a = model.nodes.add_node(0, 0, 0)
        cls.b = b = model.nodes.add_node(0, 288, 0)
        cls.c = c = model.nodes.add_node(240, 288, 0)
        cls.d = d = model.nodes.add_node(720, 288, 0)
        cls.e = e = model.nodes.add_node(720, 0, 0)
        a.restraint = [1, 1, 1, 1, 1, 0]
        e.restraint = [1, 1, 1, 1, 1, 0]

        model.members.add_member(
            a, b, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)
        cls.bc = model.members.add_member(
            b, c, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        cls.cd = model.members.add_member(
            c, d, E=29000.0, A=24.8, Ixx=2850.0, Iyy=106.0, G=11200.0,
            J=2.81, mesh=1)
        cls.ed = model.members.add_member(
            e, d, E=29000.0, A=13.3, Ixx=248.0, Iyy=53.4, G=11200.0, J=1.51,
            mesh=2)

        b.add_load(6.0, 'force', 'X')
        c.add_load(-60.0, 'force', 'Y')
        d.add_load(-120.0, 'force', 'Y')
        model.solve(second_order=True)

    def test_girder_moments(self):
        bc_end = next(iter(self.bc.submembers.values())
                      ).results['major axis moments']
        cd_end = next(iter(self.cd.submembers.values())
                      ).results['major axis moments']
        assert [bc_end[0], bc_end[1], cd_end[1]] == pytest.approx(
            self.BOOK_MOMENTS, rel=self.RTOL)

    def test_moment_at_mid_height_of_ed(self):
        lower = next(iter(self.ed.submembers.values()))
        assert lower.results['major axis moments'][1] == pytest.approx(
            self.BOOK_MID_ED, rel=self.RTOL)

    def test_equilibrium_on_deformed_geometry(self):
        # As in Example 9.5: moments about the origin, on the displaced
        # geometry, balance to within 0.04% of the P-Delta moment here.
        loads = [(self.b, 6.0, 0.0), (self.c, 0.0, -60.0),
                 (self.d, 0.0, -120.0)]

        sum_fx = sum_fy = sum_mz = p_delta = 0.0
        for node, fx, fy in loads:
            x = node.coordinates.x + node.Ux
            y = node.coordinates.y + node.Uy
            sum_fx += fx
            sum_fy += fy
            sum_mz += x * fy - y * fx
            p_delta += abs(node.Ux * fy) + abs(node.Uy * fx)
        for node in (self.a, self.e):
            x = node.coordinates.x + node.Ux
            y = node.coordinates.y + node.Uy
            sum_fx += node.Rx
            sum_fy += node.Ry
            sum_mz += node.Rmz + x * node.Ry - y * node.Rx

        assert sum_fx == pytest.approx(0, abs=1e-6)
        assert sum_fy == pytest.approx(0, abs=1e-6)
        assert abs(sum_mz) < 0.01 * p_delta
