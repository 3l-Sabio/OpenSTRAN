from .Member import Member
import math


class Members():
    """
    Object that holds the member objects
    """

    def __init__(self, nodes):
        self.members = {}
        self.count = 0
        self.nodes = nodes

    def addMember(
        self,
        node_i,
        node_j,
        i_release=None,
        j_release=None,
        E=None,
        Ixx=None,
        Iyy=None,
        A=None,
        G=None,
        J=None,
        mesh=None,
        bracing=None,
        shape=None
    ):
        """
        Method to add member objects to the model

        REQUIRED PARAMETERS:
        node_i: OpenStruct.node 3D Space Frame Node Object
        node_j: OpenStruct.node 3D Space Frame Node Object

        OPTIONAL PARAMETERS
        i_release: False = unpinned, True = pinned
        j_release: False = unpinned, True = pinned
        E: Young's Modulus [ksi]
        Izz: Moment of Inertia about the strong axis [in^4]
        Ixx: Moment of Inertia about the weak axis [in^4]
        A: Cross-Sectional Area [in^2]
        G: Shear Modulus [ksi]
        J: Polar Moment of Inertia [in^4]
        mesh: number of discretizations per member

        USAGE:
        M1 = frame.members.addMember(N1,N2)
        M2 = frame.members.addMember(N2,N3)
        M3 = frame.members.addMember(N3,N4)
        """
        self.count += 1
        member = Member(
            self.nodes,
            node_i,
            node_j,
            i_release,
            j_release,
            E,
            Ixx,
            Iyy,
            A,
            G,
            J,
            mesh,
            bracing,
            shape
        )
        self.members[self.count] = member
        return (member)
