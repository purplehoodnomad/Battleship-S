from __future__ import annotations
import random
import logging
from abc import abstractmethod

# from game import Game
# from player import Player
# from field import Field, Cell

logger = logging.getLogger(__name__)


class BotException(Exception): pass
class Bot:
    """
    Bots communicate with all of the modules directly
    This allows to think them all the way out without asking renderer to give them copy of all information
    """
    def __init__(self, name, game: Game):
        """
        Modificates game player instance to mark it as AI
        """
        player = game.get_player(name)
        player.is_ai = True


    def get_free_coords(self, field: dict) -> list:
        """
        Returns list of (y,x) which are not void and not shot yet
        """
        return [coords for coords, state in field.items() if state == "free"]
    

    def get_neighbours(self, coords: tuple, field: dict) -> list:
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
        return [coord for coord in cross_neighbours if coord in field]

    @abstractmethod
    def shoot(self, field: dict) -> tuple:
        """
        Expects {(y,x): "status"}
        Returns (y,x) coords where bot wants to shoot
        """
        ...

class Randomer(Bot):
    """
    Simpliest AI. Shoots absolutely randomly
    """
    def __init__(self, name, game):
        super().__init__(name, game)
        logger.info(f"{name} is now Randomer Bot")

    def shoot(self, field: dict) -> tuple:
        shot_available = self.get_free_coords(field)
        return random.choice(shot_available)


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
        

    def hunt_validation(self, field: dict) -> list:
        """
        Validates coordinates from hunting set to be shootable 
        """
        if not self.hunt: return self.hunt
        
        validated = []
        for coords in list(self.hunt):
            if field[coords] == "free":
                validated.append(coords)
        self.hunt = validated
        return self.hunt


    def shoot(self, field: dict) -> tuple:
        if self.last_shot is not None and field[self.last_shot] == "hit":
            self.hunt.extend([coords for coords in self.get_neighbours(self.last_shot, field) if coords not in self.hunt])

        shot_available = self.hunt_validation(field)
        if not shot_available:
            shot_available = self.get_free_coords(field)
        self.last_shot = random.choice(shot_available)
        return self.last_shot
