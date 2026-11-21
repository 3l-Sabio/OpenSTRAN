from .Nodes import Nodes
from .Members import Members
from .Submember import SubMember

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
            second-order analysis; 0 for a first-order analysis or after a
            failed second-order analysis.
        has_results (bool): Whether the last solve recovered results. False
            if it failed before the first-order solution; after a failed
            second-order analysis the results are the first-order ones.
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
        self.has_results: bool = False
        self.force_vector: np.ndarray | None = None
        self.global_displacement_vector: np.ndarray | None = None
        self.global_force_vector: np.ndarray | None = None

    def solve(
        self,
        nodes: Nodes,
        members: Members,
        second_order: bool = False,
        tolerance: float = 1e-8,
        max_iterations: int = 50
    ) -> None:
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
        geometry held fixed. If a second-order analysis fails or is 
        interrupted, the model is left holding the first-order solution.

        Args:
            nodes (Nodes): Collection of nodes in the structural model.
            members (Members): Collection of members in the structural model.
            second_order (bool, optional): Include the effect of axial forces
                on stiffness. Defaults to False.
            tolerance (float, optional): Convergence tolerance of a
                second-order analysis: the largest norm of the unbalanced
                load, relative to the norm of the applied loads. Defaults to
                1e-8.
            max_iterations (int, optional): Maximum number of iterations of a
                second-order analysis. Defaults to 50.

        Raises:
            RuntimeError: If a second-order analysis does not converge, or if
                its tangent stiffness stops being positive definite (the loads
                are most likely at or above the second-order limit load).
            ValueError: If a second-order analysis finds that the elastic
                stiffness is singular.
        """
        self.Kt = None
        self.iterations = 0
        self.has_results = False
        self._setup(nodes)

        # First-order analysis with the elastic stiffness of each submember.
        submembers = self._submembers(members)
        elastic = [(submbr, submbr.Kl) for submbr in submembers]
        for submbr in submembers:
            submbr.second_order_axial = 0.0
        self.Kp = self._assemble(elastic)
        self.global_displacement_vector = self._solve_free(self.Kp)
        self._recover(elastic, self.Kp)
        self.has_results = True

        if not second_order:
            return

        first_order = self.global_displacement_vector.copy()
        completed = False
        try:
            self._second_order(nodes, submembers, tolerance, max_iterations)
            completed = True
        finally:
            if not completed:
                # Whether an error or an interrupt stopped the analysis,
                # leave the model holding the first-order solution rather
                # than a mixture of iterations.
                for submbr in submembers:
                    submbr.second_order_axial = 0.0
                self.global_displacement_vector = first_order
                self._recover(elastic, self.Kp)
                self.Kt = None
                self.iterations = 0

    def critical_load_factor(self, nodes: Nodes, members: Members) -> float:
        """Elastic critical load factor of the applied loads.

        Solves the eigenproblem of McGuire et al., Equation 8.7,
        ``[Ke + lambda Kg] {d} = 0``, in which the geometric stiffness Kg is
        formed from the axial forces of a first-order analysis under the
        applied loads (see ``SubMember.geometric_stiffness``). The model is 
        left holding the first-order solution.

        Args:
            nodes (Nodes): Collection of nodes in the structural model.
            members (Members): Collection of members in the structural model.

        Returns:
            float: The smallest positive factor lambda such that lambda times
            the applied loads is an elastic critical load.

        Raises:
            ValueError: If the applied loads put no member in compression, if
                every member in compression is restrained against bending and
                twisting, or if the elastic stiffness is singular.
        """
        self.solve(nodes, members)
        assert self.Kp is not None

        submembers = self._submembers(members)
        free = self._free_dofs()
        self._check_stiffness(nodes, submembers, self.Kp, free)

        no_critical_load = ValueError(
            "The applied loads have no elastic critical load: they put no "
            "member in compression, or every member in compression is "
            "restrained against bending and twisting.")
        scale = max(
            (abs(float(force))
             for submbr in submembers
             for key in ('axial', 'shear', 'transverse shear')
             for force in submbr.results[key]),
            default=0.0)
        geometric: list[tuple[SubMember, np.ndarray]] = []
        compression = False
        for submbr in submembers:
            Fx2 = float(submbr.results['axial'][1])
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

    def _submembers(self, members: Members) -> list[SubMember]:
        """All submembers of the model, in assembly order."""
        return [
            submbr
            for mbr in members.members.values()
            for submbr in mbr.submembers.values()
        ]

    def _setup(self, nodes: Nodes) -> None:
        """Count the degrees of freedom, list the restrained ones and build
        the force vector."""
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

        # Instantiate the force vector.
        self.force_vector = np.zeros((self.nDoF, 1))
        for i, node in enumerate(nodes.nodes.items()):
            self.force_vector[i*6][0] = node[1].Fx
            self.force_vector[i*6 + 1][0] = node[1].Fy
            self.force_vector[i*6 + 2][0] = node[1].Fz
            self.force_vector[i*6 + 3][0] = node[1].Mx
            self.force_vector[i*6 + 4][0] = node[1].My
            self.force_vector[i*6 + 5][0] = node[1].Mz

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
                "The elastic stiffness is singular: the structure is a "
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
                N_prev = submbr.second_order_axial
                N = float(submbr.results['axial'][1])
                submbr.second_order_axial = N
                f = submbr.transformation_matrix.T @ (
                    submbr.tangent_difference(N_prev, N)
                    @ np.asarray(submbr.results['displacements'], dtype=float))
                i = 6*(submbr.node_i.node_ID - 1)
                j = 6*(submbr.node_j.node_ID - 1)
                R[i:i + 6] += f[:6]
                R[j:j + 6] += f[6:]
            unbalanced = float(np.linalg.norm(R[free]))

            # Tangent stiffness from the current axial forces.
            tangent = [
                (submbr, submbr.tangent_stiffness(submbr.second_order_axial))
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
        """Recover reactions, member forces and nodal results.

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

            submbr.results['displacements'] = np.matmul(
                submbr.transformation_matrix, mbrDisplacements)
            forces = np.matmul(
                k_local, submbr.results['displacements'])

            submbr.results['axial'] = [forces[0], forces[6]]
            submbr.results['shear'] = [forces[1], forces[7]]
            submbr.results['transverse shear'] = [forces[2], forces[8]]
            submbr.results['torsional moments'] = [
                forces[3], forces[9]]
            submbr.results['minor axis moments'] = [
                forces[4], forces[10]]
            submbr.results['major axis moments'] = [
                forces[5], forces[11]]

        # Remove the influence of equivalent nodal actions from member forces
        # and store the nodal results.
        for submbr, _ in local_matrices:

            # Determine DOFs associated with the submember nodes.
            ia = submbr.node_i.node_ID*6-6
            ib = submbr.node_i.node_ID*6-1
            ja = submbr.node_j.node_ID*6-6
            jb = submbr.node_j.node_ID*6-1

            # Remove influence of equivalent nodal actions from member forces.

            submbr.results['axial'][0] = submbr.results['axial'][0] - \
                submbr.ENAs['axial'][0]
            submbr.results['axial'][1] = submbr.results['axial'][1] - \
                submbr.ENAs['axial'][1]

            submbr.results['transverse shear'][0] = submbr.results['transverse shear'][0] - \
                submbr.ENAs['transverse shear'][0]
            submbr.results['transverse shear'][1] = submbr.results['transverse shear'][1] - \
                submbr.ENAs['transverse shear'][1]

            submbr.results['shear'][0] = submbr.results['shear'][0] - \
                submbr.ENAs['shear'][0]
            submbr.results['shear'][1] = submbr.results['shear'][1] - \
                submbr.ENAs['shear'][1]

            submbr.results['torsional moments'][0] = submbr.results['torsional moments'][0] - \
                submbr.ENAs['torsional moments'][0]
            submbr.results['torsional moments'][1] = submbr.results['torsional moments'][1] - \
                submbr.ENAs['torsional moments'][1]

            submbr.results['major axis moments'][0] = submbr.results['major axis moments'][0] - \
                submbr.ENAs['major axis moments'][0]
            submbr.results['major axis moments'][1] = submbr.results['major axis moments'][1] - \
                submbr.ENAs['major axis moments'][1]

            submbr.results['minor axis moments'][0] = submbr.results['minor axis moments'][0] - \
                submbr.ENAs['minor axis moments'][0]
            submbr.results['minor axis moments'][1] = submbr.results['minor axis moments'][1] - \
                submbr.ENAs['minor axis moments'][1]

            # Store nodal reactions.
            if submbr.node_i.mesh_node is not True:
                submbr.node_i.Rx = self.global_force_vector[ia][0]
                submbr.node_i.Ry = self.global_force_vector[ia+1][0]
                submbr.node_i.Rz = self.global_force_vector[ia+2][0]
                submbr.node_i.Rmx = self.global_force_vector[ia+3][0]
                submbr.node_i.Rmy = self.global_force_vector[ia+4][0]
                submbr.node_i.Rmz = self.global_force_vector[ib][0]
            if submbr.node_j.mesh_node is not True:
                submbr.node_j.Rx = self.global_force_vector[ja][0]
                submbr.node_j.Ry = self.global_force_vector[ja+1][0]
                submbr.node_j.Rz = self.global_force_vector[ja+2][0]
                submbr.node_j.Rmx = self.global_force_vector[ja+3][0]
                submbr.node_j.Rmy = self.global_force_vector[ja+4][0]
                submbr.node_j.Rmz = self.global_force_vector[jb][0]

            # Store nodal displacements.
            submbr.node_i.Ux = self.global_displacement_vector[ia][0]
            submbr.node_i.Uy = self.global_displacement_vector[ia+1][0]
            submbr.node_i.Uz = self.global_displacement_vector[ia+2][0]
            submbr.node_i.phi_x = self.global_displacement_vector[ia+3][0]
            submbr.node_i.phi_y = self.global_displacement_vector[ia+4][0]
            submbr.node_i.phi_z = self.global_displacement_vector[ib][0]
            submbr.node_j.Ux = self.global_displacement_vector[ja][0]
            submbr.node_j.Uy = self.global_displacement_vector[ja+1][0]
            submbr.node_j.Uz = self.global_displacement_vector[ja+2][0]
            submbr.node_j.phi_x = self.global_displacement_vector[ja+3][0]
            submbr.node_j.phi_y = self.global_displacement_vector[ja+4][0]
            submbr.node_j.phi_z = self.global_displacement_vector[jb][0]

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
