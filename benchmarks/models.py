"""Model builders for the benchmarks.

Every model is built in the library's reference units (inches and kips) and
sets its mesh explicitly, so its size does not change if the default mesh
does.
"""
from dataclasses import dataclass
from typing import Callable

from OpenSTRAN import Model
from OpenSTRAN import Shape

# The section is looked up once, here, so the database query is not part of
# any timing.
SHAPE = Shape("W12X14")
BAY = 240.0      # beam span, in
STORY = 144.0    # column height, in
W = 0.1          # gravity load on every beam, kip/in
LATERAL = 5.0    # lateral load at the top of each frame, kips
FIXED = [1, 1, 1, 1, 1, 1]


@dataclass(frozen=True)
class Case:
    """One benchmark model.

    Parameters:
        name (str): Short identifier used in the benchmark ids.
        description (str): What the model is, for the results table.
        build (Callable[[], Model]): Builds the unsolved model.
        vertical_load (float): Total gravity load on the model in kips, used
            to check that the reactions balance the loads.
        Uy_max (float): Expected maximum vertical deflection in inches.
        Mzz_max (float): Expected maximum major axis moment in kip-inches.
        rounds (int): How many times the solve is timed.

    The expected deflection and moment are checked after every solve
    benchmark. The beam's are the closed-form values ``5wL^4/384EI`` and
    ``wL^2/8``. The frames have no closed form, so theirs are the values the
    dense solver gave at commit dec90cb.
    """
    name: str
    description: str
    build: Callable[[], Model]
    vertical_load: float
    Uy_max: float
    Mzz_max: float
    rounds: int


def beam(mesh: int) -> Model:
    """A simply supported beam under a uniform load."""
    model = Model()
    N1 = model.nodes.add_node(0, 0, 0)
    N2 = model.nodes.add_node(BAY, 0, 0)
    N1.restraint = [1, 1, 1, 1, 0, 0]
    N2.restraint = [1, 1, 1, 1, 0, 0]
    M1 = model.members.add_member(N1, N2, shape=SHAPE, mesh=mesh)
    M1.add_distributed_load(-W, -W, 'Y', 0, 100)
    return model


def frame_2d(bays: int, stories: int, mesh: int) -> Model:
    """A fixed-base plane frame with loaded beams and a lateral load."""
    model = Model(plane='xy')

    grid = [
        [model.nodes.add_node(i*BAY, j*STORY, 0) for i in range(bays + 1)]
        for j in range(stories + 1)
    ]
    for node in grid[0]:
        node.restraint = list(FIXED)

    # columns
    for j in range(stories):
        for i in range(bays + 1):
            model.members.add_member(
                grid[j][i], grid[j + 1][i], shape=SHAPE, mesh=mesh)

    # beams
    for j in range(1, stories + 1):
        for i in range(bays):
            member = model.members.add_member(
                grid[j][i], grid[j][i + 1], shape=SHAPE, mesh=mesh)
            member.add_distributed_load(-W, -W, 'Y', 0, 100)

    grid[stories][0].add_load(LATERAL, 'force', 'X')
    return model


def frame_3d(bays_x: int, bays_z: int, stories: int, mesh: int) -> Model:
    """A fixed-base space frame with loaded beams in both directions."""
    model = Model()

    grid = [
        [
            [model.nodes.add_node(i*BAY, j*STORY, k*BAY)
             for k in range(bays_z + 1)]
            for i in range(bays_x + 1)
        ]
        for j in range(stories + 1)
    ]
    for row in grid[0]:
        for node in row:
            node.restraint = list(FIXED)

    # columns
    for j in range(stories):
        for i in range(bays_x + 1):
            for k in range(bays_z + 1):
                model.members.add_member(
                    grid[j][i][k], grid[j + 1][i][k], shape=SHAPE, mesh=mesh)

    for j in range(1, stories + 1):
        # beams along global X
        for i in range(bays_x):
            for k in range(bays_z + 1):
                member = model.members.add_member(
                    grid[j][i][k], grid[j][i + 1][k], shape=SHAPE, mesh=mesh)
                member.add_distributed_load(-W, -W, 'Y', 0, 100)
        # beams along global Z
        for i in range(bays_x + 1):
            for k in range(bays_z):
                member = model.members.add_member(
                    grid[j][i][k], grid[j][i][k + 1], shape=SHAPE, mesh=mesh)
                member.add_distributed_load(-W, -W, 'Y', 0, 100)

    grid[stories][0][0].add_load(LATERAL, 'force', 'X')
    return model


def beams_in_3d_frame(bays_x: int, bays_z: int, stories: int) -> int:
    """Number of beams in a space frame built by :func:`frame_3d`."""
    return stories*(bays_x*(bays_z + 1) + bays_z*(bays_x + 1))


CASES: list[Case] = [
    Case(
        name="beam",
        description="Simply supported beam, mesh 50",
        build=lambda: beam(mesh=50),
        vertical_load=W*BAY,
        Uy_max=1.681326380,
        Mzz_max=720.0,
        rounds=30,
    ),
    Case(
        name="portal",
        description="Portal frame, mesh 50",
        build=lambda: frame_2d(bays=1, stories=1, mesh=50),
        vertical_load=W*BAY,
        Uy_max=0.6680481400,
        Mzz_max=508.8591319,
        rounds=20,
    ),
    Case(
        name="frame_2d_3x3",
        description="2D frame, 3 bays x 3 stories, mesh 50",
        build=lambda: frame_2d(bays=3, stories=3, mesh=50),
        vertical_load=W*BAY*3*3,
        Uy_max=0.6197677475,
        Mzz_max=611.0439654,
        rounds=3,
    ),
    Case(
        name="frame_2d_10x10",
        description="2D frame, 10 bays x 10 stories, mesh 4",
        build=lambda: frame_2d(bays=10, stories=10, mesh=4),
        vertical_load=W*BAY*10*10,
        Uy_max=1.915629589,
        Mzz_max=595.5957988,
        rounds=3,
    ),
    Case(
        name="frame_3d_2x2x2",
        description="3D frame, 2 x 2 bays x 2 stories, mesh 10",
        build=lambda: frame_3d(bays_x=2, bays_z=2, stories=2, mesh=10),
        vertical_load=W*BAY*beams_in_3d_frame(2, 2, 2),
        Uy_max=0.8381810435,
        Mzz_max=695.5510840,
        rounds=5,
    ),
]

CASES_BY_NAME: dict[str, Case] = {case.name: case for case in CASES}
