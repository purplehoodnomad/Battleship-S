import logging

logger = logging.getLogger(__name__)

class FieldException(Exception):
    pass

# this method used for not to doubling log and throwing exception then
def raise_logged(e: Exception): 
    logger.error(str(e))
    raise e

class Field:
    def __init__(self):
        self._cells = {}
    
    @property
    def is_empty(self): return not self._cells

    def wipe_field(self): self._cells = {}

    def cell_exists(self, coords: tuple): return bool(coords) and coords in self._cells
    

    def generate_field(self, params: list) -> None: # gets list of generation parameters, first is always pattern name
        match params[0]:

            case "square": return self.generate_square(params[1], params[2])
            case _:
                raise FieldException(f"No {params[0]} shaped field implemented.")
    
    def get_cells(self, coords):
        """
        This method can take both (y, x) and list of coordinates.
        It throws an error either of coordinates in list in not existing
        """
        if self.is_empty:
            logger.warning("Tried to get cell with no field")
            return None
        
        if not coords:
            raise_logged(FieldException("Asked for no cells."))
        
        if isinstance(coords, tuple) and self.cell_exists(coords): return self._cells[coords]

        elif isinstance(coords, list):
            output = []

            for element in coords:

                if not (isinstance(element, tuple) and self.cell_exists(element)):
                    raise_logged(FieldException(f"Requested Cell {element} does not exist"))

                else: element = self._cells[element]
                output.append(element)

            return output
        
        raise_logged(FieldException(f"Requested Cell {coords} does not exist"))


    def generate_square(self, height: int, width: int):
        cell_id = 0

        for y in range(height):
            for x in range(width):

                self._cells[(y, x)] = Cell(y, x)
                logger.debug(f"{self._cells[(y, x)]} - is generated.")
                cell_id += 1


class Cell:
    def __init__(self, y: int, x: int, *, is_void = False):
        if not(isinstance(y, int) and isinstance(x, int)): raise TypeError("Coordinates must be integers.")
        self.y, self.x = y, x
        self.is_void = is_void
        self.is_occupied = False
        self.occupied_by = None
    
    def __str__(self):
        if self.is_void: return f"Void ({self.y},{self.x})"
        return f"Cell ({self.y},{self.x}) occupied by {self.occupied_by}"
    
    def __repr__(self):
        return f"Cell(y={self.y}, x={self.x}, is_void={self.is_void}, is_occupied={self.is_occupied}, occupied_by={self.occupied_by})"


    def clear(self):
        self.is_occupied = False
        self.occupied_by = None