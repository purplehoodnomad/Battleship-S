from __future__ import annotations
import random
import logging

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
        self.game = game
        self.player = self.game.get_player(name)
        self.player.is_ai = True
    
    def get_opponent(self) -> Player:
        """
        Lets Bot knowing who is his target directly from the game
        """
        player_list = self.game.get_player_names()
        if len(player_list) <= 1: raise BotException("Can't get opponent, bot only in game")
        if len(player_list) >= 3: raise BotException("Playing with more than 2 players is not supported yet")
        
        del player_list[player_list.index(self.player.name)]
        return self.game.get_player(player_list[0])

    def get_free_coords(self) -> list:
        """
        Returns list of (y,x) which are not void and not shot yet
        """
        t_field = self.get_opponent().get_field()

        shot_available = []
        for coords, state in t_field.items():
            if state != "free": continue
            shot_available.append(coords)
    
        if shot_available:
            return shot_available
        raise BotException(f"No free cells remain")
    

    def get_neighbours(self, coords: tuple) -> list:
        """
        Returns list of closest (y,x) to given coords on opponent's field
        """
        y, x = coords[0], coords[1]
        
        # field method returns all neighbors - even diagonal ones, but it guarantees that those cells exist
        all_neighbours = self.get_opponent().field.neighbours([coords])

        # forms list of 4 potential coordinates next to given coords
        cross_neighbours = [(y + dy, x + dx) for dy, dx in [
                                (-1,0),
                        (0,-1),          (0,1),
                                 (1,0)]]
        # picks from all neighbours only those who are in cross
        return [pos for pos in cross_neighbours if pos in all_neighbours]


class Randomer(Bot):
    """
    Simpliest AI. Shoots absolutely randomly
    """
    def __init__(self, name, game):
        super().__init__(name, game)
        logger.info(f"{self.player} is now Randomer Bot")

    def shoot(self) -> str:
        target = self.get_opponent()
        shot_available = self.get_free_coords()

        if self.player.name == self.game.whos_turn():
            coords = random.choice(shot_available)

            result = self.game.shoot(self.player.name, target.name, coords)
            output = f"{self.player.name} shot {coords}. Result - {result}"

            if result == "hit" or result == "destroyed": output += "\n" + self.shoot()
            return output


class Hunter(Bot):
    """
    Medium AI. Shoots randomly unless hit once
    Then starts to shoot all the neighbour cells unless full ship destruction
    When destroyed - shoots randomly again
    """
    def __init__(self, name, game):
        super().__init__(name, game)
        self.hunt = set()
        logger.info(f"{self.player} is now Hunter Bot")
        
    def hunt_validation(self):
        """
        Validates coordinates from hunting set to be shootable 
        """
        if not self.hunt: return

        for coords in list(self.hunt):
            cell = self.get_opponent().field.get_cell(coords)
            if cell.is_void or cell.was_shot: self.hunt.remove(coords)


    def shoot(self) -> str:
        target = self.get_opponent()

        if not self.hunt: shot_available = self.get_free_coords()
        else: shot_available = list(self.hunt)

        if self.player.name == self.game.whos_turn():
            coords = random.choice(shot_available)

            result = self.game.shoot(self.player.name, target.name, coords)
            output = f"{self.player.name} shot {coords}. Result - {result}"
            
            self.hunt_validation() # deletes missed cell from hunt set
            if result == "hit" or result == "destroyed":
                for neighbour in self.get_neighbours(coords):
                    self.hunt.add(neighbour)
                self.hunt_validation() # validates all of the neighbours after addition
                output += "\n" + self.shoot()
            return output
