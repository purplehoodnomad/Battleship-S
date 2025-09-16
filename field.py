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
    """
    Generates playfield, manages it.
    Every shape is a rectangle where
    void cells form given shape.

    This class - source of truth of cells' status.
    """
    def __init__(self):
        # field - is a dict of cells
        # where key is their (y, x) tuple
        self._cells = {}
        self.dimensions = {"height": None, "width": None}
    

    @property
    def is_empty(self): return not self._cells


    def wipe_field(self):
        self._cells = {}
        self.dimensions = {"height": None, "width": None}
        logger.info(f"{self} wiped.")


    # checks if cell with given (y, x) is part of field
    def cell_exists(self, coords: tuple): return bool(coords) and coords in self._cells
    

    def generate_field(self, params: list) -> None:
        """
        Gets list of generation parameters, first is always pattern name.
        All the others are generational parameters. e.g. circle radius.
        This is separate method and not constructor because
        field can be regenerated multiple times without recreating the object itself.
        """
        match params[0]:

            case "square": return self.generate_square(params[1], params[2])
            case _:
                raise FieldException(f"{self}: No {params[0]} shaped field implemented.")
    


    def get_cell(self, coords: tuple):
        """
        This method only returns cell instance by given (y, x) if it part of the field.
        It can return void cell and returns no cell if field is empty.
        It's made to separate responsibility - it just gives what it can.
        """
        if self.is_empty:
            logger.warning(f"{self}: Tried to get cell with no field.")
            return None
        if not coords:
            raise_logged(FieldException(f"{self}: Asked for no cells."))
        
        if self.cell_exists(coords): return self._cells[coords]
        raise_logged(FieldException(f"{self}: Requested Cell {coords} does not exist."))


    def generate_square(self, height: int, width: int):
        self.dimensions = {"height": height-1, "width": width-1}
        for y in range(height):
            for x in range(width):
                # there's no point in creating add_cell() since it's only used in this generator
                # that's why it's changing _cells directly
                self._cells[(y, x)] = Cell(y, x)
                logger.debug(f"{self}: {self.get_cell((y, x))} - is generated.")
    

    def occupy_cells(self, entity, anchor_coords: tuple, rotation: int):
        """
        Takes entity and tries to place it correspondingly given (y, x) and rotation values.
        Raises FieldException if can't by any reason.
        If can place - it clears previously taken cells, writes information in new ones
        and forces entity self update with given position.
        """
        if entity is None or anchor_coords is None:
            raise FieldException("Entity or anchor_coords can't be None.")

        # asks which cells entity wants to take depending on it's properties
        # recieves list of (y,x) and correct rotation (e.g. 5 -> 1)
        reserved_coords, rotation = entity.reserve_coords(anchor_coords, rotation).values()
        available_cells = []

        for coords in reserved_coords:
            cell = self.get_cell(coords)
            if cell.is_void: raise FieldException(f"{self}: {cell} is void.")
            elif cell.occupied_by is not None: raise FieldException(f"{cell} is already occupied: {cell.occupied_by}")
            available_cells.append(cell)
        
        for c in entity.cells_occupied:
            c.free()
        for cell in available_cells:
            cell.occupied_by = entity
            logger.info(f"{self}: {cell} state updated.")
        # entity has only right to update it's inner links for convenience
        entity.update_state(anchor_coords, available_cells, rotation)
    
    # placeholder - change later
    def __repr__(self):
        return "FIELDNAME"

        
            



class Cell:
    """
    Smallest field unit.
    Void - are structural cells. Reason - consistent indexing cells with any generation.
    Every cell has link to entity it belongs to. Entity itself decides which of cell is what part.
    """
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