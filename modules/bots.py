from __future__ import annotations
import random
import logging
from abc import ABC, abstractmethod
from modules.enums_and_events import CellStatus

logger = logging.getLogger(__name__)


class BotException(Exception): pass
class Bot(ABC):
    """
    Bots communicate with all of the modules directly
    This allows to think them all the way out without asking renderer to give them copy of all information
    """
    def __init__(self, name, game: Game):
        """
        Modificates game player instance to mark it as AI
        """
        player = game._get_player(name)
        player.is_ai = True
        self.opponent_field = {}


    def get_free_coords(self) -> list:
        """
        Returns list of (y,x) which are not void and not shot yet
        """
        return [coords for coords, state in self.opponent_field.items() if state == CellStatus.FREE]
    

    def get_neighbours(self, coords: tuple) -> list:
        """
        Returns list of closest (y,x) to given coords on opponent's field
        """
        y, x = coords
        # forms list of 4 potential coordinates next to given coords
        cross_neighbours = [(y + dy, x + dx) for dy, dx in [
                                (-1,0),
                        (0,-1),          (0,1),
                                 (1,0)]]
        # picks from cross coordinates which are in actual field
        return [coord for coord in cross_neighbours if coord in self.opponent_field]

    @abstractmethod
    def shoot(self, field: dict) -> tuple:
        """
        Expects {(y,x): "status"}
        Returns (y,x) coords where bot wants to shoot
        """
        pass

class Randomer(Bot):
    """
    Simpliest AI. Shoots absolutely randomly
    """
    def __init__(self, name, game):
        super().__init__(name, game)
        logger.info(f"{name} is now Randomer Bot")

    def shoot(self) -> tuple[int, int]:
        shot_available = self.get_free_coords()
        shot = random.choice(shot_available)
        logger.debug(f"RandomerBot chose to shoot {shot} from {len(shot_available)} free cells")
        return shot


class Hunter(Bot):
    """
    Medium AI. Shoots randomly unless hit once
    Then starts to shoot all the neighbour cells unless full ship destruction
    When destroyed - shoots randomly again
    """
    def __init__(self, name, game):
        super().__init__(name, game)
        self.hunt = [] # [(y,x)...]
        self.last_shot = None # (y,x)
        logger.info(f"{name} is now Hunter Bot")
        

    def hunt_validation(self) -> list[tuple[int, int]]:
        """
        Validates coordinates from hunting set to be shootable 
        """
        if not self.hunt: return self.hunt
        
        validated = []
        for coords in list(self.hunt):
            if self.opponent_field[coords] == CellStatus.FREE:
                validated.append(coords)
        self.hunt = validated
        return self.hunt


    def shoot(self) -> tuple[int, int]:
        if self.last_shot is not None and self.opponent_field[self.last_shot] == CellStatus.HIT:
            self.hunt.extend([coords for coords in self.get_neighbours(self.last_shot) if coords not in self.hunt])
            logger.debug(f"HunterBot is in hunt mode. Hunting for {self.hunt}")

        shot_available = self.hunt_validation()
        if not shot_available:
            shot_available = self.get_free_coords()
            logger.debug(f"HunterBot is in random mode")
        self.last_shot = random.choice(shot_available)
        logger.debug(f"HunterBot chose to shoot {self.last_shot} from {len(shot_available)} free cells")
        return self.last_shot
