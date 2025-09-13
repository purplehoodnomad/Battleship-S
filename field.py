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
            


    def generate_square(self, height: int, width: int):
        cell_id = 0

        for y in range(width):
            for x in range(height):

                self.cells[(y, x)] = Cell(y, x)
                logger.info(f"Cell ({y},{x}) is generated")
                cell_id += 1


class Cell:
    def __init__(self, y: int, x: int, *, isPlayfield = True):
        self.y, self.x = y, x
        self.isPlayfield = isPlayfield
        self.isOccupied = False