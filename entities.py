from abc import ABC, abstractmethod
import logging
import math
from enum import Enum

if __name__ == "__main__":
    from field import Field, Cell



class EntityException(Exception):
    pass

logger = logging.getLogger(__name__)

class Entity(ABC):

    _counter = 0 # used to implement id for included entity

    def __init__(self):
        self.anchor = None # (y, x) - coords tuple
        self.cells_occupied = [] # list of cell instances
        self.rotation = None # is 0, 1, 2, 3
        self.size = 1

        self.eid = Entity._counter
        Entity._counter += 1

    @staticmethod
    def rotation_manage(rotation):
        rotation = (rotation + 4) % 4
        dydx = [
            (0,1), # rotation counterclockwise
            (1,0), # because (0,0) left upper corner - inverted square coords
            (0,-1), # computing same with sin/cos will
            (-1,0) # return same values, but this one more stable
        ]
        return (dydx[rotation], rotation)
    
    def update_state(self, anchor_coords: tuple, occupied_cells: list, rotation: int):
        self.anchor = anchor_coords
        self.cells_occupied = occupied_cells
        self.rotation = rotation
        logger.info(f"{self} state updated")


class ShipStatus(Enum):
    NOTPLACED = 0
    FULLHEALTH = 1
    DAMAGED = 2
    DESTROYED = 3
    REMOVED = 4
class ShipType(Enum):
    CORVETTE = 1
    FRIGATE = 2
    DESTROYER = 3
    CRUISER = 4
    BATTLESHIP = 5

class Ship(Entity):

    def __init__(self, size, *, status = ShipStatus.NOTPLACED):
        super().__init__()
        self.size = size
        self.status = status
        self.type = ShipType(size)
        self.damage = [] # cells which have damage where 0 is anchor

        logger.info(f"{self} created")
    

    def reserve_coords(self, anchor_coords: tuple, rotation: int):

        dydx, rotation = Entity.rotation_manage(rotation)
        y0, x0 = anchor_coords
        # note it returns calculated list of coords AND angle!
        # i chose dict with goal not to strulle with which index is what
        return {"coords": [((y0+i*dydx[0]), (x0+i*dydx[1])) for i in range(self.size)], "rotation": rotation}


    def __repr__(self):
        return f"{self.type} {self.eid} {self.status}, a:{self.anchor} r:{self.rotation}"


class Space_Object(Entity):
    pass

class Construction(Entity):
    pass