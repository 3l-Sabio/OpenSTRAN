import pytest

from OpenSTRAN import Model
from OpenSTRAN import Shape


# A portal frame with pinned bases in the global X-Y plane. A lateral load P
# acts along +X at the top of the left column and every member has the same
# section.
#
#     P -> N2 +-----------+ N3     h = column height
#             |           |        L = beam span
#             |           |
#          N1 o           o N4
#
# The vertical reactions (P * h / L, down at N1 and up at N4) and the total
# horizontal reaction follow from statics alone.
#
# The split of the horizontal reaction (P / 2 at each base), the knee moment
# (P * h / 2) and the sway come from formulas that simplify the axial
# shortening of the members, so they are compared with a tolerance of 1%.
@pytest.mark.parametrize("h", [120., 180.], scope="class")
@pytest.mark.parametrize("L", [144., 240., 360.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("P", [7.5], scope="class")
class TestPortalFrame:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, h: float, L: float, s: str, P: float):
        cls.test_model = Model(plane='xy')
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(0, h, 0)
        cls.N3 = cls.test_model.nodes.add_node(L, h, 0)
        cls.N4 = cls.test_model.nodes.add_node(L, 0, 0)

        # pinned bases; the X-Y plane restrains the out-of-plane movement
        cls.N1.restraint = [1, 1, 1, 1, 1, 0]
        cls.N4.restraint = [1, 1, 1, 1, 1, 0]

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )
        cls.M2 = cls.test_model.members.add_member(
            cls.N2, cls.N3, shape=cls.shape, E=cls.E, G=cls.G
        )
        cls.M3 = cls.test_model.members.add_member(
            cls.N3, cls.N4, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.N2.add_load(P, 'force', 'X')

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, P: float, h: float):
        expected = P * h / 2  # at each knee
        assert self.test_model.Mzz_max == pytest.approx(expected, rel=1e-2)

    def test_max_shear(self, P: float, h: float, L: float):
        # the columns carry P / 2 each and the beam carries P * h / L
        expected = max(P / 2, P * h / L)
        assert self.test_model.Vy_max == pytest.approx(expected, rel=1e-2)

    def test_max_axial(self, P: float, h: float, L: float):
        # the columns carry P * h / L each and the beam carries P / 2
        expected = max(P * h / L, P / 2)
        assert self.test_model.axial_max == pytest.approx(expected, rel=1e-2)

    def test_max_reaction(self, P: float, h: float, L: float):
        expected = P * h / L
        assert self.test_model.Ry_max == pytest.approx(expected)

    def test_max_deflection(self, P: float, h: float, L: float):
        ei = self.E * self.shape.Ix
        ea = self.E * self.shape.A
        # sway of the loaded knee: bending of the beam and the columns, the
        # tilt from one column shortening while the other stretches, and half
        # of the shortening of the beam
        expected = P * h ** 2 * L / (12 * ei) + P * h ** 3 / (6 * ei) \
            + 2 * P * h ** 3 / (ea * L ** 2) + P * L / (4 * ea)
        assert self.test_model.Ux_max == pytest.approx(expected, rel=1e-2)

    def test_node_reaction_1(self, P: float, h: float, L: float):
        expected = -P * h / L  # the windward base is held down
        assert self.N1.Ry == pytest.approx(expected)

    def test_node_reaction_4(self, P: float, h: float, L: float):
        expected = P * h / L
        assert self.N4.Ry == pytest.approx(expected)

    def test_horizontal_reactions(self, P: float):
        expected = -P / 2  # each base resists half of the load
        assert self.N1.Rx == pytest.approx(expected, rel=1e-2)
        assert self.N4.Rx == pytest.approx(expected, rel=1e-2)

    def test_equilibrium(self, P: float):
        # the reactions balance the applied load
        assert self.N1.Rx + self.N4.Rx == pytest.approx(-P)
        assert self.N1.Ry + self.N4.Ry == pytest.approx(0, abs=1e-6)

    def test_no_base_moment(self):
        # pinned bases carry no moment
        assert self.N1.Rmz == pytest.approx(0, abs=1e-6)
        assert self.N4.Rmz == pytest.approx(0, abs=1e-6)
