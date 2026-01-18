class Node():
    """
    3D Space Frame Node Object

    REQUIRED PARAMETERS:

    coordinates:    (x,y,z)
    nodeID:            Unique Identifier for the Node

    OPTIONAL PARAMETERS:

    meshNode:    True - The node is part of a member mesh
                False - Standard node

    restraint = [Ux, Uy, Uz, φx, φy, φz], 0 = 'free', 1 = 'locked'

    plane = 'xy' – defines a model constrained to the X-Y plane
    plane = 'yz' – defines a model constrained to the Y-Z plane
    plane = 'xz' – defines a model constrained to the X-Z plane

    DEFAULT PARAMETERS:

    Fx:        Force applied to the node along the x-axis    [kips]
    Fy:        Force applied to the node along the y-axis    [kips]
    Fz:        Force applied to the node along the z-axis    [kips]
    Mx:        Moment applied to the node along the x-axis    [kip-ft]
    My:        Moment applied to the node along the y-axis    [kip-ft]
    Mz:        Moment applied to the node along the z-axis    [kip-ft]
    Ux:        Nodal displacement in the x direction        [ft]
    Uy:        Nodal displacement in the y direction        [ft]
    Uz:        Nodal displacement in the z direction        [ft]
    phi_x:    Nodal rotation in the x direction            [rad]
    phi_y:    Nodal rotation in the y direction            [rad]
    phi_z:    Nodal rotation in the z direction            [rad]
    eFx:    Equivalent nodal force along the x-axis        [kips]
    eFy:    Equivalent nodal force along the y-axis        [kips]
    eFz:    Equivalent nodal force along the z-axis        [kips]
    eMx:    Equivalent nodal moment along the x-axis    [kip-ft]
    eMy:    Equivalent nodal moment along the y-axis    [kip-ft]
    eMz:    Equivalent nodal moment along the z-axis    [kip-ft]
    """

    def __init__(
        self,
        coordinates,
        nodeID,
        meshNode=False,
        Fx=0.0,
        Fy=0.0,
        Fz=0.0,
        Mx=0.0,
        My=0.0,
        Mz=0.0,
        Ux=0.0,
        Uy=0.0,
        Uz=0.0,
        phi_x=0.0,
        phi_y=0.0,
        phi_z=0.0,
        eFx=0.0,
        eFy=0.0,
        eFz=0.0,
        eMx=0.0,
        eMy=0.0,
        eMz=0.0,
        plane=None,
        restraint=None
    ):
        # coordinates
        self.coordinates = coordinates
        # ID
        self.nodeID = nodeID
        # True indicates the node is part of a member mesh
        self.meshNode = meshNode
        # forces
        self.Fx = Fx
        self.Fy = Fy
        self.Fz = Fz
        # moments
        self.Mx = Mx
        self.My = My
        self.Mz = Mz
        # displacements
        self.Ux = Ux
        self.Uy = Uy
        self.Uz = Uz
        # rotations
        self.phi_x = phi_x
        self.phi_y = phi_y
        self.phi_z = phi_z
        # equivalent forces
        self.eFx = eFx
        self.eFy = eFy
        self.eFz = eFz
        # equivalent moments
        self.eMx = eMx
        self.eMy = eMy
        self.eMz = eMz
        # restraint
        if plane == None:
            self.restraint = [0, 0, 0, 0, 0, 0]
        elif plane == 'xy':
            self.restraint = [0, 0, 1, 1, 1, 0]
        elif plane == 'yz':
            self.restraint = [1, 0, 0, 0, 1, 1]
        elif plane == 'zx':
            self.restraint = [0, 1, 0, 1, 0, 1]
        # nodal reactions
        self.Rx = 0
        self.Ry = 0
        self.Rz = 0
        self.Rmx = 0
        self.Rmy = 0
        self.Rmz = 0

    def addRestraint(self, restraint):
        """
        Method to restrain the nodal degrees of freedom

        REQUIRED PARAMETERS:

        restraint:    list of 0s and 1s for the various degrees of
                    freedom, [Ux, Uy, Uz, φx, φy, φz], where non-zero
                    values are restrained degrees of freedom. For
                    example, the list to represent a pin would hold
                    1s for the translational degrees of freedom and
                    0s for the rotational degrees of freedom.

                    pinned node:                [1,1,1,0,0,0]
                    fixed node:                    [1,1,1,1,1,1]
                    roller in the x direction:    [0,1,1,0,0,0]
                    etc.

        USAGE:

        Node.addRestraint([1,1,1,0,0,0])
        """
        # check the user defined list is properly formatted
        if type(restraint) == list and len(restraint) == 6 and restraint == [n for n in restraint if n in [0, 1]]:
            # restrain the node
            self.restraint = restraint
        else:
            raise ValueError('{msg1}\n{msg2}\n{msg3}\n{msg4}\n{msg5}\n{msg6}'.format(
                msg1=str('restraint: "{r}" not recognized.'.format(
                    r=restraint
                )
                ),
                msg2=str('restraint must be a list of 0s and 1s:'),
                msg3=str('Degrees of Freedom: [Ux, Uy, Uz, φx, φy, φz]'),
                msg4=str("Pinned Node: [1,1,1,0,0,0]"),
                msg5=str("Fixed Node: [1,1,1,1,1,1]"),
                msg6=str("Roller in the x direction: [0,1,1,0,0,0]")
            ))

    def addLoad(self, mag, lType='moment', direction='y'):
        """
        lType: type of nodal load moment or point load
        mag: magnitude of the applied load in kips or kip-ft
        direction: the local plane in which the load is applied
        """

        if lType == 'moment':
            if direction == 'X':
                self.Mx += mag*12
            if direction == 'Y':
                self.My += mag*12
            if direction == 'Z':
                self.Mz += mag*12
        else:
            if direction == 'X':
                self.Fx += mag
            if direction == 'Y':
                self.Fy += mag
            if direction == 'Z':
                self.Fz += mag
