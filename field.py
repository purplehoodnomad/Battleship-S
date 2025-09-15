import logging
if __name__ == "__main__":
    from entities import Entity

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

    def wipe_field(self):
        self._cells = {}
        logger.info(f"{self} wiped.")

    def cell_exists(self, coords: tuple): return bool(coords) and coords in self._cells
    

    def generate_field(self, params: list) -> None: # gets list of generation parameters, first is always pattern name
        match params[0]:

            case "square": return self.generate_square(params[1], params[2])
            case _:
                raise FieldException(f"{self}: No {params[0]} shaped field implemented.")
    
    def get_cell(self, coords):
        if self.is_empty:
            logger.warning(f"{self}: Tried to get cell with no field.")
            return None
        
        if not coords:
            raise_logged(FieldException(f"{self}: Asked for no cells."))
        
        if self.cell_exists(coords): return self._cells[coords]

        raise_logged(FieldException(f"{self}: Requested Cell {coords} does not exist."))


    def generate_square(self, height: int, width: int):
        cell_id = 0

        for y in range(height):
            for x in range(width):

                self._cells[(y, x)] = Cell(y, x)
                logger.debug(f"{self}: {self.get_cell((y, x))} - is generated.")
                cell_id += 1
    
    def occupy_cells(self, entity, anchor_coords: tuple, rotation: int):
        
        reserved_coords, rotation = entity.reserve_coords(anchor_coords, rotation).values()
        available_cells = []

        for coords in reserved_coords:
            cell = self.get_cell(coords)

            if cell.is_void: raise FieldException(f"{self}: {cell} is void.")
            elif cell.occupied_by is not None: raise FieldException(f"{cell} is already occupied: {cell.occupied_by}")
            available_cells.append(cell)
        
        # if didn't get any exceptions - empty previously taken cells
        # this does field since it's source of truth
        for c in entity.cells_occupied:
            c.free()
        for cell in available_cells:
            cell.occupied_by = entity
            logger.info(f"{self}: {cell} state updated.")
        # entity has only right to update it's inner links for convenience
        entity.update_state(anchor_coords, available_cells, rotation)
    
    def __repr__(self):
        return "FIELDNAME"

        
            



class Cell:
    def __init__(self, y: int, x: int, *, is_void = False):
        if not(isinstance(y, int) and isinstance(x, int)): raise TypeError("Coordinates must be integers.")
        self.y, self.x = y, x
        self.is_void = is_void
        self.occupied_by = None
    
    def __str__(self):
        if self.is_void: return f"Void ({self.y},{self.x})"
        return f"Cell ({self.y},{self.x})"
    
    def __repr__(self):
        return f"Cell(y={self.y}, x={self.x}, is_void={self.is_void}, occupied_by={self.occupied_by})"


    def free(self):
        self.occupied_by = None
        logger.info(f"{self} state updated.")