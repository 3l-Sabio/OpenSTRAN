import pytest

from math import sqrt

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [10., 15.])
@pytest.mark.parametrize("s", ["W12X14", "HSS6X6X3/16"])
@pytest.mark.parametrize("P", [1., 2.5, 5., 7.5])
@pytest.mark.parametrize("x", range(0, 100, 5))
class TestSimpleBeam:
    @pytest.fixture(autouse=True)
    def setup_model(self, L: float, s: str, P: float, x: float):
        # run before every test method for the current parameter set
        self.test_model = Model()
        self.shape = Shape(s)
        self.E = 29000
        self.G = 12000

        self.N1 = self.test_model.nodes.add_node(0, 0, 0)
        self.N2 = self.test_model.nodes.add_node(L, 0, 0)

        self.N1.restraint = [1, 1, 1, 0, 0, 0]
        self.N2.restraint = [1, 1, 1, 0, 0, 0]

        self.M1 = self.test_model.members.add_member(
            self.N1, self.N2, shape=self.shape, E=self.E, G=self.G
        )
        self.M1.add_point_load(-P, "Y", x)

        self.test_model.solve()
        self.test_model.maxMbrForces()
        self.test_model.maxReactions()
        self.test_model.max_deflection()

    def test_max_moment(self, P: float, L: float, x: float):
        l = L * 12
        a = l*x/100
        b = l - a
        assert self.test_model.Mzz_max == pytest.approx(P * a * b / l)

    def test_max_shear(self, P: float, L: float, x: float):
        l = L * 12
        a = l*x/100
        b = l - a
        assert self.test_model.Vy_max == pytest.approx(max(P*a/l, P*b/l))

    def test_max_reaction(self, P: float, L: float, x: float):
        l = L * 12
        a = l*x/100
        b = l - a
        assert self.test_model.Ry_max == pytest.approx(max(P*a/l, P*b/l))

    def test_deflection(self, L: float, x: float, P: float):
        l = L * 12
        a = l*x/100
        b = l - a
        I = self.shape.Ix
        if a < b:
            assert self.test_model.Uy_max == pytest.approx(
                P*a*b*(b+2*a)*sqrt(3*b*(b+2*a))/(27*self.E*I*l), rel=1e-3)
        else:
            assert self.test_model.Uy_max == pytest.approx(
                P*a*b*(a+2*b)*sqrt(3*a*(a+2*b))/(27*self.E*I*l), rel=1e-3)

    def test_node_reaction_1(self, P: float, L: float, x: float):
        l = L * 12
        a = l*x/100
        b = l - a
        assert self.N1.Ry == pytest.approx(P*b/l)

    def test_node_reaction_2(self, P: float, L: float, x: float):
        l = L * 12
        a = l*x/100
        assert self.N2.Ry == pytest.approx(P*a/l)
