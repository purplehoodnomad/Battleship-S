from __future__ import annotations
import logging
from enum import Enum
import uuid
from modules.player import Player
from modules.entities import Entity


logger = logging.getLogger()


class GameException(Exception): pass
class Game:
    """
    Manages players and their abilities. Interface for renderer structures - CLI or endpoints
    """
    default_entities = {
        Entity.Type.CORVETTE: 4,
        Entity.Type.FRIGATE: 3,
        Entity.Type.DESTROYER: 2,
        Entity.Type.CRUISER: 1,
        # Entity.Type.BATTLESHIP: 0,
        # Entity.Type.RELAY: 0,
        # Entity.Type.PLANET: 0
    }
    
    class State(Enum):
        LOBBY = 1
        SETUP = 2
        ACTIVE = 3
        OVER = 4

    def __init__(self):
        self.id = "game_" + str(uuid.uuid4())[:6]
        self._players = {}
        self.order = [] # order of turns ("name")
        self.turn = 0
        self.state = self.State.LOBBY
        self.winner = None


    def whos_turn(self) -> str:
        """
        Converts current turn into index and returns name of player.
        """
        if not self.order: raise GameException("Order is empty. No players set")
        return self.order[(self.turn) % len(self.order)]
       

    def set_player(self, name: str, color: str) -> dict:
        """
        Returns created player metadata. Names are unique identificators.
        """
        self.check_state(self.State.LOBBY)

        if len(self._players) >= 2: raise GameException("Game supports 2 players only.")
        
        if str(name) in self._players: name = str(uuid.uuid4())[:3] # guarantees unique names
        player = Player(name[:10], color) # slices player name for more convenient readable size
        
        self._players[player.name] = player
        self.order.append(player.name)

        logger.info(f"{self}: Player: {player} was set.")
        logger.info(f"{self}: player order: {self.order}.")
        return self.get_player_meta(player.name)
    

    def del_player(self, name: str) -> None:
        self.get_player(name)
        self.check_state(self.State.LOBBY)

        del self.order[self.order.index(name)]
        del self._players[name]
        logger.info(f"Player {name} was deleted")
        logger.info(f"{self}: player order: {self.order}.")
    

    def get_player(self, name: str) -> Player:
        """
        Allows to get access to player instance directly.
        If there's no special need - it's better to use get_player_meta().
        """
        if not self._players: raise GameException("No players in current game")
        try: return self._players[name]
        except KeyError: raise GameException(f"No Player {name} in game")

    
    def get_player_names(self) -> list:
        if not self._players: raise GameException("No players in current game")
        return list(self._players.keys())
    
    
    def get_player_meta(self, name: str) -> dict:
        """
        Safely provides neccesary player information.
        """
        player = self.get_player(name)
        meta = {
            "name": player.name,
            "color": player.color,
            "order": self.order.index(player.name),
            "is_ai": player.is_ai,
            "pending": {} # dict if pending entities
        }
        for etype, amount in player.pending_entities.items():
            meta["pending"][str(etype).replace("Type.", "").capitalize()] = amount
        return meta
    

    def change_entity_list(self, name: str, types: dict) -> dict:
        """
        Changes entities amount which are present in types dict.
        """
        player = self.get_player(name)
        self.check_state(self.State.LOBBY)

        for etype, amount in types.items():
            if etype in self.default_entities:
                if not amount: amount = 0
                elif int(amount) > 4: amount = 4
                elif int(amount) < 0: amount = 0
                else: amount = int(amount)
                player.pending_entities[etype] = int(amount)
        return player.pending_entities
    
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! НЕ ПРОБОВАЛ
    def replace_entity(self, name, eid, coords, rot):
        self.check_state(self.State.SETUP)
        player = self.get_player(name)
        player.replace_entity(eid, coords, rot)


    def get_player_field(self, name: str, *, private = False) -> dict:
        player = self.get_player(name)
        return player.get_field(private=private)
    

    def shoot(self, shooter_name: str, coords: tuple) -> str:

        self.check_state(self.State.ACTIVE)
        shooter = self.get_player(shooter_name)
        if self.whos_turn() != shooter_name: raise GameException(f"{shooter_name} cant shoot now, it's {self.whos_turn()}'s turn")

        # getting opponent's instance
        names = self.get_player_names()
        if len(names) != 2: raise GameException(f"Can't get opponent of {shooter_name}, player count {len(names)}!=2")
        del names[names.index(shooter_name)]
        victim = self.get_player(names[0])
        
        result = victim.take_shot(coords)
        if result == "hit": return result
        elif result == "destroyed":
            if all(Entity.Status.DESTROYED == entity.status for entity in victim.entities.values()):
                self.state = self.State.OVER
                self.winner = shooter.name
        self.turn += 1
        return result
        
        

    def change_player_field(self, name: str, shape: str, params: list) -> None:
        self.check_state(self.State.LOBBY)
        player = self.get_player(name)
        player.set_field(shape, params)


    def ready(self) -> None:
        """
        Tries to proceed to setup state if possible.
        """
        self.check_state(self.State.LOBBY)
        if len(self._players) != 2: raise GameException("Must be 2 players to initialize setup state")

        for player in self._players.values():
            if player.field is None: raise GameException(f"Can't initialize setup state: {player} doesn't have a field")
            counter = 0
            for amount in player.pending_entities.values():
                counter += amount
            if counter == 0: raise GameException(f"Can't initialize setup state: {player} doesn't have pending entities list")

        self.state = self.State.SETUP
        logger.info(f"{self}: state has changed. Players must place ships")


    def start(self) -> None:
        self.check_state(self.State.SETUP)

        for player in self._players.values():
            if len(player.entities.values()) == 0: raise GameException(f"{player} doesn't have any placed entities")
            for amount_unplaced in player.pending_entities.values():
                if amount_unplaced != 0: raise GameException(f"{player} hasn't placed all their entities")
        
        self.state = self.State.ACTIVE
        logger.info(f"{self}: state has changed. Turn {self.turn} - {self.whos_turn()} shoots")


    def place_entity(self, name: str, entity: int, coords: tuple, rot: int) -> None:
        
        self.check_state(self.State.SETUP)
        player = self.get_player(name)
        player.place_entity(entity, coords, rot)
    

    def autoplace(self, name: str):
        """
        Autoplaces all remain ships
        """
        import random
        player = self.get_player(name)
        for entity, amount in player.pending_entities.items().__reversed__(): # starts with big ones first
            if amount == 0: continue
            counter = 0
            for _ in range(amount):
                success = False
                while not success:
                    if counter >= 50000: raise ValueError("Unable to autoplace entities - Too many iterations")
                    counter += 1
                    try:
                        y = random.randint(0, player.field.dimensions["height"] - 1)
                        x = random.randint(0, player.field.dimensions["width"] - 1) 
                        rot = random.randint(0, 3)
                        self.place_entity(name, entity.value, (y, x), rot)
                        success = True
                    except Exception: continue
        player.normalize_eids()
    

    def normalize_eids(self) -> None:
        """
        Placing wrong creates a lot of gc instances
        This method brings eid back to numeration from 0
        """
        if not self._players: raise GameException("Unable to normalize eids: No players")
        for player in self._players.values():
            player.normalize_eids()


    def whos_winner(self):
        try:
            self.check_state(self.State.OVER)
            return self.winner
        except GameException: return

    def check_state(self, state: Game.State) -> None:
        """
        Raises error if current state not match expected one.
        """
        if state != self.state: raise GameException(f"Wrong game state {self.state}. {state} expected.")


    def __repr__(self):
        return f"{self.id} {self.state}"