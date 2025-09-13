from abc import ABC, abstractmethod
import logging
import field as f
import math
from enum import Enum

class EntityException(Exception):
    pass

logger = logging.getLogger(__name__)

class Entity(ABC):
    def __init__(self):

        self.isPlaced = False
        self.x = None
        self.y = None
    
    @abstractmethod
    def set_entity(self, x, y):
        pass


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

    _count = 0


    def __init__(self, size, *, status = ShipStatus.NOTPLACED):
        super().__init__()

        self.rotation = None # can take 0 = right, 1 = up, 2 = left, 3 = down, note that (-1 == 3, 4 == 0)
        self.anchor = None # (y, x)
        self.size = size
        self.type = ShipType(size)
        self.cells_occupied = [] # list of [(x1,y1), (x2,y2)...]
        self.damage = [] # cells which have damage

        self.status = status
        self.ship_id = Ship._count
        Ship._count += 1

        logger.info(f"{self} created")


    def set_entity(self, playfield: f.Field, coords: tuple, rotation: int):

        if playfield.cells[coords].isOccupied:
            logger.error(f"Tried to place {self} on ocuppied Cell{coords}")
        
        occupation_cells = self.get_shipTiles(coords, rotation)
        
        for cell in occupation_cells:

            if playfield.cell_exists(playfield, cell):
                tile = playfield.cells[cell]
                
                if tile.isOccupied:
                    msg = f"Tried to place {self} on ocuppied {tile}"
                    logger.error(msg)
                    raise EntityException(msg)
                
                elif tile.isVoid:
                    msg = f"Tried to place {self} on void {tile}"
                    logger.error(msg)
                    raise EntityException(msg)
                
                self.anchor = occupation_cells[0]
                self.rotation = rotation
                self.cells_occupied = occupation_cells

                for cell in occupation_cells:
                    tile = playfield.cells[cell]
                    tile.isOccupied = True
                    tile.occupiedBy = self
                return
            return EntityException(f"Couldn't place {self} on {coords}")


    def get_shipTiles(self, ref_anchor: tuple, ref_angle: int):
        # reference parameters, can be differ from self ones already stored
        position = [ref_anchor]

        for i in range(1, self.size):
            y = ref_anchor[0] + i*round(math.sin(ref_angle * math.pi/2)) # y + dy
            x = ref_anchor[1] + i*round(math.cos(ref_angle * math.pi/2)) # x + dx
            position.append((y, x))
        return position


    def __str__(self):
        return f"{self.type} {self.ship_id} {self.cells_occupied}"



class Space_Object(Entity):
    pass

class Construction(Entity):
    pass