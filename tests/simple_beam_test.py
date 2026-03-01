import pytest

from OpenSTRAN.Model import Model
from OpenSTRAN.Database.Shape import Shape


# instantiate a test model; load and define section and material properties
test_model = Model()
s = Shape("W12X14")
E = 29000
G = 12000
# define a node at the origin and "L" feet from the origin
L = 10
N1 = test_model.nodes.add_node(0, 0, 0)
N2 = test_model.nodes.add_node(L, 0, 0)
# restrain the nodes with simple pins
N1.restraint = [1, 1, 1, 0, 0, 0]
N2.restraint = [1, 1, 1, 0, 0, 0]
# define a member and add a distributed load to the member
M1 = test_model.members.add_member(N1, N2, shape=s, E=E, G=G)
# add a point load to the model
P = 10
M1.add_point_load(-P, 'Y', 50)
# solve the test model and perform post processing of member forces
test_model.solve()
test_model.maxMbrForces()
test_model.maxReactions()
test_model.max_deflection()


def test_max_moment():
    assert test_model.Mzz_max == pytest.approx(P*L*12/4)


def test_max_shear():
    assert test_model.Vy_max == pytest.approx(P/2)


def test_max_reaction():
    assert test_model.Ry_max == pytest.approx(P/2)


def test_deflection():
    assert test_model.Uy_max == pytest.approx(P*(L*12)**3/(48*E*s.Ix))


def test_node_reaction_1():
    assert N1.Ry == pytest.approx(P/2)


def test_node_reaction_2():
    assert N2.Ry == pytest.approx(P/2)
