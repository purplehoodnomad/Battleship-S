from __future__ import annotations
import random
import logging
from abc import ABC, abstractmethod
from modules.enums_and_events import CellStatus

logger = logging.getLogger(__name__)


class BotException(Exception): pass
class Bot(ABC):
    """
TODO
    """
    def __init__(self):
        self.opponent_field: dict[tuple[int,int], CellStatus] = {}
        self.last_shot = ((-1,-1), CellStatus.MISS)


    def get_free_coords(self) -> set[tuple[int, int]]:
        """
        Returns set of (y,x) which are not void and not shot yet
        """
        return {coords for coords, state in self.opponent_field.items() if state == CellStatus.FREE}


    def get_neighbours(self, coords: tuple[int, int]) -> set[tuple[int, int]]:
        """
        Returns list of all (y,x) next to given coords vertically, horizontally and diagonally.
        """
        y, x = coords

        neighbours = [(y + dy, x + dx) for dy, dx in [
                        (1,-1),  (-1,0), (1,1),
                        (0,-1),          (0,1),
                        (-1,-1),  (1,0), (-1,1)]]

        return {coord for coord in neighbours if coord in self.opponent_field}

    def get_cross_neighbours(self, coords: tuple[int, int]) -> set[tuple[int, int]]:
        """
        Returns list of closest (y,x) vertically and horizontally.
        """
        y, x = coords
        # forms list of 4 potential coordinates next to given coords
        cross_neighbours = [(y + dy, x + dx) for dy, dx in [
                                (-1,0),
                        (0,-1),          (0,1),
                                 (1,0)]]
        # picks from cross coordinates which are in actual field
        return {coord for coord in cross_neighbours if coord in self.opponent_field}


    def validate_destruction(self, destroyed_cells: list[tuple[int, int]]) -> None:
        """
        Gets list of destroyed cells and mark closest coords to them on the field as hit.
        To be unavailable to picked from by bot.
        """
        for coords in destroyed_cells:
            for neighbour in list(self.get_neighbours(coords)):
                self.opponent_field[neighbour] = CellStatus.HIT
    
    def shot_result(self, coords: tuple[int, int], shot_result: CellStatus):
        self.opponent_field[coords] = shot_result
        self.last_shot = (coords, shot_result)
        

    @abstractmethod
    def shoot(self) -> tuple[int, int]:
        """
        Expects {(y,x): "status"}
        Returns (y,x) coords where bot wants to shoot
        """
        pass

class Randomer(Bot):
    """
    Simpliest AI. Shoots absolutely randomly
    """
    def __init__(self):
        super().__init__()

    def shoot(self) -> tuple[int, int]:
        shot_available = self.get_free_coords()
        return random.choice(list(shot_available))


class Hunter(Bot):
    """
    Medium AI. Shoots randomly unless hit once
    Then starts to shoot all the neighbour cells unless full ship destruction
    When destroyed - shoots randomly again
    """
    def __init__(self):
        super().__init__()
        self.hunt: set[tuple[int, int]] = set()

        

    def hunt_validation(self) -> None:
        """
        Validates coordinates from hunting set to be shootable 
        """
        self.hunt &= self.get_free_coords()


    def shoot(self) -> tuple[int, int]:
        
        last_coords, last_result = self.last_shot
        if last_result == CellStatus.HIT:
            self.hunt.update(self.get_cross_neighbours(last_coords))

        self.hunt_validation()
        shot_available = self.hunt if self.hunt else self.get_free_coords()
        return random.choice(list(shot_available))
