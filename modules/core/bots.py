import random
import logging

from abc import ABC, abstractmethod

from modules.common.enums import CellStatus
from modules.common.utils import invert_output


logger = logging.getLogger(__name__)


class Bot(ABC):
    """
    Generator of shot coordinates (y, x) but it's inner rules.
    Before it can shoot - must be initiated with opponent's field snapshot from the Event.
    Then shoots.
    After - expects renderer to give it instructions about aftermath of it's shot - Bot can't watch on field as a real player.
    It can't communicate with the Game class directly because of security purposes.
    """
    def __init__(self, name: str):
        self.name = str(name)
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
        Gets list of destroyed cells and mark closest coords to them on the field as missed.
        So bot doesn't shoot next to already destroyed ships.
        Destruction validation is guaranteed by game events.
        """
        for coords in destroyed_cells:
            for neighbour in self.get_neighbours(coords):
                self.opponent_field[neighbour] = CellStatus.MISS
                
                if hasattr(self, "hunt"):
                    self.hunt.discard(neighbour)

    
    def shot_result(self, coords: tuple[int, int], shot_result: CellStatus) -> None:
        
        if coords not in self.opponent_field:
            logger.warning(f"{invert_output(coords)} is not part of opponent's field snapshot but {shot_result} result given.")
        
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
    def __init__(self, name: str):
        super().__init__(name)


    def shoot(self) -> tuple[int, int]:
        shot_available = self.get_free_coords()
        
        try:
            return random.choice(list(shot_available))
        
        except IndexError:
            logger.warning(f"{self} has no available cells to shoot - returned None as coords chose.")
            pass
    

    def __str__(self):
        return f"RandomerBot-{self.name}"


class Hunter(Bot):
    """
    Medium AI. Shoots randomly unless hit once
    Then starts to shoot all the neighbour cells unless full ship destruction
    When destroyed - shoots randomly again
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.hunt: set[tuple[int, int]] = set()


    def hunt_validation(self) -> None:
        """
        Validates coordinates from hunting set to be shootable 
        """
        self.hunt &= self.get_free_coords()


    def shoot(self) -> tuple[int, int]|None:
        
        logger.debug("hunting for cells: " + str(self.hunt))
        last_coords, last_result = self.last_shot
        if last_result == CellStatus.HIT:
            self.hunt.update(self.get_cross_neighbours(last_coords))

        self.hunt_validation()
        shot_available = self.hunt if self.hunt else self.get_free_coords()
        
        try:
            return random.choice(list(shot_available))
        
        except IndexError:
            logger.warning(f"{self} has no available cells to shoot - returned None as coords chose.")
            pass


    def __str__(self):
        return f"HunterBot-{self.name}"