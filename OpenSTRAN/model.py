import numpy as np

from .Nodes import Nodes
from .Members import Members
from .Solver import Solver


class Model():
    """
    3D space frame structural model.

    This class represents a three-dimensional space frame for finite element analysis.
    The model neglects deformations due to transverse shear stresses and torsional warping,
    operating under the assumption that such effects are negligible in typical civil
    engineering applications.

    :param plane: Constrains the model to a two-dimensional plane. Valid values are 'xy',
        'yz', or 'xz'. If None, the model is fully three-dimensional.
    :type plane: str | None
    :ivar nodes: Collection of nodes in the structure
    :type nodes: Nodes
    :ivar members: Collection of members (elements) in the structure
    :type members: Members
    :ivar solver: Solver instance for performing structural analysis
    :type solver: Solver

    :Example:

        >>> import OpenSTRAN
        >>> frame_2d = OpenSTRAN.Model(plane='xy')
        >>> frame_3d = OpenSTRAN.Model()
    """

    def __init__(self, plane: str | None = None) -> None:
        """
        Initialize a structural model.

        :param plane: Plane constraint for 2D models ('xy', 'yz', or 'xz').
            Defaults to None for 3D models.
        :type plane: str | None
        """
        self.nodes = Nodes(plane)
        self.members = Members(self.nodes)
        self.solver = Solver()

    def solve(self) -> None:
        """Solve the structural system and compute reactions and member forces.

        This method performs a complete finite element analysis including:
        
        - Assembly and solution of the global stiffness system
        - Calculation of nodal reactions at restrained DOFs
        - Determination of member forces and local extrema

        :returns: None
        :rtype: None
        """
        self.solver.solve(self.nodes, self.members)
        self.maxReactions()
        self.maxMbrForces()

    def maxReactions(self) -> None:
        """Calculate maximum reaction forces and moments at restrained nodes.

        Computes the maximum absolute values of reaction forces and moments
        across all support nodes in the structure.

        :returns: None
        :rtype: None
        
        Sets the following instance attributes:
        
        - Rx_max: Maximum X-direction reaction force
        - Ry_max: Maximum Y-direction reaction force
        - Rz_max: Maximum Z-direction reaction force
        - Rmx_max: Maximum X-direction reaction moment
        - Rmy_max: Maximum Y-direction reaction moment
        - Rmz_max: Maximum Z-direction reaction moment
        """
        Rx: list[float] = []
        Ry: list[float] = []
        Rz: list[float] = []
        Rmx: list[float] = []
        Rmy: list[float] = []
        Rmz: list[float] = []

        for node in self.nodes.nodes.values():
            if node.mesh_node != False:
                Rx.append(node.Rx)
                Ry.append(node.Ry)
                Rz.append(node.Rz)
                Rmx.append(node.Rmx)
                Rmy.append(node.Rmy)
                Rmz.append(node.Rmz)

        self.Rx_max = abs(max(Rx, key=lambda x: abs(x)))
        self.Ry_max = abs(max(Ry, key=lambda x: abs(x)))
        self.Rz_max = abs(max(Rz, key=lambda x: abs(x)))
        self.Rmx_max = abs(max(Rmx, key=lambda x: abs(x)))
        self.Rmy_max = abs(max(Rmy, key=lambda x: abs(x)))
        self.Rmz_max = abs(max(Rmz, key=lambda x: abs(x)))

    def maxMbrForces(self) -> None:
        """Calculate maximum member forces and identify local extrema.

        Computes the maximum values for all member internal forces (axial, shear, torsion,
        and bending moments) and identifies their local maxima and minima distributions
        along members.

        :returns: None
        :rtype: None
        
        Sets the following instance attributes:
        
        - axial_max, axial_maxima, axial_minima: Axial force results
        - torque_max, torque_maxima, torque_minima: Torsional moment results
        - Vy_max, Vy_maxima, Vy_minima: Y-direction shear force results
        - Vz_max, Vz_maxima, Vz_minima: Z-direction shear force results
        - Mzz_max, Mzz_maxima, Mzz_minima: Major axis bending moment results
        - Myy_max, Myy_maxima, Myy_minima: Minor axis bending moment results
        """
        axial: list[float] = []
        torque: list[float] = []
        Vy: list[float] = []
        Vz: list[float] = []
        Mzz: list[float] = []
        Myy: list[float] = []

        for mbr in self.members.members.values():
            for submbr in mbr.submembers.values():
                axial.append(submbr.results['axial'][0])
                axial.append(submbr.results['axial'][1]*-1)
                torque.append(submbr.results['torsional moments'][0])
                torque.append(submbr.results['torsional moments'][1]*-1)
                Vy.append(submbr.results['shear'][0])
                Vy.append(submbr.results['shear'][1]*-1)
                Vz.append(submbr.results['transverse shear'][0])
                Vz.append(submbr.results['transverse shear'][1]*-1)
                Mzz.append(submbr.results['major axis moments'][0])
                Mzz.append(submbr.results['major axis moments'][1]*-1)
                Myy.append(submbr.results['minor axis moments'][0])
                Myy.append(submbr.results['minor axis moments'][1]*-1)

        self.axial_max = abs(max(axial, key=lambda x: abs(x)))
        self.axial_maxima = self.localMaxima(axial)
        self.axial_minima = self.localMinima(axial)

        self.torque_max = abs(max(torque, key=lambda x: abs(x)))
        self.torque_maxima = self.localMaxima(torque)
        self.torque_minima = self.localMinima(torque)

        self.Vy_max = abs(max(Vy, key=lambda x: abs(x)))
        self.Vy_maxima = self.localMaxima(Vy)
        self.Vy_minima = self.localMinima(Vy)

        self.Vz_max = abs(max(Vz, key=lambda x: abs(x)))
        self.Vz_maxima = self.localMaxima(Vz)
        self.Vz_minima = self.localMinima(Vz)

        self.Mzz_max = abs(max(Mzz, key=lambda x: abs(x)))
        self.Mzz_maxima = self.localMaxima(Mzz)
        self.Mzz_minima = self.localMinima(Mzz)

        self.Myy_max = abs(max(Myy, key=lambda x: abs(x)))
        self.Myy_maxima = self.localMaxima(Myy)
        self.Myy_minima = self.localMinima(Myy)

    def localMaxima(self, forces: list[float]) -> list[bool]:
        """Identify local maxima in a force distribution.

        Determines which points in the force distribution represent local maxima
        by comparing adjacent values, accounting for numerical precision with
        near-equal comparisons.

        :param forces: List of force values along a member or structure
        :type forces: list[float]
        :returns: Boolean list indicating local maxima positions
        :rtype: list[bool]
        """
        maxima = [False for _ in forces]
        length = len(forces)-1
        for i, force in enumerate(forces):
            if i == 0:
                if force > 0:
                    maxima[i] = True
            if i % 2 == 0 or i == 1:
                continue
            elif i == length:
                if force > 0:
                    maxima[i] = True
            else:
                if forces[i-2] > force:
                    continue
                if np.isclose(forces[i-2], force) and np.isclose(forces[i+2], force):
                    continue
                if np.isclose(forces[i-2], force) and forces[i+2] < force:
                    maxima[i] = True
                    continue
                if forces[i-2] < force and forces[i+2] < force:
                    maxima[i] = True
                    continue
                if forces[i-2] < force and np.isclose(forces[i+2], force):
                    maxima[i] = True
                    continue
        return (maxima)

    def localMinima(self, forces: list[float]) -> list[bool]:
        """Identify local minima in a force distribution.

        Determines which points in the force distribution represent local minima
        by comparing adjacent values, accounting for numerical precision with
        near-equal comparisons.

        :param forces: List of force values along a member or structure
        :type forces: list[float]
        :returns: Boolean list indicating local minima positions
        :rtype: list[bool]
        """
        minima = [False for _ in forces]
        length = len(forces)-1
        for i, force in enumerate(forces):
            if i == 0:
                if force < 0:
                    minima[i] = True
            if i % 2 == 0 or i == 1:
                continue
            elif i == length:
                if force < 0:
                    minima[i] = True
            else:
                if forces[i-2] < force:
                    continue
                if np.isclose(forces[i-2], force) and np.isclose(forces[i+2], force):
                    continue
                if np.isclose(forces[i-2], force) and forces[i+2] > force:
                    minima[i] = True
                    continue
                if forces[i-2] > force and np.isclose(forces[i+2], force):
                    minima[i] = True
                    continue
                if forces[i-2] > force and forces[i+2] > force:
                    minima[i] = True
                    continue
        return (minima)

    def reactions(self) -> None:
        """Print nodal reactions to console.

        Displays all reaction forces (Rx, Ry, Rz) and reaction moments (Mx, My, Mz)
        at all restrained support nodes in a formatted table.

        :returns: None
        :rtype: None
        """
        print('Nodal Reactions')
        for node in self.nodes.nodes.values():
            if node.mesh_node != True:
                print(f'\tNode {node.node_ID}:')
                print(f'\t\tRx = {node.Rx:.2f} kips')
                print(f'\t\tRy = {node.Ry:.2f} kips')
                print(f'\t\tRz = {node.Rz:.2f} kips')
                print(f'\t\tMx = {node.Mx:.2f} kip-ft')
                print(f'\t\tMy = {node.My:.2f} kip-ft')
                print(f'\t\tMz = {node.Mz:.2f} kip-ft')
