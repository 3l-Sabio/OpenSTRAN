import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [87., 120., 207.96], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("w", [1.25/12, 5.3/12], scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestCantileverBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, axis: str):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(L, 0, 0)

        cls.N1.restraint = [1, 1, 1, 1, 1, 1]  # fixed
        cls.N2.restraint = [0, 0, 0, 0, 0, 0]  # free

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.M1.add_distributed_load(-w, -w, axis, 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / 2
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(expected)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, axis: str):
        expected = w * L
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, axis: str):
        expected = w * L
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(expected)
        else:
            assert self.test_model.Rz_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float, axis: str):
        if axis == "Y":
            expected = w * L ** 4 / (8 * self.E * self.shape.Ix)
            assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = w * L ** 4 / (8 * self.E * self.shape.Iy)
            assert self.test_model.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, axis: str):
        expected = w * L
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(expected)
        else:
            assert self.N1.Rz == pytest.approx(expected)

    def test_node_reaction_2(self, axis: str):
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(0, abs=1e-6)
        else:
            assert self.N2.Rz == pytest.approx(0, abs=1e-6)

    def test_node_reaction_moment_1(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / 2
        if axis == "Y":
            assert self.N1.Rmz == pytest.approx(expected)
        else:
            assert self.N1.Rmy == pytest.approx(-expected)
