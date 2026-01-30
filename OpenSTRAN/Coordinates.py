from numpy import array

from dataclasses import dataclass, field, asdict

from typing import Self, Any


@dataclass(slots=True)
class Coordinate():
    """
    A class representing a 3D coordinate in space.

    Attributes:
        x (float): The x-coordinate in feet.
        y (float): The y-coordinate in feet.
        z (float): The z-coordinate in feet.
        coordinates (tuple[float, float, float]): A tuple containing the (x, y, z) coordinates.
        vector (numpy.ndarray): A numpy array representation of the coordinate vector.
    """
    x: float
    y: float
    z: float
    coordinates: tuple[float, float, float] = field(init=False)
    vector: object = field(init=False)

    def __post_init__(self):
        """
        Post-initialization method to compute and set the coordinates tuple and vector array.
        """
        self.coordinates = (self.x, self.y, self.z)
        self.vector = array([self.x, self.y, self.z])

    def properties(self) -> dict[str, Any]:
        """
        Return the dataclass properties as a dictionary.

        Returns:
            Dict[str, Any]: Dictionary of this instance's fields.
        """
        return asdict(self)

    @classmethod
    def from_tuple(cls, coordinates: tuple[float, float, float]) -> Self:
        """
        Create a `Coordinate` instance from a tuple of x, y, z values.

        :param coordinates: A tuple containing (x, y, z) coordinate values.
        :type coordinates: tuple[float, float, float]

        :returns: A new `Coordinate` instance.
        :rtype: Self
        """
        x = coordinates[0]
        y = coordinates[1]
        z = coordinates[2]
        return cls(x, y, z)
