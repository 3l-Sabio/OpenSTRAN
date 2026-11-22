import math

import numpy as np
import pytest

from OpenSTRAN import Model
from OpenSTRAN.Node import Node


# Worked examples from Chapter 13 of W. McGuire, R. H. Gallagher and
# R. D. Ziemian, "Matrix Structural Analysis", 2nd edition. Each class
# rebuilds one example and checks OpenSTRAN against the values printed in the
# book. Units are those of the book (kN and mm).
#
# Each class sets its own RTOL and ATOL to match how precisely its source
# values are printed.


# Example 13.11 (pp. 407-408): joint displacements of a symmetric gable frame,
# found by splitting the loads into symmetric and antisymmetric parts.
#
#                     10 kN
#                       |
#                       v
#                       c
#                     /   \
#           bc      /       \      cd
#                 /           \
#      5 kN ->  b               d  <- 5 kN acts to the right at d too
#               |               |
#          ab   |               |   ed
#               |               |
#               a               e
#
# a and e are fixed. ab and ed are vertical, 5 m long, with A = 4e3 mm^2 and
# I = 50e6 mm^4. bc and cd are 8 m long and rise 3 m to the apex, with
# A = 6e3 mm^2 and I = 200e6 mm^4. E = 200,000 MPa. The book prints each
# half-span as 7.416 m, which is sqrt(55) m rounded; the exact value is used,
# as in Example 5.3.
#
# The book solves half the frame twice: a symmetric part, with 5 kN (half of
# the 10 kN apex load) at c, and an antisymmetric part, with 5 kN to the
# right at b. On the whole frame these are the 10 kN apex load alone, and
# the two 5 kN side loads alone, so each part is built here as its own
# model.
class TestExample13_11_SymmetricGableFrame:
    E = 200.0  # kN/mm^2

    # The book's printed results are about 0.5% larger than the exact
    # solution of the stiffness equations it prints (up to 5.0e-3, u_c of
    # the antisymmetric part). The solution of those printed equations
    # agrees with OpenSTRAN to within 4e-4, so the excess appears to be in
    # the book's arithmetic; its cause is unknown, and the printed values
    # were taken from a transcription, not re-checked against the page.
    # RTOL = 1e-2 leaves 2x headroom. The symmetry and equilibrium tests
    # check the results tightly.
    RTOL = 1e-2
    ATOL = 1e-6

    # Symmetric part: u_b, v_b, theta_b, v_c (mm, mm, rad, mm).
    BOOK_SYMMETRIC = [-2.208, -0.0313, -0.611e-3, -5.583]
    # Antisymmetric part: u_b, v_b, theta_b, u_c, theta_c.
    BOOK_ANTISYMMETRIC = [7.085, 0.0093, -0.7403e-3, 7.093, 0.3680e-3]

    # The joints of each load case's model, by name; filled in by
    # setup_models.
    symmetric: dict[str, Node]
    antisymmetric: dict[str, Node]

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_models(cls):
        cx = 1000 * math.sqrt(55)

        # The same frame is built twice, once for each load case.
        for symmetric in (True, False):
            model = Model(plane='xy')
            a = model.nodes.add_node(0, 0, 0)
            b = model.nodes.add_node(0, 5000, 0)
            c = model.nodes.add_node(cx, 8000, 0)
            d = model.nodes.add_node(2 * cx, 5000, 0)
            e = model.nodes.add_node(2 * cx, 0, 0)
            a.restraint = [1, 1, 1, 1, 1, 1]
            e.restraint = [1, 1, 1, 1, 1, 1]

            # One element per member. As in Example 5.3, Iyy differs from
            # Ixx so that bending about the wrong axis would show up.
            model.members.add_member(
                a, b, E=cls.E, A=4e3, Ixx=50e6, Iyy=5e6, G=80.0, J=1e6,
                mesh=1)
            model.members.add_member(
                b, c, E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=80.0, J=1e6,
                mesh=1)
            model.members.add_member(
                c, d, E=cls.E, A=6e3, Ixx=200e6, Iyy=20e6, G=80.0, J=1e6,
                mesh=1)
            model.members.add_member(
                e, d, E=cls.E, A=4e3, Ixx=50e6, Iyy=5e6, G=80.0, J=1e6,
                mesh=1)

            if symmetric:
                c.add_load(-10.0, 'force', 'Y')
            else:
                b.add_load(5.0, 'force', 'X')
                d.add_load(5.0, 'force', 'X')

            results = model.solve()

            # The nodes, and their displacements and reactions, by name.
            nodes = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e}
            solved = {name: results.node(node) for name, node in nodes.items()}
            if symmetric:
                cls.symmetric, cls.symmetric_nodes = solved, nodes
            else:
                cls.antisymmetric, cls.antisymmetric_nodes = solved, nodes

    def test_symmetric_part(self):
        b, c = self.symmetric['b'], self.symmetric['c']
        np.testing.assert_allclose(
            [b.Ux, b.Uy, b.phi_z, c.Uy], self.BOOK_SYMMETRIC,
            rtol=self.RTOL, atol=self.ATOL)

    def test_antisymmetric_part(self):
        b, c = self.antisymmetric['b'], self.antisymmetric['c']
        np.testing.assert_allclose(
            [b.Ux, b.Uy, b.phi_z, c.Ux, c.phi_z], self.BOOK_ANTISYMMETRIC,
            rtol=self.RTOL, atol=self.ATOL)

    def test_symmetric_part_is_symmetric(self):
        # The book's boundary conditions on the plane of symmetry: u_c and
        # theta_c are zero. d mirrors b.
        b, c, d = (self.symmetric[n] for n in 'bcd')
        np.testing.assert_allclose([c.Ux, c.phi_z], 0, atol=1e-9)
        np.testing.assert_allclose(
            [d.Ux, d.Uy, d.phi_z], [-b.Ux, b.Uy, -b.phi_z],
            rtol=1e-9, atol=1e-12)

    def test_antisymmetric_part_is_antisymmetric(self):
        # The book's boundary condition on the plane of symmetry: v_c is
        # zero. d moves with b, with the opposite vertical displacement.
        b, c, d = (self.antisymmetric[n] for n in 'bcd')
        np.testing.assert_allclose(c.Uy, 0, atol=1e-9)
        np.testing.assert_allclose(
            [d.Ux, d.Uy, d.phi_z], [b.Ux, -b.Uy, b.phi_z],
            rtol=1e-9, atol=1e-12)

    @pytest.mark.parametrize("symmetric", [True, False])
    def test_reactions_balance_the_loads(self, symmetric: bool):
        # Statics holds exactly, independent of the book's rounding. Only the
        # reactions at the supports a and e are summed, against the loads as
        # written here, so a load that the solver lost or misapplied fails
        # here. Moments are taken about a, the origin.
        nodes = self.symmetric_nodes if symmetric else self.antisymmetric_nodes
        solved = self.symmetric if symmetric else self.antisymmetric
        if symmetric:
            loads = [('c', 0.0, -10.0)]  # joint, Fx, Fy (kN)
        else:
            loads = [('b', 5.0, 0.0), ('d', 5.0, 0.0)]

        sum_fx = sum_fy = sum_mz = 0.0
        for name, fx, fy in loads:
            x, y = nodes[name].coordinates.x, nodes[name].coordinates.y
            sum_fx += fx
            sum_fy += fy
            sum_mz += x * fy - y * fx
        for name in ('a', 'e'):
            x, y = nodes[name].coordinates.x, nodes[name].coordinates.y
            r = solved[name]
            sum_fx += r.Rx
            sum_fy += r.Ry
            sum_mz += r.Rmz + x * r.Ry - y * r.Rx

        assert sum_fx == pytest.approx(0, abs=1e-9 * 10)
        assert sum_fy == pytest.approx(0, abs=1e-9 * 10)
        assert sum_mz == pytest.approx(0, abs=1e-9 * 10 * 20000)
