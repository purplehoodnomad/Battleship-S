import logging
from random import choice, randint
from typing import Optional

from modules.common.enums import EntityType, EntityStatus
from modules.common.exceptions import EntityException
from modules.common.utils import circle_coords, sort_circle_coords, invert_output


logger = logging.getLogger(__name__)


class Entity:

    _counter = 0 # used to implement entity ids
    def __init__(self):

        # metadata
        self.eid = Entity._counter # counter is used as identifier. It's simpliest way to implement unique id when there're no async
        Entity._counter += 1

        # geometry and positioning
        self.anchor: tuple = None # (y, x) # type: ignore
        self.size = 1
        self.rotation: int = None # 0, 1, 2, 3 # type: ignore
        
        # reference attributes
        self.cells_occupied = [] # list of cell coords
        self.cells_damaged = set() # cells which have damage where 0 is anchor

        # state and identification
        self.type = EntityType.UNIDENTIFIED
        self._status = EntityStatus.NOTPLACED



    def update_state(
        self,
        *,
        anchor_coords: tuple[int, int] = None, # type: ignore
        cells_occupied: list[tuple[int, int]] = None, # type: ignore
        rotation: int = None, # type: ignore
        status: EntityStatus = None # type: ignore
    ) -> None:
        """
        Syncronizes self state with data given by Field.
        Updates only given parameters.
        """
        if anchor_coords is not None: self.anchor = anchor_coords
        if cells_occupied is not None: self.cells_occupied = cells_occupied
        if rotation is not None: self.rotation = rotation
        if status is not None: self.status = status


    def make_damage(self, coords: tuple[int, int]) -> None:
        "Converts given coords to distance from anchor point and marks it as damaged."
        if coords not in self.cells_occupied:
            raise EntityException(f"Tried to damage {coords} which are not cells occupied by {self}")
        
        damaged_tile = self.cells_occupied.index(coords)
        
        self.cells_damaged.add(damaged_tile)

        if self.size == len(self.cells_damaged):
            self.status = EntityStatus.DESTROYED
        else:
            self.status = EntityStatus.DAMAGED


    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value: EntityStatus):
        if not isinstance(value, EntityStatus):
            raise EntityException(f"Tried to set status of {self} to {value} which is not EntityStatus")
        
        old = self._status
        self._status = value
        
        logger.debug(f"{self} state changed: {old} → {self.status}")


    @staticmethod
    def rotation_manage(rotation) -> tuple[tuple[int, int], int]:
        """
        Rotation is counterclockwise because (0,0) is a left upper corner of the field - inverted square coords.
        Computing same with sin/cos would result same values, but this one more stable for tile-based field.
        Returns tuple of ((dy, dx), normalized rotation value).
        """
        rotation = (rotation + 4) % 4
        dydx = [
            (0,1),  # right
            (1,0),  # down
            (0,-1), # left
            (-1,0)  # up
        ]
        return (dydx[rotation], rotation)
    

    def reserve_coords(self, anchor_coords: tuple, rotation: int) -> tuple[list[tuple[int, int]], int]:
        """
        Returns tuple: list of cells entity would take with giiven anchor coords and rotation;
        and normalized rotation.
        """
        y0, x0 = anchor_coords
        
        dydx, rotation = Entity.rotation_manage(rotation)
        reserved_coords = [((y0 + i*dydx[0]), (x0 + i*dydx[1])) for i in range(self.size)]
        
        return (reserved_coords, rotation)
    

    def __str__(self):
        type_name = str(self.type).replace('EntityType.', '').capitalize()
        return f"{type_name}-{self.eid}, occupies cells: {[(invert_output(coords)) for coords in self.cells_occupied]}"



class Ship(Entity):
    """
    Main entity in the game.
    Can be placed next to the field border and planet orbits.
    Can't be placed next to other ships or relays.
    """
    def __init__(self, etype: EntityType):
        """
        Creates ship entity with given ship type.
        """
        super().__init__()
        
        if not isinstance(etype, EntityType) or etype.value > EntityType.CRUISER.value:
            raise EntityException(f"Ship must have ship type value or same int value, not {etype}")
        self.size = etype.value
        self.type = etype


    @property
    def metadata(self) -> dict:
        """
        Returns ship's metadata as dict.
        """
        return {
            "eid": self.eid,
            "etype": self.type,
            "status": self.status,
            "size": self.size,
            "anchor": self.anchor,
            "rotation": self.rotation,
            "cells_occupied": self.cells_occupied,
            "cells_damaged": self.cells_damaged,
        }


    def __repr__(self):
        return f"eid={self.eid} {self.type} {self.status}, a={self.anchor} r={self.rotation}, occupied={[coords for coords in self.cells_occupied]}"


