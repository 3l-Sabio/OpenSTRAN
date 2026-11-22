import pytest

from OpenSTRAN import Model
from OpenSTRAN import Shape


# A cantilever with a concentrated moment M applied to the node at its free
# end. The moment is constant along the beam and there is no shear.
#
#   moment         M
#   reaction       A moment of M opposing the applied moment
#   deflection     M * l**2 / (2 * E * I)   (at the free end)
#   rotation       M * l / (E * I)          (at the free end)
@pytest.mark.parametrize("L", [120., 180.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("M", [60., 240.], scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestCantileverBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, M: float, axis: str):
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
        cls.N2.add_load(M, 'moment', axis)

        cls.results = cls.test_model.solve()

    def test_max_moment(self, M: float, axis: str):
        expected = M
        # a moment about global Z bends the beam about its major axis
        if axis == "Z":
            assert self.results.Mzz_max == pytest.approx(expected)
        else:
            assert self.results.Myy_max == pytest.approx(expected)

    def test_max_shear(self):
        assert self.results.Vy_max == pytest.approx(0, abs=1e-6)
        assert self.results.Vz_max == pytest.approx(0, abs=1e-6)

    def test_max_reaction(self):
        assert self.results.Ry_max == pytest.approx(0, abs=1e-6)
        assert self.results.Rz_max == pytest.approx(0, abs=1e-6)

    def test_deflection(self, M: float, L: float, axis: str):
        if axis == "Z":
            expected = M * L ** 2 / (2 * self.E * self.shape.Ix)
            assert self.results.Uy_max == pytest.approx(expected)
        else:
            expected = M * L ** 2 / (2 * self.E * self.shape.Iy)
            assert self.results.Uz_max == pytest.approx(expected)

    def test_rotation(self, M: float, L: float, axis: str):
        if axis == "Z":
            expected = M * L / (self.E * self.shape.Ix)
            assert self.results.node(self.N2).phi_z == pytest.approx(expected)
        else:
            expected = M * L / (self.E * self.shape.Iy)
            assert self.results.node(self.N2).phi_y == pytest.approx(expected)

    def test_node_reaction_moment_1(self, M: float, axis: str):
        expected = -M
        if axis == "Z":
            assert self.results.node(self.N1).Rmz == pytest.approx(expected)
        else:
            assert self.results.node(self.N1).Rmy == pytest.approx(expected)

    def test_node_reaction_moment_2(self, axis: str):
        # the free end has no support, so it has no reaction
        if axis == "Z":
            assert self.results.node(self.N2).Rmz == pytest.approx(0, abs=1e-6)
        else:
            assert self.results.node(self.N2).Rmy == pytest.approx(0, abs=1e-6)
