import pytest

from math import sqrt

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


def reactions(P: float, l: float, x: float) -> tuple[float, float, float, float]:
    """Closed-form results for a propped cantilever under a concentrated load.

    P is the load,
    l is the span, and
    x is the load location as a percentage of the span from the fixed end.

    Returns the reaction at the fixed end, the reaction at the supported end,
    the moment at the fixed end and the moment under the load.
    """
    b = l * x / 100          # fixed end to load
    a = l - b                # load to supported end
    r_fixed = P * a * (3 * l**2 - a**2) / (2 * l**3)
    r_supported = P * b**2 * (a + 2 * l) / (2 * l**3)
    m_fixed = P * a * b * (a + l) / (2 * l**2)
    m_load = r_supported * a
    return r_fixed, r_supported, m_fixed, m_load


@pytest.mark.parametrize("L", [120., 180.], scope="class")
@pytest.mark.parametrize("s", ["W12X14", "HSS6X4X3/16"], scope="class")
@pytest.mark.parametrize("P", [7.5], scope="class")
@pytest.mark.parametrize("x", range(0, 101, 10), scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestBeamFixedAtOneEndSupportedAtOther:
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
        cls.N2.restraint = [0, 1, 1, 0, 0, 0]  # roller

        cls.M1 = cls.test_model.members.add_member(
            cls.N1, cls.N2, shape=cls.shape, E=cls.E, G=cls.G
        )
        cls.M1.add_point_load(-P, axis, x)

        cls.test_model.solve()
        cls.test_model.max_deflection()

    def test_max_moment(self, P: float, L: float, x: float, axis: str):
        _, _, m_fixed, m_load = reactions(P, L, x)
        expected = max(m_fixed, m_load)
        if axis == "Y":
            assert self.test_model.Mzz_max == pytest.approx(expected, abs=1e-6)
        else:
            assert self.test_model.Myy_max == pytest.approx(expected, abs=1e-6)

    def test_max_shear(self, P: float, L: float, x: float, axis: str):
        r_fixed, r_supported, _, _ = reactions(P, L, x)
        expected = 0.0 if x == 0 or x == 100 else max(r_fixed, r_supported)
        if axis == "Y":
            assert self.test_model.Vy_max == pytest.approx(expected)
        else:
            assert self.test_model.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, P: float, L: float, x: float, axis: str):
        r_fixed, r_supported, _, _ = reactions(P, L, x)
        expected = max(r_fixed, r_supported)
        if axis == "Y":
            assert self.test_model.Ry_max == pytest.approx(expected)
        else:
            assert self.test_model.Rz_max == pytest.approx(expected)

    def test_deflection(self, L: float, x: float, P: float, axis: str):
        b = L*x/100   # fixed end to load
        a = L - b     # load to supported end
        if axis == "Y":
            i = self.shape.Ix
            u = self.test_model.Uy_max
        else:
            i = self.shape.Iy
            u = self.test_model.Uz_max
        if a < (sqrt(2) - 1) * L:
            # max deflection lies between the load and the fixed end
            assert u == pytest.approx(
                P*a*(L**2-a**2)**3/(3*self.E*i*(3*L**2-a**2)**2), rel=1e-3)
        else:
            # max deflection lies between the supported end and the load
            assert u == pytest.approx(
                P*a*b**2/(6*self.E*i)*sqrt(a/(2*L+a)), rel=1e-3)

    def test_node_reaction_1(self, P: float, L: float, x: float, axis: str):
        r_fixed, _, _, _ = reactions(P, L, x)
        if axis == "Y":
            assert self.N1.Ry == pytest.approx(r_fixed, abs=1e-6)
        else:
            assert self.N1.Rz == pytest.approx(r_fixed, abs=1e-6)

    def test_node_reaction_2(self, P: float, L: float, x: float, axis: str):
        _, r_supported, _, _ = reactions(P, L, x)
        if axis == "Y":
            assert self.N2.Ry == pytest.approx(r_supported, abs=1e-6)
        else:
            assert self.N2.Rz == pytest.approx(r_supported, abs=1e-6)

    def test_node_reaction_moment_1(self, P: float, L: float, x: float, axis: str):
        _, _, m_fixed, _ = reactions(P, L, x)
        if axis == "Y":
            assert self.N1.Rmz == pytest.approx(m_fixed, abs=1e-6)
        else:
            assert self.N1.Rmy == pytest.approx(-m_fixed, abs=1e-6)

    def test_node_reaction_moment_2(self, axis: str):
        if axis == "Y":
            assert self.N2.Rmz == pytest.approx(0, abs=1e-6)
        else:
            assert self.N2.Rmy == pytest.approx(0, abs=1e-6)
