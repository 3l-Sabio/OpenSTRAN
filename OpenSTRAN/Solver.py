from .Nodes import Nodes
from .Members import Members

import numpy as np


class Solver():
    """Solver class for structural finite element analysis.

    This class performs finite element analysis on structural models by assembling
    the global stiffness matrix, applying boundary conditions, and solving for nodal
    displacements and member forces.

    :ivar nDoF: Total number of degrees of freedom in the structure
    :type nDoF: int
    :ivar pinDoF: List of pinned (rotational) degrees of freedom indices
    :type pinDoF: list[int]
    :ivar restrainedDoF: List of restrained degrees of freedom indices
    :type restrainedDoF: list[int]
    :ivar Kp: Primary stiffness matrix for the structure
    :type Kp: numpy.ndarray | None
    :ivar force_vector: Global force vector with applied loads
    :type force_vector: numpy.ndarray | None
    :ivar global_displacement_vector: Global displacement vector at all nodes
    :type global_displacement_vector: numpy.ndarray | None
    :ivar global_force_vector: Global reaction force vector
    :type global_force_vector: numpy.ndarray | None
    """

    def __init__(self) -> None:
        """Initialize the Solver with empty attributes.

        Sets up the solver with default values for the stiffness matrix,
        degrees of freedom tracking, and solution vectors.
        """
        self.nDoF: int = 0
        self.pinDoF: list[int] = []
        self.restrainedDoF: list[int] = []
        self.Kp: np.ndarray | None = None
        # self.restrainedIndex: list[int] = []
        self.force_vector: np.ndarray | None = None
        self.global_displacement_vector: np.ndarray | None = None
        self.global_force_vector: np.ndarray | None = None

    def solve(self, nodes: Nodes, members: Members) -> None:
        """Solve the structural system for displacements and member forces.

        This method performs a complete finite element analysis including:
        
        - Assembly of the global stiffness matrix
        - Application of boundary conditions
        - Solution for nodal displacements using matrix reduction
        - Computation of member forces and reactions
        - Removal of equivalent nodal actions (distributed loads)

        :param nodes: Collection of nodes in the structural model
        :type nodes: Nodes
        :param members: Collection of members in the structural model
        :type members: Members
        :returns: None
        :rtype: None
        """
        # Re-instantiate empty arrays for second-order analysis.
        self.restrainedDoF = []

        # Determine the total degrees of freedom for the model.
        self.nDoF = nodes.count*6

        # Determine the rotational restrained degrees of freedom.
        for mbr in members.members.values():

            for submbr in mbr.submembers.values():

                if submbr.i_release == False and submbr.j_release == False:
                    continue

                elif submbr.i_release == True and submbr.j_release == False:
                    self.pinDoF.append(submbr.node_i.node_ID*6-1)
                    self.pinDoF.append(submbr.node_i.node_ID*6)

                elif submbr.i_release == False and submbr.j_release == True:
                    self.pinDoF.append(submbr.node_j.node_ID*6-1)
                    self.pinDoF.append(submbr.node_j.node_ID*6)

                elif submbr.i_release == True and submbr.j_release == True:
                    self.pinDoF.append(submbr.node_i.node_ID*6-2)
                    self.pinDoF.append(submbr.node_i.node_ID*6-1)
                    self.pinDoF.append(submbr.node_i.node_ID*6)
                    self.pinDoF.append(submbr.node_j.node_ID*6-2)
                    self.pinDoF.append(submbr.node_j.node_ID*6-1)
                    self.pinDoF.append(submbr.node_j.node_ID*6)

        # Remove duplicates from the rotational restrained degrees of freedom.
        # Duplicates may exist because a user could potentially define
        # an i and j release on each side of a single node.
        self.pinDoF = list(dict.fromkeys(self.pinDoF))

        # Instantiate the primary stiffness matrix.
        self.Kp = np.zeros([self.nDoF, self.nDoF])

        # Instantiate a list of the restrained degrees of freedom.
        for i, node in enumerate(nodes.nodes.items()):
            if node[1].restraint == [0, 0, 0, 0, 0, 0]:
                continue
            else:
                for n, DoF in enumerate(node[1].restraint):
                    if DoF == 1:
                        self.restrainedDoF.append(i*6 + n)

        # Check pins to see if attached members contribute to stiffness.
        for DoF in [x-1 for x in self.pinDoF]:
            if (np.sum(self.Kp[DoF, :]) < 1*10**-6):
                self.restrainedDoF.append(DoF)

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

        # Construct the primary stiffness matrix for the structure.
        for mbr in members.members.values():
            for submbr in mbr.submembers.values():
                node_ID_i = submbr.node_i.node_ID
                node_ID_j = submbr.node_j.node_ID
                i_release = submbr.i_release
                j_release = submbr.j_release
                KG = submbr.Kg
                self.AddMemberToKp(node_ID_i, node_ID_j,
                                   i_release, j_release, KG)

        # Impose the influence of supports to produce the structure stiffness matrix.
        self.Ks = np.delete(self.Kp, self.restrainedDoF, 0)
        self.Ks = np.delete(self.Ks, self.restrainedDoF, 1)
        self.Ks = np.matrix(self.Ks)

        # Solve for unknown displacements.
        reducedForceVector = np.delete(
            self.force_vector, self.restrainedDoF, 0)

        U = np.linalg.solve(self.Ks, reducedForceVector)
        self.global_displacement_vector = np.zeros([self.nDoF, 1])
        assert self.global_displacement_vector is not None
        index = 0
        for i in range(self.nDoF):
            if i in self.restrainedDoF:
                continue
            else:
                self.global_displacement_vector[i] = U[index]
                index += 1

        # Back-substitute displacements to calculate reaction forces.
        self.global_force_vector = np.matmul(
            self.Kp, self.global_displacement_vector)
        assert self.global_force_vector is not None

        # Use nodal displacements to determine member forces.
        for mbr in members.members.values():
            for submbr in mbr.submembers.values():
                if submbr.i_release == False and submbr.j_release == False:
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
                        submbr.Kl, submbr.results['displacements'])

                    submbr.results['axial'] = [forces[0], forces[6]]
                    submbr.results['shear'] = [forces[1], forces[7]]
                    submbr.results['transverse shear'] = [forces[2], forces[8]]
                    submbr.results['torsional moments'] = [
                        forces[3], forces[9]]
                    submbr.results['minor axis moments'] = [
                        forces[4], forces[10]]
                    submbr.results['major axis moments'] = [
                        forces[5], forces[11]]

                elif submbr.i_release == True and submbr.j_release == False:
                    ia = submbr.node_i.node_ID*6-6
                    ib = submbr.node_i.node_ID*6-3
                    ja = submbr.node_j.node_ID*6-6
                    jb = submbr.node_j.node_ID*6-1

                    mbrDisplacements = np.array([
                        self.global_displacement_vector[ia, 0],
                        self.global_displacement_vector[ia+1, 0],
                        self.global_displacement_vector[ia+2, 0],
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
                        submbr.Kl, submbr.results['displacements'])

                    submbr.results['axial'] = [forces[0], forces[4]]
                    submbr.results['transverse shear'] = [forces[1], forces[5]]
                    submbr.results['shear'] = [forces[2], forces[6]]
                    submbr.results['torsional moments'] = [
                        forces[3], forces[7]]
                    submbr.results['major axis moments'] = [0, forces[8]]
                    submbr.results['minor axis moments'] = [0, forces[9]]

                elif submbr.i_release == False and submbr.j_release == True:
                    ia = submbr.node_i.node_ID*6-6
                    ib = submbr.node_i.node_ID*6-1
                    ja = submbr.node_j.node_ID*6-6
                    jb = submbr.node_j.node_ID*6-3

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
                        self.global_displacement_vector[jb, 0]
                    ]).T

                    submbr.results['displacements'] = np.matmul(
                        submbr.transformation_matrix, mbrDisplacements)
                    forces = np.matmul(
                        submbr.Kl, submbr.results['displacements'])

                    submbr.results['axial'] = [forces[0], forces[6]]
                    submbr.results['transverse shear'] = [forces[1], forces[7]]
                    submbr.results['shear'] = [forces[2], forces[8]]
                    submbr.results['torsional moments'] = [
                        forces[3], forces[9]]
                    submbr.results['major axis moments'] = [forces[4], 0]
                    submbr.results['minor axis moments'] = [forces[5], 0]

                elif submbr.i_release == True and submbr.j_release == True:
                    ia = submbr.node_i.node_ID*6-6
                    ib = submbr.node_i.node_ID*6-3
                    ja = submbr.node_j.node_ID*6-6
                    jb = submbr.node_j.node_ID*6-3

                    mbrDisplacements = np.array([
                        self.global_displacement_vector[ia, 0],
                        self.global_displacement_vector[ia+1, 0],
                        self.global_displacement_vector[ib, 0],
                        self.global_displacement_vector[ja, 0],
                        self.global_displacement_vector[ja+1, 0],
                        self.global_displacement_vector[jb, 0]
                    ]).T

                    submbr.results['displacements'] = np.matmul(
                        submbr.transformation_matrix, mbrDisplacements)
                    forces = np.matmul(
                        submbr.Kl, submbr.results['displacements'])

                    submbr.results['axial'] = [forces[0], forces[3]]
                    submbr.results['transverse shear'] = [forces[1], forces[4]]
                    submbr.results['shear'] = [forces[2], forces[5]]
                    submbr.results['torsional moments'] = [0, 0]
                    submbr.results['major axis moments'] = [0, 0]
                    submbr.results['minor axis moments'] = [0, 0]

        # Remove the influence of equivalent nodal actions.
        for mbr in members.members.values():
            for n, submbr in mbr.submembers.items():

                # Determine DOFs associated with the submember nodes.
                ia = submbr.node_i.node_ID*6-6
                ib = submbr.node_i.node_ID*6-1
                ja = submbr.node_j.node_ID*6-6
                jb = submbr.node_j.node_ID*6-1

                # Remove influence of equivalent nodal actions from the global force vector.

                self.global_force_vector[ia] = self.global_force_vector[ia] - \
                    submbr.node_i.eFx
                self.global_force_vector[ia +
                                         1] = self.global_force_vector[ia+1] - submbr.node_i.eFy
                self.global_force_vector[ia +
                                         2] = self.global_force_vector[ia+2] - submbr.node_i.eFz
                self.global_force_vector[ia +
                                         3] = self.global_force_vector[ia+3] - submbr.node_i.eMx
                self.global_force_vector[ia +
                                         4] = self.global_force_vector[ia+4] - submbr.node_i.eMy
                self.global_force_vector[ib] = self.global_force_vector[ib] - \
                    submbr.node_i.eMz

                self.global_force_vector[ja] = self.global_force_vector[ja] - \
                    submbr.node_j.eFx
                self.global_force_vector[ja +
                                         1] = self.global_force_vector[ja+1] - submbr.node_j.eFy
                self.global_force_vector[ja +
                                         2] = self.global_force_vector[ja+2] - submbr.node_j.eFz
                self.global_force_vector[ja +
                                         3] = self.global_force_vector[ja+3] - submbr.node_j.eMx
                self.global_force_vector[ja +
                                         4] = self.global_force_vector[ja+4] - submbr.node_j.eMy
                self.global_force_vector[jb] = self.global_force_vector[jb] - \
                    submbr.node_j.eMz

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
                if submbr.node_i.mesh_node != True:
                    submbr.node_i.Rx = self.global_force_vector[ia][0]
                    submbr.node_i.Ry = self.global_force_vector[ia+1][0]
                    submbr.node_i.Rz = self.global_force_vector[ia+2][0]
                    submbr.node_i.Rmx = self.global_force_vector[ia+3][0]
                    submbr.node_i.Rmy = self.global_force_vector[ia+4][0]
                    submbr.node_i.Rmz = self.global_force_vector[ib][0]
                elif submbr.node_j.mesh_node != True:
                    submbr.node_j.Rx = self.global_force_vector[ja][0]
                    submbr.node_j.Ry = self.global_force_vector[ja+1][0]
                    submbr.node_j.Rz = self.global_force_vector[ja+2][0]
                    submbr.node_j.Rmx = self.global_force_vector[ja+3][0]
                    submbr.node_j.Rmy = self.global_force_vector[ja+4][0]
                    submbr.node_j.Rmz = self.global_force_vector[jb][0]

    def AddMemberToKp(self, node_ID_i: int, node_ID_j: int, i_release: bool, j_release: bool, KG: np.ndarray) -> None:
        """Add member stiffness contributions to the global stiffness matrix.

        Extracts the appropriate submatrix from the member's global stiffness matrix
        based on end releases and assembles it into the primary stiffness matrix at
        the correct locations corresponding to the member's nodes.

        :param node_ID_i: Node ID at the start of the member
        :type node_ID_i: int
        :param node_ID_j: Node ID at the end of the member
        :type node_ID_j: int
        :param i_release: Whether the i-node has rotational releases (pinned)
        :type i_release: bool
        :param j_release: Whether the j-node has rotational releases (pinned)
        :type j_release: bool
        :param KG: Global stiffness matrix of the member (12x12 or reduced)
        :type KG: numpy.ndarray
        :returns: None
        :rtype: None
        """
        assert self.Kp is not None

        if i_release == False and j_release == False:
            k11 = KG[0:6, 0:6]
            k12 = KG[0:6, 6:12]
            k21 = KG[6:12, 0:6]
            k22 = KG[6:12, 6:12]

            ia = 6*node_ID_i-6
            ib = 6*node_ID_i-1
            ja = 6*node_ID_j-6
            jb = 6*node_ID_j-1

        elif i_release == True and j_release == False:
            k11 = KG[0:4, 0:4]
            k12 = KG[0:4, 4:10]
            k21 = KG[4:10, 0:4]
            k22 = KG[4:10, 4:10]

            ia = 6*node_ID_i-6
            ib = 6*node_ID_i-3
            ja = 6*node_ID_j-6
            jb = 6*node_ID_j-1

        elif i_release == False and j_release == True:
            k11 = KG[0:6, 0:6]
            k12 = KG[0:6, 6:10]
            k21 = KG[6:10, 0:6]
            k22 = KG[6:10, 6:10]

            ia = 6*node_ID_i-6
            ib = 6*node_ID_i-1
            ja = 6*node_ID_j-6
            jb = 6*node_ID_j-3

        elif i_release == True and j_release == True:
            k11 = KG[0:3, 0:3]
            k12 = KG[0:3, 3:6]
            k21 = KG[3:6, 0:3]
            k22 = KG[3:6, 3:6]

            ia = 6*node_ID_i-6
            ib = 6*node_ID_i-4
            ja = 6*node_ID_j-6
            jb = 6*node_ID_j-4

        else:
            raise ValueError(
                "Member boundary conditions must be pinned or fixed"
            )

        self.Kp[ia:ib+1, ia:ib+1] = self.Kp[ia:ib+1, ia:ib+1] + k11
        self.Kp[ia:ib+1, ja:jb+1] = self.Kp[ia:ib+1, ja:jb+1] + k12
        self.Kp[ja:jb+1, ia:ib+1] = self.Kp[ja:jb+1, ia:ib+1] + k21
        self.Kp[ja:jb+1, ja:jb+1] = self.Kp[ja:jb+1, ja:jb+1] + k22
