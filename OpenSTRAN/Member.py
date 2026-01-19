from .Submember import SubMember
import numpy as np
import math


class Member():
    """
    3D Space Frame Member Object Between Nodes

    REQUIRED PARAMETERS

    node_i: 3D Space Frame Node Object (See Node Class)
    node_j: 3D Space Frame Node Object (See Node Class)

    OPTIONAL PARAMERS

    i_release: False = unpinned, True = pinned
    j_release: False = unpinned, True = pinned
    E: Young's Modulus [ksi]
    I: Moment of Inertia [in^4]
    A: Cross-Sectional Area [in^2]
    G: Shear Modulus [ksi]
    J: Polar Moment of Inertia [in^4]
    mesh: number of discretizations per member
    bracing: 'continuous', 'quarter', 'third', 'midspan', or locations 
    along span as an array: [(l1,l2,...,ln)]

    pointLoads: list of tuples [(orientation, location, mag),...]
    """

    def __init__(
        self,
        nodes,
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
        # default properties are for a W12x14
        self.node_i = node_i
        self.node_j = node_j
        self.i_release = False if i_release == None else i_release
        self.j_release = False if j_release == None else j_release
        self.E = 29000 if E == None else E
        self.Izz = 88.6 if Ixx == None else Ixx
        self.Iyy = 2.36 if Iyy == None else Iyy
        self.A = 4.16 if A == None else A
        self.G = 12000 if G == None else G
        self.J = 0.0704 if J == None else J
        self.mesh = 50 if mesh == None else mesh
        self.bracing = 'continuous' if bracing == None else bracing
        self.shape = 'W12X14' if shape == None else shape
        self.count = 0
        self.submembers = {}
        self.pointLoads = []

        # calculate the member length based on the node coordinates
        self.length = self.calculateMbrLength(node_i, node_j)

        if self.mesh == None:
            self.addSubMember(
                self.node_i,
                self.node_j,
                self.i_release,
                self.j_release,
                self.E,
                self.Ixx,
                self.Iyy,
                self.A,
                self.G,
                self.J
            )

        else:
            for i, node in enumerate(
                self.addMesh(nodes, node_i, node_j, self.mesh, self.length)
            ):
                if i+1 == 1:
                    i = node_i
                    j = node

                    self.addSubMember(
                        i,
                        j,
                        self.i_release,
                        False,
                        self.E,
                        self.Izz,
                        self.Iyy,
                        self.A,
                        self.G,
                        self.J)

                elif i+1 < self.mesh:
                    i = j
                    j = node

                    self.addSubMember(
                        i,
                        j,
                        False,
                        False,
                        self.E,
                        self.Izz,
                        self.Iyy,
                        self.A,
                        self.G,
                        self.J
                    )

                else:
                    i = j
                    j = node_j

                    self.addSubMember(
                        i,
                        j,
                        False,
                        self.j_release,
                        self.E,
                        self.Izz,
                        self.Iyy,
                        self.A,
                        self.G,
                        self.J
                    )

    def calculateMbrLength(self, node_i, node_j):
        # calculate the x, y and z vector components of the member
        dx = node_j.coordinates.x - node_i.coordinates.x
        dy = node_j.coordinates.y - node_i.coordinates.y
        dz = node_j.coordinates.z - node_i.coordinates.z
        # calculate and return the member length
        return (math.sqrt(dx**2 + dy**2 + dz**2))

    def addMesh(self, nodes, node_i, node_j, mesh, l):
        # instantiate an array to hold the mesh nodes
        mesh_nodes = []
        # calculate the x, y and z vector components of the member
        dx = node_j.coordinates.x - node_i.coordinates.x
        dy = node_j.coordinates.y - node_i.coordinates.y
        dz = node_j.coordinates.z - node_i.coordinates.z
        # calculate the member unit vectors
        x_unit = dx/l
        y_unit = dy/l
        z_unit = dz/l
        # add the mesh to the model
        for i in range(mesh):
            # calculate the scalar
            scalar = l/mesh*(i+1)
            # calculate nodal coordinates of mesh point
            x = node_i.coordinates.x + scalar*x_unit
            y = node_i.coordinates.y + scalar*y_unit
            z = node_i.coordinates.z + scalar*z_unit
            # add the mesh coordinates as a node to the model
            mesh_nodes.append(nodes.addNode(x, y, z, mesh_node=True))
        # return a list of the mesh nodes
        return (mesh_nodes)

    def addSubMember(
        self,
        node_i,
        node_j,
        i_release,
        j_release,
        E,
        Ixx,
        Iyy,
        A,
        G,
        J
    ):
        self.count += 1
        submbr = SubMember(
            node_i,
            node_j,
            i_release,
            j_release,
            E,
            Ixx,
            Iyy,
            A,
            G,
            J
        )
        self.submembers[self.count] = submbr

    def calculateCb(self):
        # instantiate an array to hold Cb for each unbraced span
        Cb = []

        def discretize(length, n, l1=0):
            # returns n size array of locations along member span / n
            locations = []
            for i in range(n-1):
                i += 1
                locations.append(l1+i*length/n)
            return (locations)

        def braceCoordinates(bracePoint):
            # calculate the x, y and z vector components of the member
            dx = self.node_j.coordinates.x - self.node_i.coordinates.x
            dy = self.node_j.coordinates.y - self.node_i.coordinates.y
            dz = self.node_j.coordinates.z - self.node_i.coordinates.z
            # calculate the member unit vectors
            x_unit = dx/self.length
            y_unit = dy/self.length
            z_unit = dz/self.length
            # calculate nodal coordinates of brace point
            x = self.node_i.coordinates.x + bracePoint*x_unit
            y = self.node_i.coordinates.y + bracePoint*y_unit
            z = self.node_i.coordinates.z + bracePoint*z_unit
            # return the brace point coordinates
            return (x, y, z)

        if self.bracing == 'quarter':
            bracePoints = discretize(self.length, 4)
        elif self.bracing == 'third':
            bracePoints = discretize(self.length, 3)
        elif self.bracing == 'midspan':
            bracePoints = discretize(self.length, 2)
        else:
            if type(self.bracing) == list:
                pass
            else:
                raise ValueError(
                    "Must be 'quarter','third','midspan' or an array of locations"
                )
            bracePoints = self.bracing

        unbracedSpans = len(bracePoints) + 1

        for i in range(unbracedSpans):

            # determine unbraced span length
            if i == 0:
                l1 = 0
                unbracedLength = bracePoints[i]
            elif i == len(bracePoints):
                l1 = bracePoints[i-1]
                unbracedLength = self.length - l1
            else:
                l1 = bracePoints[i-1]
                unbracedLength = bracePoints[i] - l1

            # determine the the 1/4 point locations along the unbraced span
            quarterPoints = discretize(unbracedLength, 4, l1)

            # instantiate an empty array to hold Mmax
            Mmax = []
            # instantiate an empty array to hold Ma, Mb, and Mc
            M = []

            # determine the nodal coordinates of the quarter points
            for quarterPoint in quarterPoints:
                coordinates = braceCoordinates(quarterPoint)

                for submbr in self.submembers.values():
                    # 1/4 point coordinates
                    x = coordinates[0]
                    y = coordinates[1]
                    z = coordinates[2]
                    # node i coordinates
                    xi = submbr.node_i.coordinates.x
                    yi = submbr.node_i.coordinates.y
                    zi = submbr.node_i.coordinates.z
                    # node j coordinates
                    xj = submbr.node_j.coordinates.x
                    yj = submbr.node_j.coordinates.y
                    zj = submbr.node_j.coordinates.z
                    # determine which submembers the 1/4 point falls between
                    if (xi, yi, zi) <= coordinates <= (xj, yj, zj):
                        # location values for linear interpolation
                        Lp = []
                        Lp.append(0)
                        Lp.append(submbr.length)
                        # moment values for linear interpolation
                        Mp = []
                        Mp.append(submbr.results['major axis moments'][0])
                        Mp.append(-1*submbr.results['major axis moments'][1])
                        # location for moment interpolation
                        dx = x - xi
                        dy = y - yi
                        dz = z - zi
                        L = math.sqrt(dx**2 + dy**2 + dz**2)
                        # interpolate the quarter point moment value
                        M.append(abs(np.interp(L, Lp, Mp)))
                        Mmax.append(max(
                            abs(submbr.results['major axis moments'][0]),
                            abs(submbr.results['major axis moments'][1])
                        ))
                    else:
                        Mmax.append(max(
                            abs(submbr.results['major axis moments'][0]),
                            abs(submbr.results['major axis moments'][1])
                        ))
            # calculate Cb
            Mmax = max(Mmax)
            Ma = M[0]
            Mb = M[1]
            Mc = M[2]
            Cb.append(12.5*Mmax/(2.5*Mmax + 3*Ma + 4*Mb + 3*Mc))

        self.Cb = min(min(Cb), 3)
        return (self.Cb)

    def addPointLoad(self, mag, direction, location):
        # direction in global 'X', 'Y', or 'Z'
        # location in % of span

        location = self.length*(location/100)

        # instantiate a variable measuring distance along member
        l1 = 0

        # acceptable floating point error to consider load at node
        pointError = 1*10**-10

        # iterate through the sub-members
        for n, submbr in self.submembers.items():

            l2 = l1 + submbr.length

            # check if the load lands on the current sub-member
            if l1 <= location <= l2:

                # extract rotation matrix for current submember
                TM = submbr.rotationMatrix[0:3, 0:3]

                # initialize a global force vector
                if direction == 'X':
                    FG = np.array([mag, 0, 0])

                elif direction == 'x':
                    FG = np.array(np.matmul(TM, np.array([mag, 0, 0])))

                elif direction == 'Y':
                    FG = np.array([0, mag, 0])

                elif direction == 'y':
                    FG = np.array(np.matmul(TM, np.array([0, mag, 0])))

                elif direction == 'Z':
                    FG = np.array([0, 0, mag])

                elif direction == 'z':
                    FG = np.array(np.matmul(TM, np.array([0, 0, mag])))

                # check if the load lands on node i of the sub-member
                if l1-pointError < location < l1+pointError:
                    # add the X component of the load
                    submbr.node_i.addLoad(mag=FG[0], lType='v', direction='X')

                    # add the Y component of the load
                    submbr.node_i.addLoad(mag=FG[1], lType='v', direction='Y')

                    # add the Z component of the load
                    submbr.node_i.addLoad(mag=FG[2], lType='v', direction='Z')

                # check if the load lands on node j of the sub-member
                elif l2-pointError < location < l2+pointError:
                    # add the X component of the load
                    submbr.node_j.addLoad(mag=FG[0], lType='v', direction='X')

                    # add the Y component of the load
                    submbr.node_j.addLoad(mag=FG[1], lType='v', direction='Y')

                    # add the Z component of the load
                    submbr.node_j.addLoad(mag=FG[2], lType='v', direction='Z')

                # the load arbitrarily lands somewhere along the sub-member
                else:
                    #         P
                    # o-------|-----o
                    # |<- a ->|<-b->|
                    b = l2 - location
                    a = submbr.length - b

                    # transform the global force vector to local coordinates
                    FL = np.matmul(TM, FG)

                    # extract local axial force
                    axial = FL[0]

                    # extract local shearing force
                    v = FL[1]

                    # extract local transverse force
                    t = FL[2]

                    # calculate equivalent nodal actions
                    if submbr.i_release == True and submbr.j_release == False:
                        # instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([10, 1])

                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b**2 * \
                            (a+2*submbr.length)/(2*submbr.length**3)
                        f_local[2, 0] = t*b**2 * \
                            (a+2*submbr.length)/(2*submbr.length**3)
                        f_local[4, 0] = axial*a/(submbr.length)
                        f_local[5, 0] = v*a * \
                            (3*submbr.length**2-a**2)/(2*submbr.length**3)
                        f_local[6, 0] = t*a * \
                            (3*submbr.length**2-a**2)/(2*submbr.length**3)
                        f_local[8, 0] = t*a*b * \
                            (a+submbr.length)/(2*submbr.length**2)
                        f_local[9, 0] = v*a*b * \
                            (a+submbr.length)/(2*submbr.length**2)

                    elif submbr.i_release == False and submbr.j_release == True:
                        # instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([10, 1])

                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b * \
                            (3*submbr.length**2-b**2)/(2*submbr.length**3)
                        f_local[2, 0] = t*b * \
                            (3*submbr.length**2-b**2)/(2*submbr.length**3)
                        f_local[4, 0] = -t*b*a * \
                            (b+submbr.length)/(2*submbr.length**2)
                        f_local[5, 0] = -v*b*a * \
                            (b+submbr.length)/(2*submbr.length**2)
                        f_local[6, 0] = axial*a/(submbr.length)
                        f_local[7, 0] = v*a**2 * \
                            (b+2*submbr.length)/(2*submbr.length**3)
                        f_local[8, 0] = t*a**2 * \
                            (b+2*submbr.length)/(2*submbr.length**3)

                    else:
                        # instantiate an array to hold equivalent nodal actions
                        f_local = np.zeros([12, 1])

                        # forces at node i
                        f_local[0, 0] = axial*b/(submbr.length)
                        f_local[1, 0] = v*b**2*(3*a+b)/submbr.length**3
                        f_local[2, 0] = t*b**2*(3*a+b)/submbr.length**3
                        f_local[4, 0] = -t*a*b**2/submbr.length**2
                        f_local[5, 0] = -v*a*b**2/submbr.length**2

                        # forces at node j
                        f_local[6, 0] = axial*a/(submbr.length)
                        f_local[7, 0] = v*a**2*(a+3*b)/submbr.length**3
                        f_local[8, 0] = t*a**2*(a+3*b)/submbr.length**3
                        f_local[10, 0] = t*a**2*b/submbr.length**2
                        f_local[11, 0] = v*a**2*b/submbr.length**2

                    # transform the local force vector to global reference plane
                    TM = np.matrix(submbr.rotationMatrix)
                    f_global = TM.I*f_local

                    # add the equivalent nodal forces and moments to each node
                    if submbr.i_release == True and submbr.j_release == False:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_j.Fx += f_global[4, 0]
                        submbr.node_j.Fy += f_global[5, 0]
                        submbr.node_j.Fz += f_global[6, 0]
                        submbr.node_j.Mx += f_global[7, 0]
                        submbr.node_j.My += f_global[8, 0]
                        submbr.node_j.Mz += f_global[9, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_j.eFx += f_global[4, 0]
                        submbr.node_j.eFy += f_global[5, 0]
                        submbr.node_j.eFz += f_global[6, 0]
                        submbr.node_j.eMx += f_global[7, 0]
                        submbr.node_j.eMy += f_global[8, 0]
                        submbr.node_j.eMz += f_global[9, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[4, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[5, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[6, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[8, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[9, 0]

                    elif submbr.i_release == False and submbr.j_release == True:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_i.My += f_global[4, 0]
                        submbr.node_i.Mz += f_global[5, 0]
                        submbr.node_j.Fx += f_global[6, 0]
                        submbr.node_j.Fy += f_global[7, 0]
                        submbr.node_j.Fz += f_global[8, 0]
                        submbr.node_j.Mx += f_global[9, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_i.eMy += f_global[4, 0]
                        submbr.node_i.eMz += f_global[5, 0]
                        submbr.node_j.eFx += f_global[6, 0]
                        submbr.node_j.eFy += f_global[7, 0]
                        submbr.node_j.eFz += f_global[8, 0]
                        submbr.node_j.eMx += f_global[9, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[6, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[7, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[5, 0]

                    else:
                        submbr.node_i.Fx += f_global[0, 0]
                        submbr.node_i.Fy += f_global[1, 0]
                        submbr.node_i.Fz += f_global[2, 0]
                        submbr.node_i.Mx += f_global[3, 0]
                        submbr.node_i.My += f_global[4, 0]
                        submbr.node_i.Mz += f_global[5, 0]
                        submbr.node_j.Fx += f_global[6, 0]
                        submbr.node_j.Fy += f_global[7, 0]
                        submbr.node_j.Fz += f_global[8, 0]
                        submbr.node_j.Mx += f_global[9, 0]
                        submbr.node_j.My += f_global[10, 0]
                        submbr.node_j.Mz += f_global[11, 0]

                        submbr.node_i.eFx += f_global[0, 0]
                        submbr.node_i.eFy += f_global[1, 0]
                        submbr.node_i.eFz += f_global[2, 0]
                        submbr.node_i.eMx += f_global[3, 0]
                        submbr.node_i.eMy += f_global[4, 0]
                        submbr.node_i.eMz += f_global[5, 0]
                        submbr.node_j.eFx += f_global[6, 0]
                        submbr.node_j.eFy += f_global[7, 0]
                        submbr.node_j.eFz += f_global[8, 0]
                        submbr.node_j.eMx += f_global[9, 0]
                        submbr.node_j.eMy += f_global[10, 0]
                        submbr.node_j.eMz += f_global[11, 0]

                        submbr.ENAs['axial'][0] += f_local[0, 0]
                        submbr.ENAs['axial'][1] += f_local[6, 0]
                        submbr.ENAs['shear'][0] += f_local[1, 0]
                        submbr.ENAs['shear'][1] += f_local[7, 0]
                        submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                        submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                        submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                        submbr.ENAs['minor axis moments'][1] += f_local[10, 0]
                        submbr.ENAs['major axis moments'][0] += f_local[5, 0]
                        submbr.ENAs['major axis moments'][1] += f_local[11, 0]

                break

            l1 = l2

    def addTrapLoad(self, Mag1, Mag2, direction, loc1, loc2):
        """
        Add an arbitrary trapezoidal load to the model

        Parameters:
        Mag1:         [float] start magnitude of the distributed load (kips)
        Mag2:         [float] end magnitude of the distributed load (kips)
        direction:     [string] global or local direction of the applied load
        loc1:         [float] start location of the load along member span (%)
        loc2:         [float] end location of the load along member span (%)
        """

        # convert the start and end locations to feet
        loc1 = self.length*(loc1/100)
        loc2 = self.length*(loc2/100)

        # calculate the slope of the trapezoidal load
        m = (Mag2-Mag1)/(loc2-loc1)

        # instantiate a variable to measure distance along member
        l1 = 0

        # iterate through the members submembers
        for n, submbr in self.submembers.items():
            # calculate the end location of current submember
            l2 = l1+submbr.length

            # extract rotation matrix for current submember
            TM = submbr.rotationMatrix[0:3, 0:3]

            if l2 < loc1 or l1 > loc2:
                # the load does not land on the current submember
                # continue to the next iteration
                l1 = l2
                continue

            if l1 <= loc1 and l2 >= loc2:
                # the load is located entirely on the current submember
                w1 = Mag1
                w2 = Mag2
                l = submbr.length
                a = loc1 - l1
                lw = loc2 - loc1
                b = l2 - loc2

            if l1 <= loc1 and l2 <= loc2:
                # the load begins on the current submember
                w1 = Mag1
                w2 = m*(l2-loc1)+Mag1
                l = submbr.length
                a = loc1 - l1
                lw = l2 - loc1
                b = 0

            if l1 >= loc1 and l2 >= loc2:
                # the load ends on the current submember
                w1 = m*(l1-loc1)+Mag1
                w2 = Mag2
                l = submbr.length
                a = 0
                lw = loc2 - l1
                b = l2 - loc2

            if l1 >= loc1 and l2 <= loc2:
                # the load continues over the current submember
                w1 = m*(l1-loc1)+Mag1
                w2 = m*(l2-loc1)+Mag1
                l = submbr.length
                a = 0
                lw = l2 - l1
                b = 0

            # initialize a global force vector
            if direction == 'X':
                FG1 = np.array([w1, 0, 0])
                FG2 = np.array([w2, 0, 0])

            elif direction == 'x':
                FG1 = np.matmul(TM, np.array([w1, 0, 0]))
                FG2 = np.matmul(TM, np.array([w2, 0, 0]))

            elif direction == 'Y':
                FG1 = np.array([0, w1, 0])
                FG2 = np.array([0, w2, 0])

            elif direction == 'y':
                FG1 = np.matmul(TM, np.array([0, w1, 0]))
                FG2 = np.matmul(TM, np.array([0, w2, 0]))

            elif direction == 'Z':
                FG1 = np.array([0, 0, w1])
                FG2 = np.array([0, 0, w2])

            elif direction == 'z':
                FG1 = np.matmul(TM, np.array([0, 0, w1]))
                FG2 = np.matmul(TM, np.array([0, 0, w2]))

            # transform the global force vector to local coordinates
            FL1 = np.matmul(TM, FG1)
            FL2 = np.matmul(TM, FG2)

            # extract local axial force
            a1 = FL1[0]
            a2 = FL2[0]

            # extract local shearing force
            v1 = FL1[1]
            v2 = FL2[1]
            vd = v2 - v1
            vm = (v1+v2)/2

            # extract local transverse force
            t1 = FL1[2]
            t2 = FL2[2]
            td = t2 - t1
            tm = (t1+t2)/2

            if submbr.i_release == False and submbr.j_release == False:
                # instantiate a local force vector
                f_local = np.zeros([12, 1])

                # calculate the geometric constants
                s1 = 10*((l**2+a**2)*(l+a)-(a**2+b**2)*(a-b)-l*b*(l+b)-a**3)
                s2 = lw*(l*(2*l+a+b)-3*(a-b)**2-2*a*b)
                s3 = 120*a*b*(a+lw)+10*lw*(6*a**2+4*l*lw-3*lw**2)
                s4 = 10*l*lw**2-10*lw*a*(l-3*b)-9*lw**3

                # forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[7, 0] = (lw*(s1*vm+s2*vd))/(20*l**3)  # normal shear
                f_local[8, 0] = (lw*(s1*tm+s2*td)) / \
                    (20*l**3)  # transverse shear
                f_local[10, 0] = -(lw*(s3*tm+s4*td)) / \
                    (120*l**2)  # minor axis moment
                f_local[11, 0] = -(lw*(s3*vm+s4*vd)) / \
                    (120*l**2)  # major axis moment

                # forces at node i
                vj = f_local[7, 0]  # normal shear force at node j
                tj = f_local[8, 0]  # transverse shear force at node j
                mj = f_local[10, 0]  # minor axis moment at node j
                Mj = f_local[11, 0]  # major axis moment at node j

                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = lw*vm-vj  # normal shear
                f_local[2, 0] = lw*tm-tj  # transverse shear
                f_local[4, 0] = mj+tj*l-a*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[5, 0] = Mj+vj*l-a*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

            if submbr.i_release == True and submbr.j_release == False:
                s1 = 40*l*(2*l**2-lw**2)+10*lw * \
                    (lw**2-2*b**2)-40*b*(l-a)*(2*l+a)
                s2 = lw*(3*lw**2-10*l*(lw+2*b)+10*b*(b+lw))

                # forces at node i
                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = (lw*(s1*vm+s2*vd))/(80*l**3)  # normal shear
                f_local[2, 0] = (lw*(s1*tm+s2*td)) / \
                    (80*l**3)  # transverse shear
                f_local[4, 0] = 0  # minor axis moment
                f_local[5, 0] = 0  # major axis moment

                # forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[7, 0] = lw*vm-f_local[1, 0]  # normal shear
                f_local[8, 0] = lw*vm-f_local[2, 0]  # transverse shear
                f_local[10, 0] = f_local[8, 0]*l-b*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[11, 0] = f_local[7, 0]*l-b*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

            if submbr.i_release == False and submbr.j_release == True:
                s1 = 40*l*(2*l**2-lw**2)+10*lw * \
                    (lw**2-2*a**2)-40*a*(l-b)*(2*l+b)
                s2 = lw*(3*lw**2-10*l*(lw+2*a)+10*a*(a+lw))

                # forces at node i
                f_local[0, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[1, 0] = (lw*(s1*vm+s2*vd))/(80*l**3)  # normal shear
                f_local[2, 0] = (lw*(s1*tm+s2*td)) / \
                    (80*l**3)  # transverse shear
                f_local[4, 0] = f_local[2, 0]*l-a*lw*tm - \
                    (lw**2*(2*t2+t1))/6  # minor axis moment
                f_local[5, 0] = f_local[1, 0]*l-a*lw*vm - \
                    (lw**2*(2*v2+v1))/6  # major axis moment

                # forces at node j
                f_local[6, 0] = (a1+a2)*submbr.length/2  # axial
                f_local[7, 0] = lw*vm-f_local[1, 0]  # normal shear
                f_local[8, 0] = lw*vm-f_local[2, 0]  # transverse shear
                f_local[10, 0] = 0  # minor axis moment
                f_local[11, 0] = 0  # major axis moment

            # transform the local force vector to global reference plane
            TM = np.matrix(submbr.rotationMatrix)
            f_global = TM.I*f_local

            # add the equivalent nodal forces and moments to each node
            if submbr.i_release == True and submbr.j_release == False:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_j.Fx += f_global[4, 0]
                submbr.node_j.Fy += f_global[5, 0]
                submbr.node_j.Fz += f_global[6, 0]
                submbr.node_j.Mx += f_global[7, 0]
                submbr.node_j.My += f_global[8, 0]
                submbr.node_j.Mz += f_global[9, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_j.eFx += f_global[4, 0]
                submbr.node_j.eFy += f_global[5, 0]
                submbr.node_j.eFz += f_global[6, 0]
                submbr.node_j.eMx += f_global[7, 0]
                submbr.node_j.eMy += f_global[8, 0]
                submbr.node_j.eMz += f_global[9, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[4, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[5, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[6, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[8, 0]
                submbr.ENAs['major axis moments'][1] += f_local[9, 0]

            elif submbr.i_release == False and submbr.j_release == True:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_i.My += f_global[4, 0]
                submbr.node_i.Mz += f_global[5, 0]
                submbr.node_j.Fx += f_global[6, 0]
                submbr.node_j.Fy += f_global[7, 0]
                submbr.node_j.Fz += f_global[8, 0]
                submbr.node_j.Mx += f_global[9, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_i.eMy += f_global[4, 0]
                submbr.node_i.eMz += f_global[5, 0]
                submbr.node_j.eFx += f_global[6, 0]
                submbr.node_j.eFy += f_global[7, 0]
                submbr.node_j.eFz += f_global[8, 0]
                submbr.node_j.eMx += f_global[9, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[6, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[7, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                submbr.ENAs['major axis moments'][1] += f_local[5, 0]

            else:
                submbr.node_i.Fx += f_global[0, 0]
                submbr.node_i.Fy += f_global[1, 0]
                submbr.node_i.Fz += f_global[2, 0]
                submbr.node_i.Mx += f_global[3, 0]
                submbr.node_i.My += f_global[4, 0]
                submbr.node_i.Mz += f_global[5, 0]
                submbr.node_j.Fx += f_global[6, 0]
                submbr.node_j.Fy += f_global[7, 0]
                submbr.node_j.Fz += f_global[8, 0]
                submbr.node_j.Mx += f_global[9, 0]
                submbr.node_j.My += f_global[10, 0]
                submbr.node_j.Mz += f_global[11, 0]

                submbr.node_i.eFx += f_global[0, 0]
                submbr.node_i.eFy += f_global[1, 0]
                submbr.node_i.eFz += f_global[2, 0]
                submbr.node_i.eMx += f_global[3, 0]
                submbr.node_i.eMy += f_global[4, 0]
                submbr.node_i.eMz += f_global[5, 0]
                submbr.node_j.eFx += f_global[6, 0]
                submbr.node_j.eFy += f_global[7, 0]
                submbr.node_j.eFz += f_global[8, 0]
                submbr.node_j.eMx += f_global[9, 0]
                submbr.node_j.eMy += f_global[10, 0]
                submbr.node_j.eMz += f_global[11, 0]

                submbr.ENAs['axial'][0] += f_local[0, 0]
                submbr.ENAs['axial'][1] += f_local[6, 0]
                submbr.ENAs['shear'][0] += f_local[1, 0]
                submbr.ENAs['shear'][1] += f_local[7, 0]
                submbr.ENAs['transverse shear'][0] += f_local[2, 0]
                submbr.ENAs['transverse shear'][1] += f_local[8, 0]
                submbr.ENAs['minor axis moments'][0] += f_local[4, 0]
                submbr.ENAs['minor axis moments'][1] += f_local[10, 0]
                submbr.ENAs['major axis moments'][0] += f_local[5, 0]
                submbr.ENAs['major axis moments'][1] += f_local[11, 0]

            l1 = l2

    def secondOrder(self):
        for submbr in self.submembers.values():
            # calculate the submember local geometric stiffness matrix
            KG = submbr.calculateKG()

            # redefine the submember local stiffness matrix
            submbr.Kl += KG

            # calculate the submember global geometric stiffness matrix
            submbr.KG = submbr.TM.T.dot(submbr.Kl).dot(submbr.TM)
