import pytest

from math import hypot

from OpenSTRAN import Model
from OpenSTRAN import Shape


# A sloped simple beam (a rafter) in the global X-Y plane, pinned at the low
# end and on a horizontal roller at the high end. A uniform gravity load of w
# per foot of member length acts along global Y, so it has a component across
# the member (bending) and a component along the member (axial).
#
#   max shear           (W / 2) * cos(slope)
#   max axial           (W / 2) * sin(slope)
@pytest.mark.parametrize("run", [96., 144.], scope="class")
@pytest.mark.parametrize("rise", [36., 72., 108.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("w", [1.25/12, 5.3/12], scope="class")
class TestInclinedBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, run: float, rise: float, s: str, w: float):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(run, rise, 0)

        cls.N1.restraint = [1, 1, 1, 1, 0, 0]  # pinned
        cls.N2.restraint = [0, 1, 1, 1, 0, 0]  # roller, free along X

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.M1.add_distributed_load(-w, -w, "Y", 0, 100)

        cls.results = cls.test_model.solve()

    def test_max_moment(self, w: float, run: float, rise: float):
        length = hypot(run, rise)
        expected = w * length * run / 8
        assert self.results.Mzz_max == pytest.approx(expected)

    def test_max_shear(self, w: float, run: float, rise: float):
        length = hypot(run, rise)
        expected = w * length / 2 * (run / length)
        assert self.results.Vy_max == pytest.approx(expected)

    def test_max_axial(self, w: float, run: float, rise: float):
        length = hypot(run, rise)
        expected = w * length / 2 * (rise / length)
        assert self.results.axial_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, run: float, rise: float):
        expected = w * hypot(run, rise) / 2
        assert self.results.Ry_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, run: float, rise: float):
        length = hypot(run, rise)
        cos = run / length
        sin = rise / length
        # vertical deflection at midspan: the bending deflection under the
        # load component across the member, plus the axial shortening under
        # the component along the member, each resolved onto global Y
        bending = 5 * (w * cos) * length ** 4 / (384 * self.E * self.shape.Ix)
        axial = (w * sin) * length ** 2 / (8 * self.E * self.shape.A)
        expected = bending * cos + axial * sin
        assert self.results.Uy_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, run: float, rise: float):
        expected = w * hypot(run, rise) / 2
        assert self.results.node(self.N1).Ry == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, run: float, rise: float):
        expected = w * hypot(run, rise) / 2
        assert self.results.node(self.N2).Ry == pytest.approx(expected)

    def test_no_horizontal_reaction(self):
        # a vertical load on a pin and roller produces no horizontal reaction
        assert self.results.node(self.N1).Rx == pytest.approx(0, abs=1e-6)
