import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [120., 180.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("P", [7.5], scope="class")
@pytest.mark.parametrize("x", range(0, 101, 10), scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestCantileverBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, P: float, x: float, axis: str):
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
        cls.M1.add_point_load(-P, axis, x)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, P: float, L: float, x: float, axis: str):
        b = L*x/100
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(P * b, abs=1e-6)
        else:
            assert self.test_model.Myy_max == pytest.approx(P * b, abs=1e-6)

    def test_max_shear(self, P: float, x: float, axis: str):
        expected = 0.0 if x == 0 else P
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, P: float, axis: str):
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(P)
        else:
            assert self.test_model.Rz_max == pytest.approx(P)

    def test_deflection(self, L: float, x: float, P: float, axis: str):
        b = L*x/100
        if axis == "Y":
            i = self.shape.Ix
            u = self.test_model.Uy_max
        else:
            i = self.shape.Iy
            u = self.test_model.Uz_max
        assert u == pytest.approx(P*b**2*(3*L-b)/(6*self.E*i), rel=1e-3)

    def test_node_reaction_1(self, P: float, axis: str):
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(P)
        else:
            assert self.N1.Rz == pytest.approx(P)

    def test_node_reaction_2(self, axis: str):
        # the free end has no support, so it has no reaction
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(0, abs=1e-6)
        else:
            assert self.N2.Rz == pytest.approx(0, abs=1e-6)

    def test_node_reaction_moment_1(self, P: float, L: float, x: float, axis: str):
        b = L*x/100
        if axis == "Y":
            assert self.N1.Rmz == pytest.approx(P * b, abs=1e-6)
        else:
            assert self.N1.Rmy == pytest.approx(-P * b, abs=1e-6)
