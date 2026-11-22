from .Loads import Loads
from .Node import PLANE_RESTRAINTS, Node
from .Nodes import Nodes
from .Members import Members
from .Results import Results
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
        loads (Loads): The loads applied to the structure, added with
            ``Node.add_load``, ``Member.add_point_load`` and
            ``Member.add_distributed_load``.
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
        self.loads = Loads()
        self.nodes = Nodes(plane, loads=self.loads)
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
        captured only if the member is meshed into several submembers. An
        analysis that fails or is interrupted raises, and the model keeps
        the results of its previous analysis, if any.

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
        results = self.solver.solve(
            self.nodes, self.members, self.loads,
            second_order=second_order,
            tolerance=tolerance, max_iterations=max_iterations)
        self.results = results
        return results

    def critical_load_factor(self) -> float:
        """Elastic critical load factor of the applied loads.

        Returns the smallest positive factor lambda for which lambda times the
        applied loads is an elastic critical (buckling) load, from the
        eigenproblem ``[Ke + lambda Kg] {d} = 0`` with the geometric
        stiffness Kg formed from the first-order axial forces. The results of
        the model (``results``) are left as they were.

        Returns:
            float: The elastic critical load factor.

        Raises:
            ValueError: If the applied loads put no member in compression, if
                every member in compression is restrained against bending and
                twisting, or if the elastic stiffness is singular.
        """
        self._prepare()
        return self.solver.critical_load_factor(
            self.nodes, self.members, self.loads)

    def _prepare(self) -> None:
        """Mesh each member.

        Meshing is deferred to this point so that nodes created by loads are
        included in the member mesh.
        """
        for member in self.members.members.values():
            member.prepare()

    def _require_results(self) -> Results:
        """The results of the last analysis.

        Raises:
            RuntimeError: If the model has not been solved.
        """
        if self.results is None:
            raise RuntimeError(
                "The model has no results: call solve() first.")
        return self.results

    def reactions(self) -> None:
        """Print the nodal reactions of the last analysis to the console.

        Displays the reaction forces (Rx, Ry, Rz) and reaction moments (Mx,
        My, Mz) of every node the user added, and of every mesh node with a
        support (a restraint other than those that keep the nodes of a
        two-dimensional model in its plane), for example one placed on the
        node a point load created.

        Raises:
            RuntimeError: If the model has not been solved.
        """
        results = self._require_results()

        def tidy(value: float) -> float:
            # Round first so a tiny negative value does not print as "-0.00".
            return round(value, 2) + 0.0

        def supported(node: Node) -> bool:
            in_plane = PLANE_RESTRAINTS.get(
                node.plane or '', (0, 0, 0, 0, 0, 0))
            return any(r and not p for r, p in zip(node.restraint, in_plane))

        print('Nodal Reactions')
        for node in results.nodes:
            if not node.mesh_node or supported(node):
                r = results.node(node)
                print(f'\tNode {node.node_ID}:')
                print(f'\t\tRx = {tidy(r.Rx):.2f} kips')
                print(f'\t\tRy = {tidy(r.Ry):.2f} kips')
                print(f'\t\tRz = {tidy(r.Rz):.2f} kips')
                print(f'\t\tMx = {tidy(r.Rmx):.2f} kip-in')
                print(f'\t\tMy = {tidy(r.Rmy):.2f} kip-in')
                print(f'\t\tMz = {tidy(r.Rmz):.2f} kip-in')
