import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [10., 15.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("P", [7.5], scope="class")
@pytest.mark.parametrize("x", range(0, 101, 10), scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestBeamFixedAtBothEnds:
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
        cls.N2.restraint = [1, 1, 1, 1, 1, 1]  # fixed

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )
        cls.M1.add_point_load(-P, axis, x)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        expected = max(P*a*b**2/l**2, P*a**2*b/l**2)
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(expected, abs=1e-6)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected, abs=1e-6)

    def test_max_shear(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        r1 = P*b**2*(3*a+b)/l**3
        r2 = P*a**2*(a+3*b)/l**3
        expected = 0.0 if a == 0 or b == 0 else max(r1, r2)
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        r1 = P*b**2*(3*a+b)/l**3
        r2 = P*a**2*(a+3*b)/l**3
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(max(r1, r2))
        else:
            assert self.test_model.Rz_max == pytest.approx(max(r1, r2))

    def test_deflection(self, L: float, x: float, P: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        if axis == "Y":
            i = self.shape.Ix
            u = self.test_model.Uy_max
        else:
            i = self.shape.Iy
            u = self.test_model.Uz_max
        if a < b:
            assert u == pytest.approx(
                2*P*b**3*a**2/(3*self.E*i*(3*b+a)**2), rel=1e-3)
        else:
            assert u == pytest.approx(
                2*P*a**3*b**2/(3*self.E*i*(3*a+b)**2), rel=1e-3)

    def test_node_reaction_1(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        expected = P*b**2*(3*a+b)/l**3
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(expected, abs=1e-6)
        else:
            assert self.N1.Rz == pytest.approx(expected, abs=1e-6)

    def test_node_reaction_2(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        expected = P*a**2*(a+3*b)/l**3
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(expected, abs=1e-6)
        else:
            assert self.N2.Rz == pytest.approx(expected, abs=1e-6)

    def test_node_reaction_moment_1(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        expected = P*a*b**2/l**2
        if axis == "Y":
            assert self.N1.Rmz == pytest.approx(expected, abs=1e-6)
        else:
            assert self.N1.Rmy == pytest.approx(-expected, abs=1e-6)

    def test_node_reaction_moment_2(self, P: float, L: float, x: float, axis: str):
        l = L * 12
        a = l*x/100
        b = l - a
        expected = P*a**2*b/l**2
        if axis == "Y":
            assert self.N2.Rmz == pytest.approx(-expected, abs=1e-6)
        else:
            assert self.N2.Rmy == pytest.approx(expected, abs=1e-6)
