from abc import ABC, abstractmethod
import logging
import field as f
import math

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


class Ship(Entity):

    status = {
    0: "Not Placed",
    1: "Full Health",
    2: "Damaged",
    3: "Destroyed",
    4: "Removed"
    }

    type = {
        1: "Corvette",
        2: "Frigate",
        3: "Destroyer",
        4: "Cruiser",
        99: "Battleship"
    }

    _count = 0


    def __init__(self, size, *, status = 0):
        super().__init__()

        self.rotation = None # can take 0 = right, 1 = down, 2 = left, 3 = up, note that (-1 == 3, 4 == 0)
        self.anchor = None # (y, x)
        self.size = size
        self.cells_occupied = [] # list of [(x1,y1), (x2,y2)...]
        self.damage = [] # cells which have damage

        self.status = status
        self.ship_id = Ship._count
        Ship._count += 1

        logger.info(f"{Ship.type[size]} id:{self.ship_id} size of {size} created")


    def set_entity(self, playfield: f.Field, coords: tuple, rotation: int):

        if playfield.cells[coords].isOccupied:
            logger.exception(f"Tried to place {self.ship_id} on ocuppied Cell{coords}")
            raise EntityException(f"Cell {coords} is already ocuppied.")
        
        print(self.get_shipTiles(coords, rotation))


    def get_shipTiles(self, ref_anchor: tuple, ref_angle: int):
        # reference parameters, can be differ from self ones alaready stored
        position = [ref_anchor]

        for i in range(1, self.size):
            y = ref_anchor[0] + round(math.sin(ref_angle * math.pi/2))
            x = ref_anchor[1] + round(math.cos(ref_angle * math.pi/2))
            position.append((x, y))
        
        return position


    def __str__(self):
        return str(self.ship_id)



class Space_Object(Entity):
    pass

class Construction(Entity):
    pass