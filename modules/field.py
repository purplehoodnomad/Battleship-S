from __future__ import annotations
import logging
from modules.enums_and_events import CellStatus, EntityType, EntityStatus, FieldException, circle_coords, ngon_coords, convert_input, invert_output


logger = logging.getLogger(__name__)


class Field:
    """
    Generates playfield, manages it.
    Every shape is a rectangle where void cells form given shape.
    Field - only source of truth
    """
    def __init__(self, shape = None, params = None, /, name = "Unknown"):
        self.name = str(name)
        # field - is a dict of cells
        # where key is their (y, x) tuple
        self._cells = {}
        self.dimensions = {"height": 0, "width": 0}
        self.shape = "empty"
        if shape is not None or params is not None:
            self.generate_field(shape, params)

    @property
    def useful_cells_coords(self) -> list[tuple[int, int]]:
        """
        Returns list of all non-void cells.
        Optimizes data transfering by removing useless information.
        """
        return [coords for coords, cell in self._cells.items() if not cell.is_void]


    def is_empty(self) -> bool:
        return not self._cells

    def wipe_field(self) -> None:
        self._cells = {}
        self.shape = "empty"
        self.dimensions = {"height": 0, "width": 0}
        logger.info(f"{self} wiped")


    def cell_exists(self, coords: tuple[int, int]) -> bool:
        """
        Checks if cell with given (y, x) is part of field
        """
        if coords is None: return False
        return coords in self._cells
    

    def generate_field(self, shape: str|int, params: list[int]) -> None:
        """
        Gets list of shape and generation parameters (width, height, radius etc.)
        This is separate method and not constructor because
        field can be regenerated multiple times without recreating the object itself.
        """
        self.wipe_field()
        
        if shape is None: raise FieldException(f"{self}: None can't be shape")
        match shape:
            case "rectangle"|"1"|1:
                if len(params) < 2: raise FieldException(f"{self}: No proper rectangle dimensions given")
                height, width = int(params[0]), int(params[1])
                self.generate_rectangle(height, width)
                self.shape = "rectangle"
            
            case "circle"|"2"|2:
                if len(params) < 1: raise FieldException(f"{self}: No proper circle radius given")
                radius = int(params[0])
                self.generate_circle(radius)
                self.shape = "circle"
            
            case "triangle"|"3"|3:
                if len(params) < 1: raise FieldException(f"{self}: No proper triangle size given")
                radius = int(params[0])
                try:
                    angle = float(params[1])
                except IndexError:
                    angle = 0
                self.generate_ngon(3, radius, angle)
                self.shape = "triangle"
            
            case "rhombus"|"4"|4:
                if len(params) < 1: raise FieldException(f"{self}: No proper rhombus size given")
                radius = int(params[0])
                try:
                    angle = float(params[1])
                except IndexError:
                    angle = 0
                self.generate_ngon(4, radius, angle)
                self.shape = "rhombus"
            
            case "pentagon"|"5"|5:
                if len(params) < 1: raise FieldException(f"{self}: No proper pentagon size given")
                radius = int(params[0])
                try:
                    angle = float(params[1])
                except IndexError:
                    angle = 0
                self.generate_ngon(5, radius, angle)
                self.shape = "pentagon"
            
            case "hexagon"|"6"|6:
                if len(params) < 1: raise FieldException(f"{self}: No proper hexagon size given")
                radius = int(params[0])
                try:
                    angle = float(params[1])
                except IndexError:
                    angle = 0
                self.generate_ngon(6, radius, angle)   
                self.shape = "hexagon"     

            case "heptagon"|"7"|7:
                if len(params) < 1: raise FieldException(f"{self}: No proper heptagon size given")
                radius = int(params[0])
                try:
                    angle = float(params[1])
                except IndexError:
                    angle = 0
                self.generate_ngon(7, radius, angle)
                self.shape = "heptagon"

            case _:
                raise FieldException(f"{self}: no {shape} shape supported")


    def vodify_corners(self, coords: list[tuple[int, int]]) -> None:
        """
        Expects list of edge coords
        Makes void all cells which must be vodified to form a field shape
        """
        voided = set()
        
        for y in range(self.dimensions["height"]):
            for x in range(self.dimensions["width"]):
                if (y, x) not in coords:
                    voided.add((y, x))
                else: break
            for x in range(self.dimensions["width"]-1, -1, -1):
                if (y, x) not in coords:
                    voided.add((y, x))
                else: break
        
        for yx in voided:
            self.get_cell(yx).is_void = True


    def generate_rectangle(self, height: int, width: int) -> None:
        """
        Generates rectangle field with given height and width.
        H&W < 7 are non-playable and not supported.
        """
        if width < 7 or height < 7: raise FieldException(f"{self}: Dimensions must be >7")

        self.dimensions = {"height": height, "width": width}
        for y in range(height):
            for x in range(width):
                self._cells[(y, x)] = Cell(y, x)
        logger.info(f"{self} generated")


    def generate_circle(self, radius: int) -> None:
        """
        Generates round field with given height and width.
        Radius <5 are non-playable and not supported.
        """
        if radius < 5: raise FieldException(f"{self}: Circle field radius must be >4")
        size = 2*radius + 1

        self.dimensions ={"height": size, "width": size}
        for y in range(size):
            for x in range(size):
                self._cells[(y, x)] = Cell(y, x)
        
        circle_borders = circle_coords(radius, (radius, radius))
        self.vodify_corners(circle_borders)


    def generate_ngon(self, n: int, radius: int, angle = 0.0) -> None:
        """
        Generates polygon field with n vertices and given radius/angle.
        """
        if n < 3: raise FieldException(f"{self}: Polygon must have at least 3 points")
        ngon_border = ngon_coords(n=n, radius=radius, angle=angle)
        y_min = min(y for y, _ in ngon_border)
        y_max = max(y for y, _ in ngon_border) - y_min + 1
        x_min = min(x for _, x in ngon_border)
        x_max = max(x for _, x in ngon_border) - x_min + 1

        normalized_coords = []
        for y, x in ngon_border:
            normalized_coords.append((y-y_min, x-x_min))
        
        self.dimensions ={"height": y_max, "width": x_max}
        for y in range(y_max):
            for x in range(x_max):
                self._cells[(y, x)] = Cell(y, x)
        self.vodify_corners(normalized_coords)


    def get_cell(self, coords: tuple[int, int]) -> Cell:
        """
        This method only returns cell instance by given (y, x) if it part of the field.
        It can return void cell and returns no cell if field is empty.
        It's made to separate responsibility - it just gives what it can.
        """
        if self.is_empty():
            raise FieldException(f"{self}: Tried to get cell with no field.")
        
        if not coords: raise FieldException(f"{self}: Asked for no cells.")
        
        try: return self._cells[coords]
        except KeyError: raise FieldException(f"{self}: Requested Cell {coords} does not exist.")
    

    def occupy_cells(self, entity, anchor_coords: tuple[int, int], rotation: int) -> None:
        """
        Takes entity and tries to place it correspondingly given (y, x) and rotation values.
        Raises FieldException if can't by any reason.
        If can place - it clears previously taken cells, writes information in new ones
        and forces entity self update with given position.
        """
        if entity is None: raise FieldException(f"{self}: entity can't be None.")
        if anchor_coords is None: raise FieldException(f"{self}: anchor_coords can't be None.")
        if entity.type == EntityType.PLANET:
            raise FieldException("Tried to place planet as regular entity. Use setup_a_planet instead")

        # asks which cells entity wants to take depending on it's properties
        # recieves list of (y,x) and correct rotation (e.g.  rot = 5  -->  rot = 1)
        reserved_coords, rotation = entity.reserve_coords(anchor_coords, rotation).values()
        available_cells = []

        close_cells = self.neighbours(reserved_coords)
        if close_cells is not None:
            for coords in close_cells:
                cell = self.get_cell(coords)
                if cell.occupied_by is not None and cell.occupied_by.type != EntityType.PLANET:
                    raise FieldException(f"{self}: {cell} too close to {cell.occupied_by}")

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
        entity.update_state(anchor_coords = anchor_coords, occupied_cells = reserved_coords, rotation = rotation, status = EntityStatus.FULLHEALTH)


    def neighbours(self, coord_list: list[tuple[int, int]]) -> set[tuple[int, int]]:
            """
            Returns all potential coordinates of cells near the entity
            """
            if coord_list is None or not isinstance(coord_list, list): raise FieldException(f"Getting neighbours requires proper (y, x) list")
            
            neighbours = set()
            for y, x in coord_list:
                for dy, dx in [ (-1,-1), (-1,0), (-1,1),
                                (0,-1),          (0,1),
                                (1,-1),  (1,0),  (1,1)]:
                    
                    coords = (y + dy, x + dx)
                    if coords not in coord_list and coords in self._cells: neighbours.add(coords)
            return neighbours
    

    def setup_a_planet(self, planet):
        """
        Places planet on the field.
        Can be placed out of bounds, but orbit must cross field at least once.
        """
        if planet.type != EntityType.PLANET:
            raise FieldException(f"Tried to setup a planet {planet} which is {planet.type}. Use occupy cells instead")
        
        orbit_cells = set()
        real_cells_counter = 0
        for coords in planet.orbit_cells:
            try:
                cell = self.get_cell(coords)
            except FieldException:
                continue # when tried to place orbit cell out of bounds - skip
            
            orbit_cells.add(coords)
            if not cell.is_void:
                real_cells_counter += 1
        
        if real_cells_counter == 0: raise FieldException(f"{self}: orbit of planet never crosses any field cell. Change center or radius")
        for coords in orbit_cells:
            self.get_cell(coords).occupied_by = planet
        planet.update_state(occupied_cells=list(orbit_cells),status=EntityStatus.DAMAGED)

    
    def take_shot(self, coords: tuple[int, int]) -> CellStatus:
        """
        Returns result of attempt.
        """
        cell = self.get_cell(coords)
        if cell.is_void or cell.was_shot:
            raise FieldException(f"{self}: {invert_output(coords)} is not valid target")
        
        cell.was_shot = True
        
        if cell.occupied_by is None:
            return CellStatus.MISS
        
        occupator = cell.occupied_by
        if occupator.type == EntityType.PLANET:
            if coords == occupator.anchor:
                return CellStatus.HIT
            else:
                return CellStatus.MISS
        
        elif occupator.type == EntityType.RELAY:
            occupator.make_damage(coords)
            return CellStatus.RELAY
        
        else:
            occupator.make_damage(coords)
            return CellStatus.HIT
        

    def __iter__(self):
        return iter(self._cells.keys())

    def __repr__(self):
        return f"{self.name}'s field"



class Cell:
    """
    Smallest field unit.
    Void - are structural cells.
    Every cell has link to entity it belongs to. Entity itself decides which of cell is what part.
    """
    def __init__(self, y: int, x: int, *, is_void = False):
        if not(isinstance(y, int) and isinstance(x, int)):
            raise TypeError("Cell coordinates must be integers")
        self.y, self.x = y, x
        self.is_void = is_void
        self.was_shot = False
        self.occupied_by = None

    def free(self) -> None:
        self.occupied_by = None
    
    def __str__(self):
        if self.is_void:
            return f"void({self.y},{self.x})"
        return f"cell({self.y},{self.x})"
    
    def __repr__(self):
        return f"Cell({self.y},{self.x}) is_void={self.is_void}, was_shot={self.was_shot}"