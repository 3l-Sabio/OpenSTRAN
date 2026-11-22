import pytest

from math import sqrt

from OpenSTRAN import Model
from OpenSTRAN import Shape


@pytest.mark.parametrize("L", [57., 87., 120., 207.96, 312.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16", "L6X6X1/2"], scope="class")
@pytest.mark.parametrize("w", [1.25/12, 2.6/12, 5.3/12], scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestSimpleBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, axis: str):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(L, 0, 0)

        cls.N1.restraint = [1, 1, 1, 1, 0, 0]
        cls.N2.restraint = [1, 1, 1, 1, 0, 0]

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.M1.add_distributed_load(0, -w, axis, 0, 100)

        cls.results = cls.test_model.solve()

    def test_max_moment(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / (9 * sqrt(3))
        if axis == "Y":
            assert self.results.Mzz_max == pytest.approx(expected)
        else:
            assert self.results.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "Y":
            assert self.results.Vy_max == pytest.approx(expected)
        else:
            assert self.results.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "Y":
            assert self.results.Ry_max == pytest.approx(expected)
        else:
            assert self.results.Rz_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float, axis: str):
        W = w * L / 2  # total load
        xi = sqrt(1 - sqrt(8 / 15))  # location of max deflection, x/L
        c = 2 * xi * (7 - 10 * xi**2 + 3 * xi**4) / 360
        if axis == "Y":
            expected = c * W * L ** 3 / (self.E * self.shape.Ix)
            assert self.results.Uy_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = c * W * L ** 3 / (self.E * self.shape.Iy)
            assert self.results.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, axis: str):
        expected = w * L / 6
        if axis == "Y":
            assert self.results.node(self.N1).Ry == pytest.approx(expected)
        else:
            assert self.results.node(self.N1).Rz == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "Y":
            assert self.results.node(self.N2).Ry == pytest.approx(expected)
        else:
            assert self.results.node(self.N2).Rz == pytest.approx(expected)