class Planet(Entity):
    """
    Decoy object. Rotates over it's orbit on every turn.
    Can cross field partially - that's why position of planet (it's anchor) stored in entity instance and not in field's.
    Field only knows which cells are belong to planet's orbit.
    """
    def __init__(self, radius: int, center: tuple, rotation: Optional[int] = None):
        super().__init__()
        
        self.orbit_radius = radius
        self.orbit_center = () # (y, x) of center
        self.orbit_cells = [] # all orbit cells (even those not present on field)
        self.anchor = () # coords of current planet position on orbit
        
        self.cells_occupied = [] # all coords pairs which are part of the field
        self.type = EntityType.PLANET
        
        if rotation is None:
            self.rotation = choice([1, -1]) # 1=clockwise; -1=counterclockwise
        # sign of rotation defines direction and value defines speed
        else: self.rotation = rotation

        self.set_orbit(radius, center)
        self.position = 0 # is used for iterating in orbit_cells lists


    @property
    def position(self) -> int:
        return self._position

    @position.setter
    def position(self, value: int):
        """
        Value representing position of planet anchor on it's orbit (index of cell in orbit list).
        First setter - initialization.
        All next - rotating step: (1)=1 forwards; (-2)=2 backwards.
        """
        length = len(self.orbit_cells)
        if length == 0:
            return

        if not hasattr(self, "_position") or self._position is None:
            self._position = value % length
            self.anchor = self.orbit_cells[self._position]
            return

        old = self._position
        delta = value - old
        self._position = (old + delta * self.rotation) % length
        self.anchor = self.orbit_cells[self._position]

    
    @property
    def status(self):
        return self._status
    
    @status.setter # removes anchor point upon destruction
    def status(self, value: EntityStatus):
        
        if not isinstance(value, EntityStatus):
            raise EntityException(f"{value} is not EntityStatus")
        
        if value == EntityStatus.DESTROYED:
            self.anchor = ()
            self._status = value
            logger.info(f"Planet was destroyed: {self}")
        else:
            self._status = value


    def set_orbit(self, radius: int, center: tuple[int, int]) -> None:
        """
        Generates orbit cells and saves them in the planet instance.
        """
        if radius == 0:
            self.orbit_center = center
            self.orbit_cells = [center]
            return
        
        orbit = circle_coords(radius, center)
        orbit = sort_circle_coords(center, orbit)
        
        self.orbit_center = center
        self.orbit_cells = orbit

        self.position = randint(0, len(orbit) - 1)


    @property
    def metadata(self) -> dict:
        """
        Returns planet metadata as dict.
        """
        return {
            "eid": self.eid,
            "etype": self.type,
            "status": self.status,
            "anchor": self.anchor,
            "rotation": self.rotation,
            "cells_occupied": self.cells_occupied,
            "radius": self.orbit_radius,
            "orbit_cells": self.orbit_cells,
            "orbit_center": self.orbit_center
        }

    def reserve_coords(self, anchor_coords: tuple, rotation: int) -> tuple[list[tuple[int, int]], int]:
        raise EntityException("reserve_coords() is not supported for planets")


    def __repr__(self):
        return f"eid={self.eid} {self.type}, center={invert_output(self.orbit_center)}{self.orbit_center} radius={self.orbit_radius} anchor={invert_output(self.anchor)}{self.anchor}"



class Relay(Entity):
    """
    1-tiled ships which returns shot on shooter's field.
    """
    def __init__(self):
        super().__init__()
        self.type = EntityType.RELAY

    
    @property
    def metadata(self) -> dict:
        return {
            "eid": self.eid,
            "etype": self.type,
            "status": self.status,
            "size": self.size,
            "anchor": self.anchor,
            "rotation": self.rotation,
            "cells_occupied": self.cells_occupied,
            "cells_damaged": self.cells_damaged,
        }