from __future__ import annotations
import logging


logger = logging.getLogger(__name__)


class FieldException(Exception): pass
class Field:
    """
    Generates playfield, manages it.
    Every shape is a rectangle where void cells form given shape.
    Field - only source of truth
    """
    def __init__(self, shape = None, params = None):
        # field - is a dict of cells
        # where key is their (y, x) tuple
        self._cells = {}
        self.dimensions = {"height": -1, "width": -1}
        if shape is not None or params is not None: self.generate_field(shape, params)


    def is_empty(self) -> bool:
        return not self._cells

    def wipe_field(self) -> None:
        self._cells = {}
        self.dimensions = {"height": -1, "width": -1}
        logger.info(f"{self} wiped")

    # checks if cell with given (y, x) is part of field
    def cell_exists(self, coords: tuple) -> bool:
        return bool(coords) and coords in self._cells
    

    def generate_field(self, shape: str, params: list) -> None:
        """
        Gets list of shape and generation parameters (width, height, radius etc.)
        This is separate method and not constructor because
        field can be regenerated multiple times without recreating the object itself.
        """
        self.wipe_field()
        
        if shape is None: (f"{self}: None can't be shape")
        match shape:
            case "rectangle":
                if len(params) < 2: raise FieldException(f"{self}: No proper rectangle dimensions given.")
                height, width = int(params[0]), int(params[1])
                return self.generate_rectangle(height, width)
            case _:
                raise FieldException(f"{self}: no {shape} shape supported")

    def generate_rectangle(self, height: int, width: int) -> None:
        allowed_sizes = list(range(1, 27)) # corresponds A-Z
        if width not in allowed_sizes or height not in allowed_sizes: raise FieldException(f"{self}: Dimensions must be between 1 and 26")
        
        self.dimensions = {"height": height, "width": width}
        for y in range(height):
            for x in range(width):
                self._cells[(y, x)] = Cell(y, x)
        logger.info(f"{self} generated")


    def get_cell(self, coords: tuple) -> Cell:
        """
        This method only returns cell instance by given (y, x) if it part of the field.
        It can return void cell and returns no cell if field is empty.
        It's made to separate responsibility - it just gives what it can.
        """
        if self.is_empty():
            logger.warning(f"{self}: Tried to get cell with no field.")
            return
        if not coords: raise FieldException(f"{self}: Asked for no cells.")
        
        try: return self._cells[coords]
        except KeyError: raise FieldException(f"{self}: Requested Cell {coords} does not exist.")
    

    def occupy_cells(self, entity, anchor_coords: tuple, rotation: int) -> None:
        """
        Takes entity and tries to place it correspondingly given (y, x) and rotation values.
        Raises FieldException if can't by any reason.
        If can place - it clears previously taken cells, writes information in new ones
        and forces entity self update with given position.
        """
        if entity is None: raise FieldException(f"{self}: entity can't be None.")
        if anchor_coords is None: raise FieldException(f"{self}: anchor_coords can't be None.")

        # asks which cells entity wants to take depending on it's properties
        # recieves list of (y,x) and correct rotation (e.g.  rot = 5  -->  rot = 1)
        reserved_coords, rotation = entity.reserve_coords(anchor_coords, rotation).values()
        available_cells = []

        close_cells = self.neighbours(reserved_coords)
        if close_cells is not None:
            for coords in close_cells:
                cell = self.get_cell(coords)
                if cell.occupied_by is not None: raise FieldException(f"{self}: {cell} too close to {cell.occupied_by}")

        for coords in reserved_coords:
            cell = self.get_cell(coords)
            if cell.is_void: raise FieldException(f"{self}: {cell} is void.")
            elif cell.occupied_by is not None: raise FieldException(f"{self}: {cell} is already occupied by {cell.occupied_by}")
            available_cells.append(cell)
        
        for coords in entity.cells_occupied:
            self.get_cell(coords).free()
        for cell in available_cells:
            cell.occupied_by = entity
            logger.debug(f"{self}: {cell} state updated.")
        # entity has only right to update it's inner links for convenience
        entity.update_state(anchor_coords = anchor_coords, occupied_cells = reserved_coords, rotation = rotation, status = 1)


    def neighbours(self, coord_list: list) -> set:
            """
            Returns all potential coordinates of cells near the entity
            """
            if coord_list is None or not isinstance(coord_list, list): raise FieldException(f"{self} requires proper (y, x) list")
            
            neighbours = set()
            for y, x in coord_list:
                for dy, dx in [ (-1,-1), (-1,0), (-1,1),
                                (0,-1),          (0,1),
                                (1,-1),  (1,0),  (1,1)]:
                    
                    coords = (y + dy, x + dx)
                    if coords not in coord_list and coords in self._cells: neighbours.add(coords)
            return neighbours
    
    
    # ЕЩЕ НЕ ОПРОБОВАНО
    def take_shot(self, coords) -> str:
        """
        Returns result of attempt: miss, hit or destroyed
        If ship is destroyed - makes all nearby cells was_shot = True
        This provides instant update to the field
        """
        cell = self.get_cell(coords)
        if cell.is_void or cell.was_shot: raise FieldException(f"{self}: {coords} is not valid target")
        
        if cell.occupied_by is None:
            cell.was_shot = True
            logger.info(f"{self}: {cell} was shot")
            return "miss"
        
        cell.was_shot = True
        occupator = cell.occupied_by
        occupator.make_damage(coords)
        if occupator.status.value == 3: # 3 = Entity.Type.DESTROYED
            # filling all nearby as was_shot
            for close_coords in self.neighbours(occupator.cells_occupied):
                self.get_cell(close_coords).was_shot = True
                logger.info(f"{self}: {close_coords} marked as shot")
            return "destroyed"
        logger.info(f"{self}: {cell} was shot")
        return "hit"
        

    def __iter__(self):
        return iter(self._cells.keys())

    def __repr__(self):
        return f"Field({self.dimensions['height']}, {self.dimensions['width']})"



class Cell:
    """
    Smallest field unit.
    Void - are structural cells.
    Every cell has link to entity it belongs to. Entity itself decides which of cell is what part.
    """
    def __init__(self, y: int, x: int, *, is_void = False):
        if not(isinstance(y, int) and isinstance(x, int)): raise TypeError("Cell coordinates must be integers")
        self.y, self.x = y, x
        self.is_void = is_void
        self.was_shot = False
        self.occupied_by = None
    
    def __str__(self):
        if self.is_void:
            return f"void({self.y},{self.x})"
        
        if self.occupied_by is None:
            state = "o" if self.was_shot else "."
        else:
            state = "x" if self.was_shot else "■"
            
        return f"cell({self.y},{self.x},{state})"
    
    def __repr__(self):
        return f"Cell({self.y},{self.x}) is_void={self.is_void}, was_shot={self.was_shot})"

    def free(self):
        self.occupied_by = None
        logger.debug(f"{self} state updated.")