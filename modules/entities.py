from __future__ import annotations
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class EntityException(Exception): pass
class Entity:
    class Status(Enum):
        NOTPLACED = 0
        FULLHEALTH = 1
        DAMAGED = 2
        DESTROYED = 3
    class Type(Enum):
        UNIDENTIFIED = 0
        CORVETTE = 1
        FRIGATE = 2
        DESTROYER = 3
        CRUISER = 4
        # BATTLESHIP = 5
        # RELAY = 11
        # PLANET = 21

    _counter = 0 # used to implement entity ids
    def __init__(self):
        # geometry and positioning
        self.anchor: tuple = None # (y, x)
        self.size = 1
        self.rotation: int = None # 0, 1, 2, 3
        # reference attributes
        self.cells_occupied = [] # list of cell coords
        self.cells_damaged = set() # cells which have damage where 0 is anchor

        # state and identification
        self.type = self.Type.UNIDENTIFIED
        self.status = self.Status.NOTPLACED
        # metadata
        self.eid = Entity._counter
        Entity._counter += 1


    def update_state(self, *, anchor_coords: tuple, occupied_cells: list, rotation: int, status: int) -> None:
        """
        Syncronizes self state with data given by Field
        Updates only given parameters
        """
        if anchor_coords is not None: self.anchor = anchor_coords
        if occupied_cells is not None: self.cells_occupied = occupied_cells
        if rotation is not None: self.rotation = rotation
        if status is not None: self.status = self.Status(status)
        logger.info(f"{self} state updated")


    def make_damage(self, coords: tuple) -> None:
        # Field desided that there's entity so cells_occupied MUST contain coords
        damaged_tile = self.cells_occupied.index(coords)
        self.cells_damaged.add(damaged_tile)

        if self.size == len(self.cells_damaged): self.status = self.Status.DESTROYED
        else: self.status = self.Status.DAMAGED
        logger.debug(f"{self} state changed")


    @staticmethod
    def rotation_manage(rotation) -> tuple:
        """
        Rotation is counterclockwise because (0,0) is a left upper corner of the field - inverted square coords
        Computing same with sin/cos would result same values, but this one more stable
        """
        rotation = (rotation + 4) % 4
        dydx = [
            (0,1),  # right
            (1,0),  # down
            (0,-1), # left
            (-1,0)  # up
        ]
        return (dydx[rotation], rotation)



class Ship(Entity):
    """
    Main entity in the game
    Can be placed next to the wfield border
    Can't be placed next to other ships
    """
    def __init__(self, size: int):
        super().__init__()
        self.size = size
        self.type = Entity.Type(size)
        logger.info(f"{self} created")

    def reserve_coords(self, anchor_coords: tuple, rotation: int) -> dict:

        dydx, rotation = Entity.rotation_manage(rotation)
        y0, x0 = anchor_coords
        # note that returns calculated list of coords AND angle!
        # dcit was chosen with goal not to struggle with which index is what
        return {"coords": [((y0 + i*dydx[0]), (x0 + i*dydx[1])) for i in range(self.size)], "rotation": rotation}

    def __str__(self):
        type_name = str(self.type).replace('Type.', '').capitalize()
        return f"{type_name}-{self.eid}"

    def __repr__(self):
        return f"eid={self.eid} {self.type} {self.status}, a={self.anchor} r={self.rotation}"


class Space_Object(Entity):
    pass

class Construction(Entity):
    pass