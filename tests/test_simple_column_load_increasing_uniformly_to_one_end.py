import pytest

from math import sqrt

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [87., 120., 207.96], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("w", [1.25/12, 5.3/12], scope="class")
@pytest.mark.parametrize("axis", ["X", "Z"], scope="class")
class TestSimpleColumn:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, axis: str):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(0, L, 0)

        # pinned supports; torsion is about the global Y axis for this member
        cls.N1.restraint = [1, 1, 1, 0, 1, 0]
        cls.N2.restraint = [1, 1, 1, 0, 1, 0]

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.M1.add_distributed_load(0, -w, axis, 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / (9 * sqrt(3))
        if axis == "X":
            assert self.test_model.Mzz_max == pytest.approx(expected)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "X":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "X":
            assert self.test_model.Rx_max == pytest.approx(expected)
        else:
            assert self.test_model.Rz_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float, axis: str):
        W = w * L / 2  # total load
        xi = sqrt(1 - sqrt(8 / 15))  # location of max deflection, x/L
        c = 2 * xi * (7 - 10 * xi**2 + 3 * xi**4) / 360
        if axis == "X":
            expected = c * W * L ** 3 / (self.E * self.shape.Ix)
            assert self.test_model.Ux_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = c * W * L ** 3 / (self.E * self.shape.Iy)
            assert self.test_model.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, axis: str):
        expected = w * L / 6
        if axis == "X":
            assert self.N1.Rx == pytest.approx(expected)
        else:
            assert self.N1.Rz == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, axis: str):
        expected = w * L / 3
        if axis == "X":
            assert self.N2.Rx == pytest.approx(expected)
        else:
            assert self.N2.Rz == pytest.approx(expected)
