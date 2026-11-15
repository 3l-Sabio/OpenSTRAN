import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


# A portal frame with pinned bases in the global X-Y plane. The beam carries a
# uniformly distributed gravity load. Every member has the same section.
#
#       N2 +-----------+ N3        h = column height
#          |           |           L = beam span
#          |           |
#       N1 o           o N4
#
# The vertical reactions (w * L / 2 each) and the balance of the horizontal
# reactions are derived from statics and symmetry.
#
# The horizontal thrust comes from the classic rigid frame formula, which
# ignores axial shortening of the members:
#
#   H = w * L**2 / (4 * h * (2 * k + 3)),  k = h / L for equal sections
#
# OpenSTRAN includes axial shortening, so values built on H are compared with
# a tolerance of 1%.
@pytest.mark.parametrize("h", [120., 180.], scope="class")
@pytest.mark.parametrize("L", [144., 240., 360.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("w", [2.6/12], scope="class")
class TestPortalFrame:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, h: float, L: float, s: str, w: float):
        # run once per parameter set; the test methods share the solved model
        cls.test_model = Model(plane='xy')
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(0, h, 0)
        cls.N3 = cls.test_model.nodes.add_node(L, h, 0)
        cls.N4 = cls.test_model.nodes.add_node(L, 0, 0)

        # pinned bases; the X-Y plane already holds the out-of-plane movement
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

        cls.M2.add_distributed_load(-w, -w, "Y", 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def thrust(self, w: float, h: float, L: float) -> float:
        # horizontal reaction at each base, in kips
        k = h / L
        return w * L ** 2 / (4 * h * (2 * k + 3))

    def test_max_moment(self, w: float, h: float, L: float):
        knee = self.thrust(w, h, L) * h      # at the top of each column
        midspan = w * L ** 2 / 8 - knee      # at the center of the beam
        expected = max(knee, midspan)
        assert self.test_model.Mzz_max == pytest.approx(expected, rel=1e-2)

    def test_max_shear(self, w: float, L: float):
        expected = w * L / 2  # at each end of the beam
        assert self.test_model.Vy_max == pytest.approx(expected)

    def test_max_axial(self, w: float, L: float):
        expected = w * L / 2  # in each column
        assert self.test_model.axial_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float):
        expected = w * L / 2
        assert self.test_model.Ry_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, h: float, L: float):
        knee = self.thrust(w, h, L) * h       # kip-in
        column_load = w * L / 2               # kips
        ei = self.E * self.shape.Ix
        # midspan of the beam: a simple span deflection, reduced by the end
        # moments at the knees, plus the shortening of the columns
        expected = 5 * w * L ** 4 / (384 * ei) - knee * L ** 2 / (8 * ei) \
            + column_load * h / (self.E * self.shape.A)
        assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-2)

    def test_node_reaction_1(self, w: float, L: float):
        expected = w * L / 2
        assert self.N1.Ry == pytest.approx(expected)

    def test_node_reaction_4(self, w: float, L: float):
        expected = w * L / 2
        assert self.N4.Ry == pytest.approx(expected)

    def test_horizontal_thrust(self, w: float, h: float, L: float):
        expected = self.thrust(w, h, L)
        # the bases are pushed outward, so the supports push back inward
        assert self.N1.Rx == pytest.approx(expected, rel=1e-2)
        assert self.N4.Rx == pytest.approx(-expected, rel=1e-2)

    def test_equilibrium(self, w: float, L: float):
        # the reactions balance the applied load
        assert self.N1.Rx + self.N4.Rx == pytest.approx(0, abs=1e-6)
        assert self.N1.Ry + self.N4.Ry == pytest.approx(w * L)

    def test_no_base_moment(self):
        # pinned bases carry no moment
        assert self.N1.Rmz == pytest.approx(0, abs=1e-6)
        assert self.N4.Rmz == pytest.approx(0, abs=1e-6)
