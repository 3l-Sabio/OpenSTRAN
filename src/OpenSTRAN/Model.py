import numpy as np

from .Nodes import Nodes
from .Members import Members
from .Results import FORCE_KEYS, Results
from .Solver import Solver


class Model():
    """3D space frame structural model.

    This class represents a three-dimensional space frame for finite element
    analysis. The model neglects deformations due to transverse shear stresses and
    torsional warping, operating under the assumption that such effects are
    negligible in typical civil engineering applications.

    Parameters:
        plane (str | None): Constrains the model to a two-dimensional plane. Valid
            values are 'xy', 'yz', or 'zx'. If None, the model is fully
            three-dimensional.
        nodes (Nodes): Collection of nodes in the structure.
        members (Members): Collection of members (elements) in the structure.
        solver (Solver): Solver instance for performing structural analysis.
        results (Results | None): Results of the last analysis, or None
            before the first.

    Example:

        >>> import OpenSTRAN
        >>> frame_2d = OpenSTRAN.Model(plane='xy')
        >>> frame_3d = OpenSTRAN.Model()
    """

    def __init__(self, plane: str | None = None) -> None:
        """Initialize a structural model.

        Args:
            plane (str | None, optional): Plane constraint for 2D models ('xy', 'yz',
                or 'zx'). Defaults to None for 3D models.
        """
        self.nodes = Nodes(plane)
        self.members = Members(self.nodes)
        self.solver = Solver()
        self.results: Results | None = None

    def solve(
        self,
        second_order: bool = False,
        tolerance: float = 1e-8,
        max_iterations: int = 50
    ) -> Results:
        """Solve the structural system and compute reactions and member forces.

        This method performs a complete finite element analysis including:

        * Assembly and solution of the global stiffness system
        * Calculation of nodal reactions at restrained DOFs
        * Determination of member forces and local extrema

        With ``second_order=True`` the analysis includes the effect of axial
        forces on stiffness (P-Delta). Starting from the first-order
        solution, it iterates on the axial forces (a fixed-point iteration),
        using the tangent stiffness (elastic plus geometric) of the current
        axial forces until the unbalanced load is below ``tolerance`` times
        the applied loads. Equilibrium is formulated on the undeformed
        geometry. The bowing of a member between its ends (P-delta) is
        captured only if the member is meshed into several submembers. If
        the analysis fails or is interrupted, the model is left holding the
        first-order solution.

        Args:
            second_order (bool, optional): Run a second-order (P-Delta)
                analysis. Defaults to False.
            tolerance (float, optional): Convergence tolerance of a
                second-order analysis: the largest norm of the unbalanced
                load, relative to the norm of the applied loads. Defaults to
                1e-8.
            max_iterations (int, optional): Maximum number of iterations of a
                second-order analysis. Defaults to 50.

        Returns:
            Results: The results of the analysis, also kept as ``results``.

        Raises:
            RuntimeError: If a second-order analysis does not converge, or the
                loads are most likely at or above the second-order limit load.
            ValueError: If a second-order analysis finds that the elastic
                stiffness is singular.
        """
        self._prepare()
        try:
            self.solver.solve(
                self.nodes, self.members, second_order=second_order,
                tolerance=tolerance, max_iterations=max_iterations)
        finally:
            # A failed second-order analysis leaves the first-order solution;
            # a failed first-order analysis leaves the previous results.
            self._publish()
        assert self.results is not None
        return self.results

    def critical_load_factor(self) -> float:
        """Elastic critical load factor of the applied loads.

        Returns the smallest positive factor lambda for which lambda times the
        applied loads is an elastic critical (buckling) load, from the
        eigenproblem ``[Ke + lambda Kg] {d} = 0`` with the geometric
        stiffness Kg formed from the first-order axial forces. The model is
        left holding the first-order solution under the applied loads.

        Returns:
            float: The elastic critical load factor.

        Raises:
            ValueError: If the applied loads put no member in compression, if
                every member in compression is restrained against bending and
                twisting, or if the elastic stiffness is singular.
        """
        self._prepare()
        try:
            return self.solver.critical_load_factor(self.nodes, self.members)
        finally:
            # The model holds the first-order solution, unless that failed.
            self._publish()

    def _publish(self) -> None:
        """Keep the solver's results and copy them onto the old attributes.

        Temporary, while the node and model result attributes are replaced
        by ``results``: copies each node's displacements and reactions onto
        the node, and the maxima onto the model. Does nothing if the solver
        holds no results.
        """
        results = self.solver.results
        if results is None:
            return
        self.results = results
        for node in self.nodes.nodes.values():
            r = results.node(node)
            node.Ux, node.Uy, node.Uz = r.Ux, r.Uy, r.Uz
            node.phi_x, node.phi_y, node.phi_z = r.phi_x, r.phi_y, r.phi_z
            node.Rx, node.Ry, node.Rz = r.Rx, r.Ry, r.Rz
            node.Rmx, node.Rmy, node.Rmz = r.Rmx, r.Rmy, r.Rmz
        self.maxReactions()
        self.maxMbrForces()

    def _prepare(self) -> None:
        """Mesh each member and apply its deferred loads.

        Meshing is deferred to this point so that nodes created by loads are
        included in the member mesh.
        """
        for member in self.members.members.values():
            member.prepare()

    def maxReactions(self) -> None:
        """Calculate maximum reaction forces and moments at restrained nodes.

        Computes the maximum absolute values of reaction forces and moments
        across all support nodes in the structure.

        Sets the following instance attributes:

        * Rx_max: Maximum X-direction reaction force
        * Ry_max: Maximum Y-direction reaction force
        * Rz_max: Maximum Z-direction reaction force
        * Rmx_max: Maximum X-direction reaction moment
        * Rmy_max: Maximum Y-direction reaction moment
        * Rmz_max: Maximum Z-direction reaction moment
        """
        assert self.results is not None
        self.Rx_max = self.results.Rx_max
        self.Ry_max = self.results.Ry_max
        self.Rz_max = self.results.Rz_max
        self.Rmx_max = self.results.Rmx_max
        self.Rmy_max = self.results.Rmy_max
        self.Rmz_max = self.results.Rmz_max

    def maxMbrForces(self) -> None:
        """Calculate maximum member forces and identify local extrema.

        Computes the maximum values for all member internal forces (axial, shear,
        torsion, and bending moments) and identifies their local maxima and minima
        distributions along members.

        Sets the following instance attributes:

        * axial_max, axial_maxima, axial_minima: Axial force results
        * torque_max, torque_maxima, torque_minima: Torsional moment results
        * Vy_max, Vy_maxima, Vy_minima: Y-direction shear force results
        * Vz_max, Vz_maxima, Vz_minima: Z-direction shear force results
        * Mzz_max, Mzz_maxima, Mzz_minima: Major axis bending moment results
        * Myy_max, Myy_maxima, Myy_minima: Minor axis bending moment results
        """
        assert self.results is not None
        results = self.results

        # Each submember's end forces, with the j end's sign flipped so that
        # both ends follow the same internal force sign convention.
        ends: dict[str, list[float]] = {key: [] for key in FORCE_KEYS}
        for mbr in results.members:
            for sub in mbr.submembers:
                for key, values in ends.items():
                    values.append(sub.forces[key][0])
                    values.append(-sub.forces[key][1])

        self.axial_maxima = self.localMaxima(ends['axial'])
        self.axial_minima = self.localMinima(ends['axial'])
        self.torque_maxima = self.localMaxima(ends['torsional moments'])
        self.torque_minima = self.localMinima(ends['torsional moments'])
        self.Vy_maxima = self.localMaxima(ends['shear'])
        self.Vy_minima = self.localMinima(ends['shear'])
        self.Vz_maxima = self.localMaxima(ends['transverse shear'])
        self.Vz_minima = self.localMinima(ends['transverse shear'])
        self.Mzz_maxima = self.localMaxima(ends['major axis moments'])
        self.Mzz_minima = self.localMinima(ends['major axis moments'])
        self.Myy_maxima = self.localMaxima(ends['minor axis moments'])
        self.Myy_minima = self.localMinima(ends['minor axis moments'])

        # The peak magnitudes include the peaks between mesh nodes (e.g.
        # under distributed loads), not only the values at the nodes.
        self.axial_max = results.axial_max
        self.torque_max = results.torque_max
        self.Vy_max = results.Vy_max
        self.Vz_max = results.Vz_max
        self.Mzz_max = results.Mzz_max
        self.Myy_max = results.Myy_max

    def localMaxima(self, forces: list[float]) -> list[bool]:
        """Identify local maxima in a force distribution.

        Determines which points in the force distribution represent local maxima
        by comparing adjacent values, accounting for numerical precision with
        near-equal comparisons.

        Args:
            forces (list[float]): List of force values along a member or structure.

        Returns:
            list[bool]: Boolean list indicating local maxima positions.
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

        Args:
            forces (list[float]): List of force values along a member or structure.

        Returns:
            list[bool]: Boolean list indicating local minima positions.
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
        """
        def tidy(value: float) -> float:
            # Round first so a tiny negative value does not print as "-0.00".
            return round(value, 2) + 0.0

        print('Nodal Reactions')
        for node in self.nodes.nodes.values():
            if node.mesh_node is not True:
                print(f'\tNode {node.node_ID}:')
                print(f'\t\tRx = {tidy(node.Rx):.2f} kips')
                print(f'\t\tRy = {tidy(node.Ry):.2f} kips')
                print(f'\t\tRz = {tidy(node.Rz):.2f} kips')
                print(f'\t\tMx = {tidy(node.Rmx):.2f} kip-in')
                print(f'\t\tMy = {tidy(node.Rmy):.2f} kip-in')
                print(f'\t\tMz = {tidy(node.Rmz):.2f} kip-in')

    def max_deflection(self) -> None:
        """Copy the maximum translations of the last results onto the model
        as ``Ux_max``, ``Uy_max`` and ``Uz_max``."""
        assert self.results is not None
        self.Ux_max = self.results.Ux_max
        self.Uy_max = self.results.Uy_max
        self.Uz_max = self.results.Uz_max
