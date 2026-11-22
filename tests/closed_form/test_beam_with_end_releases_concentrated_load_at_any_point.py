import pytest

from math import sqrt

from OpenSTRAN import Model
from OpenSTRAN import Shape


@pytest.mark.parametrize("L", [120., 180.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("P", [7.5], scope="class")
@pytest.mark.parametrize("x", range(0, 101, 10), scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestBeamWithEndReleases:
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

        # release bending about both local axes at each end of the member
        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G,
            i_release=[0, 0, 0, 0, 1, 1], j_release=[0, 0, 0, 0, 1, 1]
        )
        cls.M1.add_point_load(-P, axis, x)

        cls.results = cls.test_model.solve()

    def test_max_moment(self, P: float, L: float, x: float, axis: str):
        a = L*x/100
        b = L - a
        if axis == "Y":
            assert self.results.Mzz_max == pytest.approx(P * a * b / L)
        else:
            assert self.results.Myy_max == pytest.approx(P * a * b / L)

    def test_max_shear(self, P: float, L: float, x: float, axis: str):
        a = L*x/100
        b = L - a
        expected = 0.0 if a == 0 or b == 0 else max(P*a/L, P*b/L)
        if axis == "Y":
            assert self.results.Vy_max == pytest.approx(expected)
        else:
            assert self.results.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, P: float, L: float, x: float, axis: str):
        a = L*x/100
        b = L - a
        if axis == "Y":
            assert self.results.Ry_max == pytest.approx(max(P*a/L, P*b/L))
        else:
            assert self.results.Rz_max == pytest.approx(max(P*a/L, P*b/L))

    def test_deflection(self, L: float, x: float, P: float, axis: str):
        a = L*x/100
        b = L - a
        if axis == "Y":
            i = self.shape.Ix
            u = self.results.Uy_max
        else:
            i = self.shape.Iy
            u = self.results.Uz_max
        if a < b:
            assert u == pytest.approx(
                P*a*b*(b+2*a)*sqrt(3*b*(b+2*a))/(27*self.E*i*L), rel=1e-3)
        else:
            assert u == pytest.approx(
                P*a*b*(a+2*b)*sqrt(3*a*(a+2*b))/(27*self.E*i*L), rel=1e-3)

    def test_node_reaction_1(self, P: float, L: float, x: float, axis: str):
        a = L*x/100
        b = L - a
        if axis == "Y":
            assert self.results.node(self.N1).Ry == pytest.approx(
                P*b/L, abs=1e-6)
        else:
            assert self.results.node(self.N1).Rz == pytest.approx(
                P*b/L, abs=1e-6)

    def test_node_reaction_2(self, P: float, L: float, x: float, axis: str):
        a = L*x/100
        if axis == "Y":
            assert self.results.node(self.N2).Ry == pytest.approx(
                P*a/L, abs=1e-6)
        else:
            assert self.results.node(self.N2).Rz == pytest.approx(
                P*a/L, abs=1e-6)

    def test_node_reaction_moment_1(self, axis: str):
        # the released end passes no moment to the support
        if axis == "Y":
            assert self.results.node(self.N1).Rmz == pytest.approx(0, abs=1e-6)
        else:
            assert self.results.node(self.N1).Rmy == pytest.approx(0, abs=1e-6)

    def test_node_reaction_moment_2(self, axis: str):
        # the released end passes no moment to the support
        if axis == "Y":
            assert self.results.node(self.N2).Rmz == pytest.approx(0, abs=1e-6)
        else:
            assert self.results.node(self.N2).Rmy == pytest.approx(0, abs=1e-6)
