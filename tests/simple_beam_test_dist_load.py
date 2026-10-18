import numpy as np
import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape

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

    w in kip/ft, 
    L in ft, 
    a = load start as % of span, and 
    b = load length as % of span,
    E in ksi, 
    I in in^4.
    """
    w = w / 12
    l = L * 12
    a = l * a / 100
    b = l * b / 100
    c = l - a - b
    d = a + b
    R1 = w * b * (2 * c + b) / (2 * l)
    R2 = w * b - R1
    C1 = (R1 * l**3 / 6 - w / 24 * ((b + c)**4 - c**4)) / l

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
    C1_right = R1 * l**2 / 2 - w / 6 * ((b + c)**3 - c**3) - C1
    x_right = l - np.sqrt(2 * C1_right / R2)
    if x_right >= d:
        candidates.append(x_right)
    return max(y(x) for x in candidates)


@pytest.mark.parametrize("L", [10.])
@pytest.mark.parametrize("a, b", MOVING_LOADS)
@pytest.mark.parametrize("s", ["W12X14"])
@pytest.mark.parametrize("w", [1.])
class TestSimpleBeam:
    @pytest.fixture(autouse=True)
    def setup_model(self, L: float, s: str, w: float, a: float, b: float):
        # run before every test method for the current parameter set
        self.test_model = Model()
        self.shape = Shape(s)
        self.E = 29000
        self.G = 12000

        self.N1 = self.test_model.nodes.add_node(0, 0, 0)
        self.N2 = self.test_model.nodes.add_node(L, 0, 0)

        self.N1.restraint = [1, 1, 1, 1, 0, 0]
        self.N2.restraint = [1, 1, 1, 1, 0, 0]

        self.M1 = self.test_model.members.add_member(
            self.N1, self.N2, shape=self.shape, E=self.E, G=self.G
        )

        self.M1.add_distributed_load(-w, -w, "Y", a, a + b)

        self.test_model.solve()
        self.test_model.maxMbrForces()
        self.test_model.maxReactions()
        self.test_model.max_deflection()

    def test_max_moment(self, w: float, L: float, a: float, b: float):
        a_len = L * a / 100          # ft, left support to start of load
        b_len = L * b / 100          # ft, loaded length
        c_len = L - a_len - b_len    # ft, end of load to right support
        r = w * b_len / (2 * L) * (2 * c_len + b_len)
        expected = r * (a_len + r / (2 * w)) * 12   # kip-ft -> kip-in
        assert self.test_model.Mzz_max == pytest.approx(expected)

    def test_max_shear(self, w: float, L: float, a: float, b: float):
        a_len = L * a / 100          # ft, left support to start of load
        b_len = L * b / 100          # ft, loaded length
        c_len = L - a_len - b_len    # ft, end of load to right support

        if a_len < c_len:
            expected = w * b_len / (2 * L) * (2 * c_len + b_len)
        else:
            expected = w * b_len / (2 * L) * (2 * a_len + b_len)

        assert self.test_model.Vy_max == pytest.approx(expected)

    def test_max_reaction(self, w: float, L: float, a: float, b: float):
        a_len = L * a / 100          # ft, left support to start of load
        b_len = L * b / 100          # ft, loaded length
        c_len = L - a_len - b_len    # ft, end of load to right support

        if a_len < c_len:
            expected = w * b_len / (2 * L) * (2 * c_len + b_len)
        else:
            expected = w * b_len / (2 * L) * (2 * a_len + b_len)

        assert self.test_model.Ry_max == pytest.approx(expected)

    def test_deflection(self, w: float, L: float, a: float, b: float):
        expected = max_deflection(w, L, a, b, self.E, self.shape.Ix)
        assert self.test_model.Uy_max == pytest.approx(expected, rel=1e-3)

    def test_node_reaction_1(self, w: float, L: float, a: float, b: float):
        a_len = L * a / 100          # ft, left support to start of load
        b_len = L * b / 100          # ft, loaded length
        c_len = L - a_len - b_len    # ft, end of load to right support
        expected = w * b_len / (2 * L) * (2 * c_len + b_len)
        assert self.N1.Ry == pytest.approx(expected)

    def test_node_reaction_2(self, w: float, L: float, a: float, b: float):
        a_len = L * a / 100          # ft, left support to start of load
        b_len = L * b / 100          # ft, loaded length
        expected = w * b_len / (2 * L) * (2 * a_len + b_len)
        assert self.N2.Ry == pytest.approx(expected)
