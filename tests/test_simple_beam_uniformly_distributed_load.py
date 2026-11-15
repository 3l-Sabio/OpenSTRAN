import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [4.75, 7.25, 10., 17.33, 26.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16", "L6X6X1/2"], scope="class")
@pytest.mark.parametrize("w", [1.25, 2.6, 5.3], scope="class")
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

        cls.M1.add_distributed_load(-w, -w, axis, 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / 8 * 12   # kip-ft -> kip-in
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(expected)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, axis: str):
        expected = w * L / 2
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, axis: str):
        expected = w * L / 2
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(expected)
        else:
            assert self.test_model.Rz_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float, axis: str):
        l = L * 12  # ft -> in
        w = w / 12  # klf -> kli
        if axis == "Y":
            expected = 5 * w * l ** 4 / (384 * self.E * self.shape.Ix)
            assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = 5 * w * l ** 4 / (384 * self.E * self.shape.Iy)
            assert self.test_model.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, axis: str):
        expected = w * L / 2
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(expected)
        else:
            assert self.N1.Rz == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, axis: str):
        expected = w * L / 2
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(expected)
        else:
            assert self.N2.Rz == pytest.approx(expected)
