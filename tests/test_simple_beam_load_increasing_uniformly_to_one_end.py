import pytest

from math import sqrt

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [4.75, 7.25, 10., 17.33, 26.])
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16", "L6X6X1/2"])
@pytest.mark.parametrize("w", [1.25, 2.6, 5.3])
class TestSimpleBeam:
    @pytest.fixture(autouse=True)
    def setup_model(self, L: float, s: str, w: float):
        # run before every test method for the current parameter set
        self.test_model = Model()
        self.shape = Shape(s)
        self.E = 29000
        self.G = 12000

        self.N1 = self.test_model.nodes.add_node(0, 0, 0)
        self.N2 = self.test_model.nodes.add_node(L, 0, 0)

        self.N1.restraint = [1, 1, 1, 1, 0, 0]
        self.N2.restraint = [1, 1, 1, 1, 0, 0]

        self.M1 = self.test_model.members.add_member(
            self.N1, self.N2, shape=self.shape, E=self.E, G=self.G
        )

        self.M1.add_distributed_load(0, -w, "Y", 0, 100)

        self.test_model.solve()
        self.test_model.maxMbrForces()
        self.test_model.maxReactions()
        self.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float):
        expected = w * L ** 2 / (9 * sqrt(3)) * 12  # kip-ft -> kip-in
        assert self.test_model.Mzz_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float):
        expected = w * L / 3
        assert self.test_model.Vy_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float):
        expected = w * L / 3
        assert self.test_model.Ry_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float):
        l = L * 12  # ft -> in
        w = w / 12 * l / 2  # klf -> kli
        xi = sqrt(1 - sqrt(8 / 15))  # location of max deflection, x/L
        c = 2 * xi * (7 - 10 * xi**2 + 3 * xi**4) / 360
        expected = c * w * l ** 3 / (self.E * self.shape.Ix)
        assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float):
        expected = w * L / 6
        assert self.N1.Ry == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float):
        expected = w * L / 3
        assert self.N2.Ry == pytest.approx(expected)
