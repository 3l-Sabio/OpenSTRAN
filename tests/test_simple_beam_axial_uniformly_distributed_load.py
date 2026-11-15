import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


@pytest.mark.parametrize("L", [4.75, 7.25, 10., 17.33, 26.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16", "L6X6X1/2"], scope="class")
@pytest.mark.parametrize("w", [1.25, 2.6, 5.3], scope="class")
@pytest.mark.parametrize("direction", ["X", "x"], scope="class")
class TestSimpleBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, direction: str):
        cls.test_model = Model()
        cls.shape = Shape(s)
        cls.E = 29000
        cls.G = 12000

        cls.N1 = cls.test_model.nodes.add_node(0, 0, 0)
        cls.N2 = cls.test_model.nodes.add_node(L, 0, 0)

        cls.N1.restraint = [1, 1, 1, 1, 0, 0]  # pinned
        cls.N2.restraint = [0, 1, 1, 1, 0, 0]  # roller, free along X

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )

        cls.M1.add_distributed_load(w, w, direction, 0, 100)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_axial(self, w: float, L: float):
        expected = w * L
        assert self.test_model.axial_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float):
        expected = w * L
        assert self.test_model.Rx_max == pytest.approx(expected)

    def test_max_deflection(self, w: float, L: float):
        l = L * 12  # ft -> in
        w = w / 12  # klf -> kli
        # elongation at the roller end
        expected = w * l ** 2 / (2 * self.E * self.shape.A)
        assert self.test_model.Ux_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float):
        expected = -w * L  # the support pushes back against the load
        assert self.N1.Rx == pytest.approx(expected)

    def test_node_reaction_2(self):
        # the roller cannot resist load along the member
        assert self.N2.Rx == pytest.approx(0, abs=1e-6)

    def test_no_bending(self):
        # an axial load on a straight member causes no shear or moment
        assert self.test_model.Vy_max == pytest.approx(0, abs=1e-6)
        assert self.test_model.Mzz_max == pytest.approx(0, abs=1e-6)
