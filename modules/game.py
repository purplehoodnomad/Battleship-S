from __future__ import annotations
import logging
import uuid
from modules.player import Player
from modules.entities import Entity
from modules.enums_and_events import *


logger = logging.getLogger()



class Game:
    """
    Manages players and their abilities. Interface for renderer structures - CLI or endpoints
    """
    default_entities = {
        EntityType.CORVETTE: 4,
        EntityType.FRIGATE: 2,
        EntityType.DESTROYER: 1,
        EntityType.CRUISER: 1,
        EntityType.RELAY: 3,
        EntityType.PLANET: 1,
    }
    State = GameState


    def __init__(self):
        self.id = "game_" + str(uuid.uuid4())[:6]
        self._players = {}
        self.order = [] # order of turns ("name")
        self.turn = 0
        self.state = self.State.LOBBY
        self.winner: str = None
        self.events = []

    
    def add_event(self, event_type: EventType, **kwargs) -> Event:
        """
        Forms all event types and adds them to self.event history
        """
        match event_type:
            case EventType.LOBBY:
                try: names = self.get_player_names()
                except GameException: names = []
                e = LobbyEvent(
                    game_state=self.state,
                    event_type=event_type,
                    player_1=names[0] if names else None,
                    player_2=names[1] if len(names) > 1 else None,
                    turn_order=self.order,
                    winner=self.winner,
                    lobby_event=kwargs["lobby_event"],
                    payload=kwargs["payload"],
                )
            case EventType.SHOT:
                e = ShotEvent(
                    game_state=self.state,
                    event_type=event_type,
                    turn=self.turn,
                    shooter=kwargs["shooter"],
                    target=kwargs["target"],
                    coords=kwargs["coords"],
                    shot_result=kwargs["shot_result"],
                )
            case EventType.PLACE:
                try:
                    radius = kwargs["radius"]
                    orbit_cells = kwargs["orbit_cells"]
                    orbit_center = kwargs["orbit_center"]
                except KeyError:
                    radius = None
                    orbit_cells = None
                    orbit_center = None
                e = PlaceEvent(
                    game_state=self.state,
                    event_type=event_type,
                    player_name=kwargs["player_name"],
                    entity_id=kwargs["entity_id"],
                    entity_type=kwargs["entity_type"],
                    anchor=kwargs["anchor"],
                    rotation=kwargs["rotation"],
                    cells_occupied=kwargs["cells_occupied"],
                    radius=radius,
                    orbit_cells=orbit_cells,
                    orbit_center=orbit_center,
                )
        self.events.append(e)
        logger.info(e)
        return e

       

    def set_player(self, name: str, color: str) -> LobbyEvent:
        """
        Returns created player metadata. Names are unique identificators.
        """
        self.check_state(self.State.LOBBY)

        if len(self._players) >= 2: raise GameException("Game supports 2 players only.")
        
        if str(name) in self._players: name = str(uuid.uuid4())[:3] # guarantees unique names
        player = Player(name[:10], color) # slices player name for more convenient readable size
        
        self._players[player.name] = player
        self.order.append(player.name)

        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_ADDED,
            payload=self.get_player_meta(player.name)
        )
        return event


    def get_player(self, name: str) -> Player:
        """
        Allows to get access to player instance directly.
        If there's no special need - it's better to use get_player_meta().
        """
        if not self._players: raise GameException("No players in current game")
        try: return self._players[name]
        except KeyError: raise GameException(f"No Player {name} in game")


    def get_player_meta(self, name: str) -> dict:
        """
        Safely provides neccesary player information.
        """
        player = self.get_player(name)
        return {
            "name": player.name,
            "color": player.color,
            "order": self.order.index(player.name),
            "is_ai": player.is_ai,
            "pending": player.pending_entities,
            "field_settings": {
                "shape": player.field.shape,
                "height": player.field.dimensions["height"],
                "width": player.field.dimensions["width"]
            }
        }
  

    def del_player(self, name: str) -> LobbyEvent:
        self.check_state(self.State.LOBBY)
        meta = self.get_player_meta(name)

        del self.order[self.order.index(name)]
        del self._players[name]

        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_DELETED,
            payload=meta
        )
        return event
      

    def change_entity_list(self, name: str, types: dict) -> LobbyEvent:
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

        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event


    def change_player_field(self, name: str, shape: str, params: list) -> LobbyEvent:
        self.check_state(self.State.LOBBY)
        player = self.get_player(name)
        player.set_field(shape, params)
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event


    def get_player_field(self, name: str, *, private = False) -> dict:
        player = self.get_player(name)
        return player.get_field(private=private)



    def place_entity(self, name: str, entity: int, coords: tuple, r: int) -> PlaceEvent:
        """
        Tries to place entity to coords with rotation or radius r.
        If no GameException or FieldException met - returns event dict.
        """
        self.check_state(self.State.SETUP)
        player = self.get_player(name)

        # this check is very important because planets take with their orbit large amount of cells
        # to prevent situation of collision planets with ships - planets must be placed first
        if player.pending_entities[EntityType.PLANET] > 0 and entity != EntityType.PLANET.value:
            raise GameException(f"{player} must place planets first")
        
        entity_metadata = player.place_entity(entity, [coords, r])
        if entity_metadata["etype"] == EntityType.PLANET:
            radius = entity_metadata["radius"]
            orbit_cells = entity_metadata["orbit_cells"]
            orbit_center = entity_metadata["orbit_center"]
        else:
            radius = None
            orbit_cells = None
            orbit_center = None
        
        event = self.add_event(
            EventType.PLACE,
            player_name=name,
            entity_id=entity_metadata["eid"],
            entity_type=entity_metadata["etype"],
            anchor=entity_metadata["anchor"],
            rotation=entity_metadata["rotation"],
            cells_occupied=entity_metadata["cells_occupied"],
            radius=radius,
            orbit_cells=orbit_cells,
            orbit_center=orbit_center,
        )
        return event


    def autoplace(self, name: str) -> tuple:
        """
        Autoplaces all remaining ships.
        Returns tuple: list of dicts or placement events proceeded during autoplace and summary.
        """
        import random
        player = self.get_player(name)
        autoplace_events = []
        attempts_limit = 50000
        all_attempts_counter = 0

        for entity, amount in player.pending_entities.items().__reversed__(): # starts with big ones first
            if amount == 0: continue
            counter = 0
            for _ in range(amount):
                success = False
                while not success:
                    if counter >= attempts_limit:
                        return (autoplace_events, f"Unable to autoplace all entities - Too many iterations took for {entity} ({attempts_limit})")
                    
                    counter += 1
                    all_attempts_counter += 1
                    try:
                        y = random.randint(0, player.field.dimensions["height"] - 1)
                        x = random.randint(0, player.field.dimensions["width"] - 1) 
                        if entity == EntityType.PLANET:
                            r = random.randint(3, int(max(player.field.dimensions["height"], player.field.dimensions["width"])/2))
                        else: 
                            r = random.randint(0, 3)
                        event = self.place_entity(name, entity.value, (y, x), r)
                        autoplace_events.append(event)
                        success = True
                    except FieldException: continue
        
        return (autoplace_events, f"Autoplacement successfull. Took {all_attempts_counter} iterations in total.")


    def shoot(self, shooter_name: str, coords: tuple) -> ShotEvent:

        self.check_state(self.State.ACTIVE)
        shooter = self.get_player(shooter_name)
        if self.whos_turn() != shooter_name: raise GameException(f"{shooter_name} cant shoot now, it's {self.whos_turn()}'s turn")

        # getting opponent's instance
        names = self.get_player_names()
        if len(names) != 2: raise GameException(f"Can't get opponent of {shooter_name}, player count {len(names)}!=2")
        del names[names.index(shooter_name)]
        target_name = names[0]
        target = self.get_player(target_name)
        
        result = target.take_shot(coords)
        if result == CellStatus.HIT:
            self.order.reverse()
        
        elif result == CellStatus.RELAY:
            try:
                reverse_shot_result = shooter.take_shot(coords)
                if reverse_shot_result == CellStatus.RELAY:
                        self.state = self.State.OVER
                        self.winner = "Infinite relay refraction created a black hole. No one survived."          
            except:
                pass
        
        elif result == CellStatus.DESTROYED:
            self.order.reverse()
            if all(Entity.Status.DESTROYED == entity.status for entity in target.entities.values()):
                self.state = self.State.OVER
                self.winner = shooter.name
        self.turn += 1
        
        # moving all planets on their orbites when turn proceeds
        for player in self._players.values():
            for entity in player.entities.values():
                if entity.type == EntityType.PLANET:
                    entity.position += 1
        
        event = self.add_event(
            EventType.SHOT,
            shooter=shooter_name,
            target=target_name,
            coords=coords,
            shot_result=result
        )
        return event



    def normalize_eids(self) -> None:
        """
        Placing wrong creates a lot of gc instances
        This method brings eid back to numeration from 0
        """
        if not self._players: raise GameException("Unable to normalize eids: No players")
        for player in self._players.values():
            player.normalize_eids()


    def ready(self) -> LobbyEvent:
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

        previous_state = self.state
        self.state = self.State.SETUP
        
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.STATE_CHANGED,
            payload={
                "previous_state": previous_state
            }
        )
        return event

    def start(self) -> LobbyEvent:
        self.check_state(self.State.SETUP)

        for player in self._players.values():
            if len(player.entities.values()) == 0: raise GameException(f"{player} doesn't have any placed entities")
            for amount_unplaced in player.pending_entities.values():
                if amount_unplaced != 0: raise GameException(f"{player} hasn't placed all their entities")
        
        previous_state = self.state
        self.state = self.State.ACTIVE
        
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.STATE_CHANGED,
            payload={
                "previous_state": previous_state
            }
        )
        return event


    def get_player_names(self) -> list:
        if not self._players: raise GameException("No players in current game")
        return list(self._players.keys())
  
    def whos_turn(self) -> str:
        """
        Converts current turn into index and returns name of player.
        """
        if not self.order: raise GameException("Order is empty. No players set")
        return self.order[(self.turn) % len(self.order)]
    
    def whos_winner(self) -> str:
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