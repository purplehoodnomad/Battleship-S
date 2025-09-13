from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class FieldException(Exception):
    pass


class Field(ABC):
    def __init__(self):
        self.cells = {}


    def generate_field(self, params: list): # gets list of generation parameters, params[0] is always pattern name
        match params[0]:

            case "square": return self.generate_square(params[1], params[2])
            case _:
                raise FieldException(f"No {params[0]} shaped field implemented.")
            

    def cell_exists(self, coords = None, cel_list = None):
        # this method can take both list of cells and single cell
        if not self.cells:
            logger.warning("Tried to check cell existance with no field.")
            return False
        
        if coords is not None: return coords in self.cells
        if cel_list is not None:
            return all(c in self.cells for c in cel_list)
        return False




    def generate_square(self, height: int, width: int):
        cell_id = 0

        for y in range(width):
            for x in range(height):

                self.cells[(y, x)] = Cell(y, x)
                logger.info(f"{self.cells[(y, x)]} - is generated")
                cell_id += 1


class Cell:
    def __init__(self, y: int, x: int, *, isVoid = False):
        self.y, self.x = y, x
        self.isVoid = isVoid
        self.isOccupied = False
        self.occupiedBy = None
    
    def __str__(self):
        if self.isVoid: return f"Void ({self.x},{self.y})"
        return f"Cell ({self.x},{self.y}) occupied by {self.occupiedBy}"