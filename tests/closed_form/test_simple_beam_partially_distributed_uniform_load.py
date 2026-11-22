import numpy as np
import pytest

from OpenSTRAN import Model
from OpenSTRAN import Shape

LOAD_LENGTHS = [10, 20, 30, 50, 100]   # load length, % of span
STEP = 1                                # how far the load moves each step, % of span

MOVING_LOADS = [
    (a, b)
    for b in LOAD_LENGTHS                    # for each load length...
    # ...move it until it reaches the right support
    for a in range(0, 100 - b + 1, STEP)
]


def max_deflection(w: float, L: float, a: float, b: float, E: float, I: float) -> float:
    """Max deflection (in) of a simple beam under a partial uniform load.

    w in kip/in, 
    L in inches, 
    a = load start as % of span, and 
    b = load length as % of span,
    E in ksi, 
    I in in^4.
    """
    a = L * a / 100
    b = L * b / 100
    c = L - a - b
    d = a + b
    R1 = w * b * (2 * c + b) / (2 * L)
    R2 = w * b - R1
    C1 = (R1 * L**3 / 6 - w / 24 * ((b + c)**4 - c**4)) / L

    def y(x: float) -> float:
        return (-R1 * x**3 / 6 + w / 24 * max(x - a, 0)**4
                - w / 24 * max(x - d, 0)**4 + C1 * x) / (E * I)

    # Max deflection is where the slope is zero: left of, under, or right of
    # the load
    candidates: list[float] = []
    x_left = np.sqrt(2 * C1 / R1)
    if x_left <= a:
        candidates.append(x_left)
    for u in np.roots([w / 6, -R1 / 2, -R1 * a, C1 - R1 * a**2 / 2]):
        if abs(u.imag) < 1e-9 and -1e-9 <= u.real <= b + 1e-9:
            candidates.append(a + u.real)
    C1_right = R1 * L**2 / 2 - w / 6 * ((b + c)**3 - c**3) - C1
    x_right = L - np.sqrt(2 * C1_right / R2)
    if x_right >= d:
        candidates.append(x_right)
    return max(y(x) for x in candidates)


@pytest.mark.parametrize("L", [120.], scope="class")
@pytest.mark.parametrize("a, b", MOVING_LOADS, scope="class")
@pytest.mark.parametrize("s", ["W12X14"], scope="class")
@pytest.mark.parametrize("w", [1./12], scope="class")
@pytest.mark.parametrize("axis", ["Y", "Z"], scope="class")
class TestSimpleBeam:
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_model(cls, L: float, s: str, w: float, a: float, b: float, axis: str):
        # run once per parameter set; the test methods share the solved model
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

        cls.M1.add_distributed_load(-w, -w, axis, a, a + b)

        cls.results = cls.test_model.solve()

    def test_max_moment(self, w: float, L: float, a: float, b: float, axis: str):
        a_len = L * a / 100          # in, left support to start of load
        b_len = L * b / 100          # in, loaded length
        c_len = L - a_len - b_len    # in, end of load to right support
        r = w * b_len / (2 * L) * (2 * c_len + b_len)
        expected = r * (a_len + r / (2 * w))
        if axis == "Y":
            assert self.results.Mzz_max == pytest.approx(expected)
        else:
            assert self.results.Myy_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, a: float, b: float, axis: str):
        a_len = L * a / 100          # in, left support to start of load
        b_len = L * b / 100          # in, loaded length
        c_len = L - a_len - b_len    # in, end of load to right support

        if a_len < c_len:
            expected = w * b_len / (2 * L) * (2 * c_len + b_len)
        else:
            expected = w * b_len / (2 * L) * (2 * a_len + b_len)

        if axis == "Y":
            assert self.results.Vy_max == pytest.approx(expected)
        else:
            assert self.results.Vz_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, a: float, b: float, axis: str):
        a_len = L * a / 100          # in, left support to start of load
        b_len = L * b / 100          # in, loaded length
        c_len = L - a_len - b_len    # in, end of load to right support

        if a_len < c_len:
            expected = w * b_len / (2 * L) * (2 * c_len + b_len)
        else:
            expected = w * b_len / (2 * L) * (2 * a_len + b_len)

        if axis == "Y":
            assert self.results.Ry_max == pytest.approx(expected)
        else:
            assert self.results.Rz_max == pytest.approx(expected)

    def test_deflection(self, w: float, L: float, a: float, b: float, axis: str):
        if axis == "Y":
            expected = max_deflection(w, L, a, b, self.E, self.shape.Ix)
            assert self.results.Uy_max == pytest.approx(expected, rel=1e-3)
        else:
            expected = max_deflection(w, L, a, b, self.E, self.shape.Iy)
            assert self.results.Uz_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, a: float, b: float, axis: str):
        a_len = L * a / 100          # in, left support to start of load
        b_len = L * b / 100          # in, loaded length
        c_len = L - a_len - b_len    # in, end of load to right support
        expected = w * b_len / (2 * L) * (2 * c_len + b_len)

        if axis == "Y":
            assert self.results.node(self.N1).Ry == pytest.approx(expected)
        else:
            assert self.results.node(self.N1).Rz == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, a: float, b: float, axis: str):
        a_len = L * a / 100          # in, left support to start of load
        b_len = L * b / 100          # in, loaded length
        expected = w * b_len / (2 * L) * (2 * a_len + b_len)

        if axis == "Y":
            assert self.results.node(self.N2).Ry == pytest.approx(expected)
        else:
            assert self.results.node(self.N2).Rz == pytest.approx(expected)
