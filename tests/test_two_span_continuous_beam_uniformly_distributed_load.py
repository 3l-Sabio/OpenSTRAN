import pytest

from math import sqrt

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


# A continuous beam of two equal spans, uniformly loaded on both spans, built
# from one member per span. L is the length of one span.
#
#   end reactions       3 * w * L / 8
#   middle reaction     10 * w * L / 8
#   max shear           5 * w * L / 8   (each side of the middle support)
#   max moment          w * L**2 / 8    (over the middle support)

@pytest.mark.parametrize("L", [87., 120., 207.96], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("w", [1.25/12, 5.3/12], scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
@pytest.mark.parametrize("mesh", [1, 2, 50], scope="class")
class TestTwoSpanContinuousBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, axis: str, mesh: int):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(L, 0, 0)
        cls.N3 = cls.test_model.nodes.add_node(2 * L, 0, 0)

        cls.N1.restraint = [1, 1, 1, 1, 0, 0]  # pinned
        cls.N2.restraint = [0, 1, 1, 0, 0, 0]  # roller
        cls.N3.restraint = [0, 1, 1, 0, 0, 0]  # roller

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G, mesh=mesh
        )
        cls.M2 = cls.test_model.members.add_member(
            cls.N2, cls.N3, shape=cls.shape, E=cls.E, G=cls.G, mesh=mesh
        )

        cls.M1.add_distributed_load(-w, -w, axis, 0, 100)
        cls.M2.add_distributed_load(-w, -w, axis, 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float, axis: str):
        expected = w * L ** 2 / 8
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(expected)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, axis: str):
        expected = 5 * w * L / 8
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, axis: str):
        expected = 10 * w * L / 8
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(expected)
        else:
            assert self.test_model.Rz_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float, axis: str, mesh: int):
        if mesh < 50:
            pytest.skip("deflection is only sampled at the mesh nodes")
        xi = (1 + sqrt(33)) / 16  # location of max deflection, x/L
        c = (xi - 3 * xi**3 + 2 * xi**4) / 48
        if axis == "Y":
            expected = c * w * L ** 4 / (self.E * self.shape.Ix)
            assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = c * w * L ** 4 / (self.E * self.shape.Iy)
            assert self.test_model.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, axis: str):
        expected = 3 * w * L / 8
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(expected)
        else:
            assert self.N1.Rz == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, axis: str):
        expected = 10 * w * L / 8
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(expected)
        else:
            assert self.N2.Rz == pytest.approx(expected)

    def test_node_reaction_3(self, w: float, L: float, axis: str):
        expected = 3 * w * L / 8
        if axis == "Y":
            assert self.N3.Ry == pytest.approx(expected)
        else:
            assert self.N3.Rz == pytest.approx(expected)
