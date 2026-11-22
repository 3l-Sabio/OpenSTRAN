from .Loads import Loads, NodalLoad, PointLoad
from .Nodes import Nodes
from .Members import Members
from .Submember import SubMember
from .Results import FORCE_KEYS, MemberResult, Results, SubMemberResult

import numpy as np
from scipy.linalg import solve, cho_factor, cho_solve, eigh, LinAlgError


class Solver():
    """Solver class for structural finite element analysis.

    This class performs finite element analysis on structural models by assembling
    the global stiffness matrix, applying boundary conditions, and solving for nodal
    displacements and member forces.

    Parameters:
        nDoF (int): Total number of degrees of freedom in the structure.
        restrainedDoF (list[int]): List of restrained degrees of freedom indices.
        Kp (numpy.ndarray | None): Primary (elastic) stiffness matrix for the
            structure.
        Kt (numpy.ndarray | None): Tangent stiffness matrix (elastic plus
            geometric) of the last second-order analysis, or None.
        iterations (int): Number of iterations performed by the last
            second-order analysis, including one that failed; 0 for a
            first-order analysis.
        results (Results | None): Results of the last successful solve, or
            None before the first.
        force_vector (numpy.ndarray | None): Global force vector with applied loads.
        global_displacement_vector (numpy.ndarray | None): Global displacement vector at all nodes.
        global_force_vector (numpy.ndarray | None): Global reaction force vector.
    """

    def __init__(self) -> None:
        """Initialize the Solver with empty attributes.

        Sets up the solver with default values for the stiffness matrix,
        degrees of freedom tracking, and solution vectors.
        """
        self.nDoF: int = 0
        self.restrainedDoF: list[int] = []
        self.Kp: np.ndarray | None = None
        self.Kt: np.ndarray | None = None
        self.iterations: int = 0
        self.results: Results | None = None
        self.force_vector: np.ndarray | None = None
        self.global_displacement_vector: np.ndarray | None = None
        self.global_force_vector: np.ndarray | None = None
        # The equivalent nodal actions (local coordinates) and the load
        # intensities (major i, j, minor i, j) of each submember a
        # distributed load lands on, by id, built by _setup at each solve.
        self._span_actions: dict[int, np.ndarray] = {}
        self._span_intensities: dict[int, np.ndarray] = {}
        # The local end displacements and end forces of each submember, and
        # the axial force whose geometric stiffness was included, by id, as
        # the analysis in progress has found them. The model's objects are
        # not changed: a solve that fails leaves them as they were.
        self._end_forces: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._axial: dict[int, float] = {}

    def solve(
        self,
        nodes: Nodes,
        members: Members,
        loads: Loads,
        second_order: bool = False,
        tolerance: float = 1e-8,
        max_iterations: int = 50
    ) -> Results:
        """Solve the structural system for displacements and member forces.

        This method performs a complete finite element analysis including:

        * Assembly of the global stiffness matrix
        * Application of boundary conditions
        * Solution for nodal displacements using matrix reduction
        * Computation of member forces and reactions
        * Removal of equivalent nodal actions (distributed loads)

        A second-order analysis starts from the first-order solution.
        Equilibrium is formulated on the undeformed geometry (a P-Delta
        analysis), and each iteration solves ``[Ke + Kg(N)] {U} = {F}`` with
        the axial forces N of the previous iteration. 

        The second-order analysis uses the load control method of McGuire et al.
        (Equations 12.11 and 12.16, as a single load increment) with the
        geometry held fixed. An analysis that fails or is interrupted raises
        without results and changes neither the model nor ``results``.

        Args:
            nodes (Nodes): Collection of nodes in the structural model.
            members (Members): Collection of members in the structural model.
            loads (Loads): The loads applied to the model.
            second_order (bool, optional): Include the effect of axial forces
                on stiffness. Defaults to False.
            tolerance (float, optional): Convergence tolerance of a
                second-order analysis: the largest norm of the unbalanced
                load, relative to the norm of the applied loads. Defaults to
                1e-8.
            max_iterations (int, optional): Maximum number of iterations of a
                second-order analysis. Defaults to 50.

        Returns:
            Results: The results of the analysis, also kept as ``results``.

        Raises:
            RuntimeError: If a second-order analysis does not converge, or if
                its tangent stiffness stops being positive definite (the loads
                are most likely at or above the second-order limit load).
            ValueError: If a second-order analysis finds that the elastic
                stiffness is singular.
        """
        submembers = self._first_order(nodes, members, loads)
        if second_order:
            self._second_order(nodes, submembers, tolerance, max_iterations)
        results = self._results(nodes, members, second_order)
        self.results = results
        return results

    def critical_load_factor(
        self, nodes: Nodes, members: Members, loads: Loads
    ) -> float:
        """Elastic critical load factor of the applied loads.

        Solves the eigenproblem of McGuire et al., Equation 8.7,
        ``[Ke + lambda Kg] {d} = 0``, in which the geometric stiffness Kg is
        formed from the axial forces of a first-order analysis under the
        applied loads (see ``SubMember.geometric_stiffness``). It changes
        neither the model nor ``results``.

        Args:
            nodes (Nodes): Collection of nodes in the structural model.
            members (Members): Collection of members in the structural model.
            loads (Loads): The loads applied to the model.

        Returns:
            float: The smallest positive factor lambda such that lambda times
            the applied loads is an elastic critical load.

        Raises:
            ValueError: If the applied loads put no member in compression, if
                every member in compression is restrained against bending and
                twisting, or if the elastic stiffness is singular.
        """
        submembers = self._first_order(nodes, members, loads)
        assert self.Kp is not None
        free = self._free_dofs()
        self._check_stiffness(nodes, submembers, self.Kp, free)

        no_critical_load = ValueError(
            "The applied loads have no elastic critical load: they put no "
            "member in compression, or every member in compression is "
            "restrained against bending and twisting.")
        # The axial and shear forces at both ends of each submember.
        scale = max(
            (abs(float(self._end_forces[id(submbr)][1][k]))
             for submbr in submembers
             for k in (0, 1, 2, 6, 7, 8)),
            default=0.0)
        geometric: list[tuple[SubMember, np.ndarray]] = []
        compression = False
        for submbr in submembers:
            Fx2 = float(self._end_forces[id(submbr)][1][6])
            if abs(Fx2) <= 1e-9*scale:
                Fx2 = 0.0
            compression = compression or Fx2 < 0
            geometric.append((submbr, submbr.geometric_stiffness(Fx2)))
        # Without compression every eigenvalue is zero or negative, but
        # rounding can make the largest one slightly positive, which would
        # give a meaningless factor of the order of 1e16.
        if not compression:
            raise no_critical_load
        Kgs = self._assemble(geometric)[np.ix_(free, free)]
        Ks = self.Kp[np.ix_(free, free)]

        # Solve -Kg {d} = mu Ke {d}, with mu = 1/lambda, so that the
        # positive-definite elastic stiffness is the right-hand matrix. Only
        # the largest mu is needed.
        n = len(free)
        mu_max = 0.0
        if n:
            mu_max = float(eigh(-Kgs, Ks, eigvals_only=True,
                                subset_by_index=[n - 1, n - 1])[0])
        if mu_max <= 0:
            raise no_critical_load
        return 1.0/mu_max

    def _first_order(
        self, nodes: Nodes, members: Members, loads: Loads
    ) -> list[SubMember]:
        """First-order analysis with the elastic stiffness of each
        submember.

        Returns:
            list[SubMember]: All submembers of the model, in assembly order.
        """
        self.Kt = None
        self.iterations = 0
        self._end_forces = {}
        self._axial = {}
        self._setup(nodes, loads)
        submembers = self._submembers(members)
        elastic = [(submbr, submbr.Kl) for submbr in submembers]
        self.Kp = self._assemble(elastic)
        self.global_displacement_vector = self._solve_free(self.Kp)
        self._recover(elastic, self.Kp)
        return submembers

    def _submembers(self, members: Members) -> list[SubMember]:
        """All submembers of the model, in assembly order."""
        return [
            submbr
            for mbr in members.members.values()
            for submbr in mbr.submembers.values()
        ]

    def _setup(self, nodes: Nodes, loads: Loads) -> None:
        """Count the degrees of freedom, list the restrained ones, and build
        the force vector and the span loads of the submembers from the
        loads."""
        # Determine the total degrees of freedom for the model.
        self.nDoF = nodes.count*6

        # Instantiate a list of the restrained degrees of freedom.
        self.restrainedDoF = []
        for i, node in enumerate(nodes.nodes.items()):
            if node[1].restraint == [0, 0, 0, 0, 0, 0]:
                continue
            else:
                for n, DoF in enumerate(node[1].restraint):
                    if DoF == 1:
                        self.restrainedDoF.append(i*6 + n)

        # Remove duplicates from restrained degrees of freedom.
        self.restrainedDoF = list(dict.fromkeys(self.restrainedDoF))

        # Sort the restrained degrees of freedom in ascending order.
        self.restrainedDoF.sort()

        # The force vector: nodal and point loads in the order they were
        # added, then the equivalent nodal actions of the distributed loads.
        F = np.zeros((self.nDoF, 1))
        for load in loads:
            if isinstance(load, NodalLoad):
                dof = 'XYZ'.index(load.direction)
                if load.kind == 'moment':
                    dof += 3
                F[6*(load.node.node_ID - 1) + dof, 0] += load.magnitude
            elif isinstance(load, PointLoad):
                i = 6*(load.node.node_ID - 1)
                F[i:i + 3, 0] += load.member.point_load_vector(
                    load.magnitude, load.direction)

        self._span_actions = {}
        self._span_intensities = {}
        for load in loads.distributed:
            for submbr, actions, w_major, w_minor in \
                    load.member.distributed_load_actions(
                        load.w1, load.w2, load.direction, load.loc1,
                        load.loc2):
                f_global = submbr.rotation_matrix @ actions
                i = 6*(submbr.node_i.node_ID - 1)
                j = 6*(submbr.node_j.node_ID - 1)
                F[i:i + 6, 0] += f_global[:6, 0]
                F[j:j + 6, 0] += f_global[6:, 0]
                key = id(submbr)
                self._span_actions[key] = (
                    self._span_actions.get(key, 0.0) + actions[:, 0])
                self._span_intensities[key] = (
                    self._span_intensities.get(key, 0.0)
                    + np.array([*w_major, *w_minor]))
        self.force_vector = F

    def _free_dofs(self) -> list[int]:
        """Indices of the unrestrained degrees of freedom, in order."""
        restrained = set(self.restrainedDoF)
        return [i for i in range(self.nDoF) if i not in restrained]

    def _assemble(
        self, local_matrices: list[tuple[SubMember, np.ndarray]]
    ) -> np.ndarray:
        """Assemble the structure matrix from local submember matrices.

        Args:
            local_matrices: Pairs of a submember and a 12x12 matrix in its
                local coordinates.

        Returns:
            np.ndarray: The nDoF x nDoF matrix in global coordinates.
        """
        K = np.zeros([self.nDoF, self.nDoF])
        for submbr, k_local in local_matrices:
            T = submbr.transformation_matrix
            self._add_member(
                K,
                submbr.node_i.node_ID,
                submbr.node_j.node_ID,
                T.T.dot(k_local).dot(T)
            )
        return K

    def _solve_free(self, K: np.ndarray) -> np.ndarray:
        """Solve K U = F for the unrestrained degrees of freedom.

        Returns:
            np.ndarray: The full (nDoF x 1) displacement vector, with zeros at
            the restrained degrees of freedom.
        """
        assert self.force_vector is not None

        # Impose the influence of supports to produce the structure stiffness matrix.
        free = self._free_dofs()
        self.Ks = K[np.ix_(free, free)]

        # Solve for unknown displacements.
        U = solve(self.Ks, self.force_vector[free])
        displacements = np.zeros([self.nDoF, 1])
        displacements[free] = U
        return displacements

    def _check_stiffness(
        self,
        nodes: Nodes,
        submembers: list[SubMember],
        K: np.ndarray,
        free: list[int]
    ) -> None:
        """Raise ValueError if the elastic structure stiffness is singular.
        """
        if not free:
            return
        Ks = K[np.ix_(free, free)]
        names = ['Ux', 'Uy', 'Uz', 'phi_x', 'phi_y', 'phi_z']

        # Each node's stiffness is compared with the stiffness it would have
        # if no member end were released, so that the test does not depend on
        # the units or on stiffer members elsewhere.
        reference = np.zeros((self.nDoF//6, 6, 6))
        for submbr in submembers:
            T = submbr.transformation_matrix
            k = T.T @ submbr.Kl_unreleased @ T
            reference[submbr.node_i.node_ID - 1] += k[:6, :6]
            reference[submbr.node_j.node_ID - 1] += k[6:, 6:]

        rows_by_node: dict[int, list[int]] = {}
        for row, dof in enumerate(free):
            rows_by_node.setdefault(dof // 6, []).append(row)
        node_list = list(nodes.nodes.values())
        for position, rows in rows_by_node.items():
            dofs = [free[row] % 6 for row in rows]
            try:
                values, vectors = eigh(
                    Ks[np.ix_(rows, rows)],
                    reference[position][np.ix_(dofs, dofs)])
            except LinAlgError:
                # No member at the node, or one without torsional or bending
                # stiffness: leave it to the mechanism test below.
                continue
            if values[0] > 1e-12:
                continue
            node = node_list[position]
            c = node.coordinates
            # Report the direction with its first component positive.
            mode = vectors[:, 0]/np.linalg.norm(vectors[:, 0])
            mode = mode if mode[np.abs(mode) > 1e-6][0] > 0 else -mode
            terms = [
                (mode[k], names[free[row] % 6])
                for k, row in enumerate(rows) if abs(mode[k]) > 1e-6
            ]
            if len(terms) == 1:
                what, fix = terms[0][1], "Restrain it at the node."
            else:
                what = " ".join(
                    f"{'-' if v < 0 else '+'} {abs(v):.3g} {name}"
                    for v, name in terms).lstrip("+ ")
                fix = "Restrain one of those degrees of freedom at the node."
            raise ValueError(
                f"Node {node.node_ID} at ({c.x:g}, {c.y:g}, {c.z:g}) has no "
                f"stiffness against {what}: every member there is released "
                f"for it. {fix}")

        # A mechanism spread over several nodes shows as a Cholesky pivot
        # that is a vanishing fraction of its diagonal entry, or fails.
        try:
            factor, _ = cho_factor(Ks)
            pivots = np.diag(factor)**2
            mechanism = bool(np.any(pivots*1e12 < np.diag(Ks)))
        except LinAlgError:
            mechanism = True
        if mechanism:
            raise ValueError(
                "The elastic stiffness is singular: the structure is "
                "unstable.")

    def _second_order(
        self,
        nodes: Nodes,
        submembers: list[SubMember],
        tolerance: float,
        max_iterations: int
    ) -> None:
        """Iterate from the first-order solution to second-order equilibrium.

        Each iteration solves ``[Kt(N)] {U} = {F}`` with the axial forces N
        of the previous one. Because the geometry is not updated, the
        internal forces are those of the total tangent stiffness,
        ``[Kt]{U}``, and the increment ``[Kt] {dU} = {F} - [Kt]{U}`` of
        McGuire et al. (Equations 12.11 and 12.16, the load increment zero
        after the first step) gives the same displacements.

        The unbalanced load of the current displacements, with each member
        carrying the axial force they produce, is
        ``{F} - [Kt(N)]{U} = [Kt(N_prev) - Kt(N)]{U}``, plus the rounding
        error of the previous solve, the same as in a first-order analysis,
        which no iteration reduces. The difference is formed element by
        element from the change in axial force
        (``SubMember.tangent_difference``). Forming ``{F} - [Kt]{U}``
        directly would leave rounding error from the elastic stiffness of
        short, stiff submembers far larger than the tolerance.
        """
        assert self.Kp is not None
        assert self.force_vector is not None
        assert self.global_displacement_vector is not None

        free = self._free_dofs()
        self._check_stiffness(nodes, submembers, self.Kp, free)
        F = self.force_vector[free, 0]
        U = self.global_displacement_vector
        unbalanced = 0.0

        for iteration in range(1, max_iterations + 1):
            # The unbalanced load of the current displacements. Each
            # submember keeps the axial force it now carries, for the tangent
            # stiffness and for the P-delta moment along its span.
            R = np.zeros(self.nDoF)
            for submbr in submembers:
                key = id(submbr)
                d, forces = self._end_forces[key]
                N_prev = self._axial.get(key, 0.0)
                N = float(forces[6])
                self._axial[key] = N
                f = submbr.transformation_matrix.T @ (
                    submbr.tangent_difference(N_prev, N) @ d)
                i = 6*(submbr.node_i.node_ID - 1)
                j = 6*(submbr.node_j.node_ID - 1)
                R[i:i + 6] += f[:6]
                R[j:j + 6] += f[6:]
            unbalanced = float(np.linalg.norm(R[free]))

            # Tangent stiffness from the current axial forces.
            tangent = [
                (submbr, submbr.tangent_stiffness(self._axial[id(submbr)]))
                for submbr in submembers
            ]
            Kt = self._assemble(tangent)
            Kts = Kt[np.ix_(free, free)]
            try:
                U[free, 0] = cho_solve(cho_factor(Kts), F)
            except LinAlgError:
                raise RuntimeError(
                    f"Second-order analysis failed in iteration {iteration}: "
                    "the tangent stiffness is not positive definite. The "
                    "loads are most likely at or above the second-order limit "
                    "load, which can be lower than the elastic critical load "
                    "because the axial forces change as the structure "
                    "deflects.") from None

            self.Kt = Kt
            self.iterations = iteration
            self._recover(tangent, Kt)

            # Converged when the unbalanced load of the displacements that
            # went into this iteration was small; the new displacements are
            # closer still. The displacement change is not tested, because
            # in an ill-conditioned model, such as a fine mesh near the
            # critical load, rounding keeps it from falling as low.
            if unbalanced <= tolerance*np.linalg.norm(F):
                return

        raise RuntimeError(
            f"Second-order analysis did not converge in {max_iterations} "
            f"iterations; the last unbalanced load norm was "
            f"{unbalanced:.3e}.")

    def _recover(
        self,
        local_matrices: list[tuple[SubMember, np.ndarray]],
        K: np.ndarray
    ) -> None:
        """Recover the reactions, and the end displacements and end forces
        of each submember (kept by the solver, not on the submember).

        Args:
            local_matrices: Pairs of a submember and the local stiffness
                matrix used to find its end forces.
            K: The structure matrix that produced the displacements.
        """
        assert self.global_displacement_vector is not None
        assert self.force_vector is not None

        # Back-substitute displacements to calculate reaction forces. The
        # stiffness forces at a node balance the loads applied to it plus its
        # reaction, so the applied loads (nodal loads and equivalent nodal
        # actions alike) are removed once per node.
        self.global_force_vector = np.matmul(
            K, self.global_displacement_vector) - self.force_vector
        assert self.global_force_vector is not None

        # Use nodal displacements to determine member forces.
        for submbr, k_local in local_matrices:
            ia = submbr.node_i.node_ID*6-6
            ib = submbr.node_i.node_ID*6-1
            ja = submbr.node_j.node_ID*6-6
            jb = submbr.node_j.node_ID*6-1

            mbrDisplacements = np.array([
                self.global_displacement_vector[ia, 0],
                self.global_displacement_vector[ia+1, 0],
                self.global_displacement_vector[ia+2, 0],
                self.global_displacement_vector[ia+3, 0],
                self.global_displacement_vector[ia+4, 0],
                self.global_displacement_vector[ib, 0],
                self.global_displacement_vector[ja, 0],
                self.global_displacement_vector[ja+1, 0],
                self.global_displacement_vector[ja+2, 0],
                self.global_displacement_vector[ja+3, 0],
                self.global_displacement_vector[ja+4, 0],
                self.global_displacement_vector[jb, 0]
            ]).T

            d = np.matmul(submbr.transformation_matrix, mbrDisplacements)

            # The forces of the displacements, less the equivalent nodal
            # actions of the span loads: the forces the nodes apply to the
            # submember's ends.
            key = id(submbr)
            forces = np.matmul(k_local, d)
            if key in self._span_actions:
                forces = forces - self._span_actions[key]
            self._end_forces[key] = (d, forces)

    def _results(
        self, nodes: Nodes, members: Members, second_order: bool
    ) -> Results:
        """Collect the recovered displacements, reactions and member forces
        into a Results object that later solves do not change."""
        assert self.global_displacement_vector is not None
        assert self.global_force_vector is not None

        # Reactions exist only at the restrained degrees of freedom; at the
        # others K U - F is rounding error.
        reactions = self.global_force_vector[:, 0].copy()
        reactions[self._free_dofs()] = 0.0

        return Results(
            nodes=list(nodes.nodes.values()),
            displacements=self.global_displacement_vector,
            reactions=reactions,
            members=[
                MemberResult(mbr, tuple(
                    self._submember_result(submbr)
                    for submbr in mbr.submembers.values()))
                for mbr in members.members.values()],
            second_order=second_order,
            iterations=self.iterations,
        )

    def _submember_result(self, submbr: SubMember) -> SubMemberResult:
        """The results of one submember, from the solver's own record of
        the analysis."""
        key = id(submbr)
        d, f = self._end_forces[key]
        w = self._span_intensities.get(key, np.zeros(4))
        return SubMemberResult(
            submember=submbr,
            displacements=d,
            # FORCE_KEYS follow the order of the degrees of freedom at an end.
            forces={name: (float(f[k]), float(f[k + 6]))
                    for k, name in enumerate(FORCE_KEYS)},
            w_major=(float(w[0]), float(w[1])),
            w_minor=(float(w[2]), float(w[3])),
            second_order_axial=self._axial.get(key, 0.0),
        )

    @staticmethod
    def _add_member(
        K: np.ndarray, node_ID_i: int, node_ID_j: int, KG: np.ndarray
    ) -> None:
        """Add a 12x12 global submember matrix into the structure matrix K."""
        k11 = KG[0:6, 0:6]
        k12 = KG[0:6, 6:12]
        k21 = KG[6:12, 0:6]
        k22 = KG[6:12, 6:12]

        ia = 6*node_ID_i-6
        ib = 6*node_ID_i-1
        ja = 6*node_ID_j-6
        jb = 6*node_ID_j-1

        K[ia:ib+1, ia:ib+1] = K[ia:ib+1, ia:ib+1] + k11
        K[ia:ib+1, ja:jb+1] = K[ia:ib+1, ja:jb+1] + k12
        K[ja:jb+1, ia:ib+1] = K[ja:jb+1, ia:ib+1] + k21
        K[ja:jb+1, ja:jb+1] = K[ja:jb+1, ja:jb+1] + k22
