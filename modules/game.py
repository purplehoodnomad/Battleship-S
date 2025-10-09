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
        EntityType.CORVETTE: 5,
        EntityType.FRIGATE: 3,
        EntityType.DESTROYER: 2,
        EntityType.CRUISER: 1,
        EntityType.RELAY: 3,
        EntityType.PLANET: 2,
    }


    def __init__(self):
        self.id = "game_" + str(uuid.uuid4())[:6]
        self._players = {}
        self.order = [] # order of turns ("name")
        self.turn = 0
        self.state = GameState.LOBBY
        self.winner: str = None
        self.events = []

    
    def add_event(self, event_type: EventType, **kwargs) -> LobbyEvent|PlaceEvent|ShotEvent:
        """
        Forms all event types and adds them to self.event history.
        Events store all information required to reproduce all states of game.
        It's suggested - renderers use events to draw information on clients.
        Some information is private - can't be sent directly to clients.
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
                    shot_results=kwargs["shot_results"],
                    planets_anchors=kwargs["planets_anchors"],
                    destroyed_cells=kwargs["destroyed_cells"]
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
        Names are unique identificators.
        """
        self.check_state(GameState.LOBBY)

        if len(self._players) >= 2: raise GameException("Game supports 2 players only.")
        
        if str(name) in self._players:
            raise GameException(f"{name} is already in game. Give unique name")
        player = Player(name, color) 
        
        self._players[player.name] = player
        self.order.append(player.name)

        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_ADDED,
            payload=self.get_player_meta(player.name)
        )
        return event


    def _get_player(self, name: str) -> Player:
        """
        Allows to get access to player instance directly.
        Used by game. To give safe information further - use get_player_meta().
        """
        if not self._players: raise GameException("No players in current game")
        try: return self._players[name]
        except KeyError: raise GameException(f"No Player {name} in game")


    def get_player_meta(self, name: str) -> dict:
        """
        Safely provides neccesary player information.
        """
        player = self._get_player(name)

        destroyed_cells = []
        for entity in player.entities.values():
            if entity.status == EntityStatus.DESTROYED and entity.type != EntityType.PLANET:
                for coords in entity.cells_occupied:
                    destroyed_cells.append(coords)
        
        return {
            "name": player.name,
            "color": player.color,
            "order": self.order.index(player.name),
            "pending": player.pending_entities,
            "destroyed_cells": destroyed_cells,
            "shape": player.field.shape,
            "height": player.field.dimensions["height"],
            "width": player.field.dimensions["width"],
            "real_cells": player.field.useful_cells_coords
        }
  

    def del_player(self, name: str) -> LobbyEvent:
        self.check_state(GameState.LOBBY)
        meta = self.get_player_meta(name)

        del self.order[self.order.index(name)]
        del self._players[name]

        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_DELETED,
            payload=meta
        )
        return event
    

    def change_player_color(self, name: str, color: str) -> LobbyEvent:
        """
        Allows to change color any time (even midgame).
        """
        player = self._get_player(name)
        player.colorize(color)
        
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event
      

    def change_entity_list(self, name: str, types: dict) -> LobbyEvent:
        """
        Changes entities amount for player which are present in types dict.
        """
        player = self._get_player(name)
        self.check_state(GameState.LOBBY)

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
        
        self.check_state(GameState.LOBBY)
        player = self._get_player(name)
        player.set_field(shape, params)
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event


    # TODO NOT USED. REMOVE OR REFACTOR LATER
    # def get_player_field(self, name: str, *, private = False) -> dict:
    #     player = self._get_player(name)
    #     return player.get_field(private=private)


    def place_entity(self, name: str, etype: EntityType, coords: tuple, r: int) -> PlaceEvent:
        """
        Tries to place entity to coords with rotation or radius r.
        If no GameException or FieldException met - returns event dict.
        """
        self.check_state(GameState.SETUP)
        player = self._get_player(name)

        # this check is very important because planets take with their orbit large amount of cells
        # to prevent situation of collision planets with ships - planets must be placed first
        if player.pending_entities[EntityType.PLANET] > 0 and etype != EntityType.PLANET:
            raise GameException(f"{player} must place planets first")
        
        entity_metadata = player.place_entity(etype, [coords, r])
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


    def autoplace(self, name: str) -> tuple[list[PlaceEvent], str]:
        """
        Autoplaces all remaining ships.
        Returns tuple: list of dicts or placement events proceeded during autoplace and summary.
        """
        import random
        player = self._get_player(name)
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
                        event = self.place_entity(name, entity, (y, x), r)
                        autoplace_events.append(event)
                        success = True
                    except FieldException: continue
        
        return (autoplace_events, f"Autoplacement successfull. Took {all_attempts_counter} iterations in total.")


    def shoot(self, shooter: str, coords: tuple) -> list[ShotEvent]:
        """
        Initiates shoot event and return results for both players.
        Returns 2 events in list: first is for target field and the second is for shooter itself.
        (Planet movements, relay refractions)
        """
        
        # checking for game conditions and getting shooter's instance
        self.check_state(GameState.ACTIVE)
        shooter = self._get_player(shooter)
        if self.whos_turn() != shooter.name: raise GameException(f"{shooter.name} cant shoot now, it's {self.whos_turn()}'s turn")

        # getting opponent's instance
        names = self.get_player_names()
        names.remove(shooter.name)
        target = self._get_player(names[0])

        # shoot event itself
        result = target.take_shot(coords)
        
        target_field_updates, shooter_field_updates = {}, {}
        match result:
            case CellStatus.MISS:
                target_field_updates.update({coords: result})
            
            case CellStatus.HIT:
                target_field_updates.update({coords: result})
                self.order.reverse() # next turn will start from shooter player again
            
            case CellStatus.RELAY:
                target_field_updates.update({coords: CellStatus.HIT})
                # making reflected shot into same coordinates
                try:
                    reverse_shot_result = shooter.take_shot(coords)
                    shooter_field_updates.update({coords: reverse_shot_result})
                    
                    # checking unique game ending - infinite reflection
                    if reverse_shot_result == CellStatus.RELAY:
                        self.state = GameState.OVER
                        self.winner = "Black Hole"
                except FieldException:
                    pass # if reflected shot hits already shot cell or void one
        # moving game further
        self.turn += 1

        target_planets_positions, shooter_planets_positions = [], []
        # moving planets
        for player in self._players.values():
            planet_movement_results = player.move_planets(1)
            for coords, status in planet_movement_results.items():
                if status == CellStatus.HIT:
                    if player == target:
                        target_field_updates.update(planet_movement_results)
                    else:
                        shooter_field_updates.update(planet_movement_results)
                else:
                    if player == target:
                        target_planets_positions.append(coords)
                    else:
                        shooter_planets_positions.append(coords)
        
        if not self.winner or self.winner is None:
                # checking if game ended
                shooter_is_destroyed = all(EntityStatus.DESTROYED == entity.status for entity in shooter.entities.values() if entity.type != EntityType.PLANET)
                target_is_destroyed = all(EntityStatus.DESTROYED == entity.status for entity in target.entities.values() if entity.type != EntityType.PLANET)
                if shooter_is_destroyed and target_is_destroyed:
                    self.state = GameState.OVER
                    self.winner = "Draw"
                elif shooter_is_destroyed:
                    self.state = GameState.OVER
                    self.winner = target.name
                elif target_is_destroyed:
                    self.state = GameState.OVER
                    self.winner = shooter.name  
        
        target_event = self.add_event(
            EventType.SHOT,
            shooter="Relay and Planets reaction",
            target=shooter.name,
            coords=coords,
            shot_results=shooter_field_updates,
            planets_anchors=shooter_planets_positions,
            destroyed_cells=self.get_player_meta(shooter.name)["destroyed_cells"]
        )
        shooter_event = self.add_event(
            EventType.SHOT,
            shooter=shooter.name,
            target=target.name,
            coords=coords,
            shot_results=target_field_updates,
            planets_anchors=target_planets_positions,
            destroyed_cells=self.get_player_meta(target.name)["destroyed_cells"]
        )
        logger.info(self.get_player_meta(shooter.name)["destroyed_cells"])
        logger.info(self.get_player_meta(target.name)["destroyed_cells"])
        return (shooter_event, target_event)


    # TODO NOT USED: REMOVE OR REFACTOR
    # def normalize_eids(self) -> None:
    #     """
    #     Placing wrong creates a lot of gc instances
    #     This method brings eid back to numeration from 0
    #     """
    #     if not self._players: raise GameException("Unable to normalize eids: No players")
    #     for player in self._players.values():
    #         player.normalize_eids()


    def ready(self) -> LobbyEvent:
        """
        Tries to proceed to setup state if possible.
        TODO: move sizes into entity instance
        """
        self.check_state(GameState.LOBBY)
        if len(self._players) != 2: raise GameException("Must be 2 players to initialize setup state")
        sizes = {
            EntityType.CORVETTE: 1,
            EntityType.FRIGATE: 2,
            EntityType.DESTROYER: 3,
            EntityType.CRUISER: 4,
            EntityType.PLANET: 1,
            EntityType.RELAY: 1,
        }

        players_meta = []

        for player in self._players.values():
            cells_available = len(player.field.useful_cells_coords)
            if cells_available == 0:
                raise GameException(f"Can't initialize setup state: {player} doesn't have a field")

            estimated_cells = 0
            for etype, amount in player.pending_entities.items():
                estimated_cells += 3.15 * amount * sizes[etype]
            if estimated_cells >= cells_available:
                raise GameException(f"Can't initialize setup state: {player} wouldn't be able to place all it's entities. Change amount or entity types {estimated_cells}>={cells_available}")
            if estimated_cells == 0:
                raise GameException(f"Can't initialize setup state: {player} doesn't have pending entities list")
            players_meta.append(self.get_player_meta(player.name))

        previous_state = self.state
        self.state = GameState.SETUP
        
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.STATE_CHANGED,
            payload={
                "previous_state": previous_state,
                players_meta[0]["name"]: players_meta[0],
                players_meta[1]["name"]: players_meta[1],
            }
        )
        return event

    def start(self) -> LobbyEvent:
        """
        Tries to proceed to active state if possible.
        """
        self.check_state(GameState.SETUP)

        for player in self._players.values():
            if len(player.entities.values()) == 0: raise GameException(f"{player} doesn't have any placed entities")
            for amount_unplaced in player.pending_entities.values():
                if amount_unplaced != 0: raise GameException(f"{player} hasn't placed all their entities")
        
        previous_state = self.state
        self.state = GameState.ACTIVE
        
        players_meta = []
        for name, player in self._players.items():
            updated_meta = self.get_player_meta(name)
            entities = []
            planets = []
            orbit_cells = set()
            
            for entity in player.entities.values():
                entities.append((entity.type, entity.cells_occupied))
                if entity.type == EntityType.PLANET:
                    planets.append(entity.anchor)
                    for coords in entity.orbit_cells:
                        orbit_cells.add(coords)

            updated_meta.update({
                "entities": entities,
                "planets": planets,
                "orbit_cells": list(orbit_cells)
            })
            players_meta.append(updated_meta)
        
                
        event = self.add_event(
            EventType.LOBBY,
            lobby_event=LobbyEventType.STATE_CHANGED,
            payload={
                "previous_state": previous_state,
                players_meta[0]["name"]: players_meta[0],
                players_meta[1]["name"]: players_meta[1],
            }
        )
        return event


    def get_player_names(self) -> list[str]:
        """
        Returns list of names present in game.
        """
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
            self.check_state(GameState.OVER)
            return self.winner
        except GameException: return

    def check_state(self, state: GameState) -> None:
        """
        Raises error if current state not match expected one.
        """
        if state != self.state: raise GameException(f"Wrong game state {self.state}. {state} expected.")


    def __repr__(self):
        return f"{self.id} {self.state}"