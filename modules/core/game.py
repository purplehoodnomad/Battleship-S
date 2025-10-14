import logging
import random
from typing import Optional

from modules.core.player import Player

from modules.common.events import Event, LobbyEvent, PlaceEvent, ShotEvent
from modules.common.exceptions import GameException, FieldException
from modules.common.enums import GameState, EntityType, EntityStatus, CellStatus, EventType, LobbyEventType
from modules.common.utils import invert_output


logger = logging.getLogger()


class Game:
    """
    Manages players and their rights. Interface for renderer structures - CLI or endpoints.
    """
    def __init__(self, id: str = "Game"):
        
        if not id or id is None:
            self.id = "Game"
        else:
            self.id = str(id)
        
        self._players: dict[str, Player] = {} # {name: Player}
        self.order: list[str] = [] # order of turns [name1, name2..]
        
        self.turn = 0
        self.state = GameState.LOBBY
        
        self.winner: str = None # name of winner if there any # type: ignore
        self.events: list[Event] = []


    def _append_event(self, event: Event):
        """
        Appends event to event listm logs it and returns event to caller.
        """
        self.events.append(event)
        logger.debug(f"Event {len(self.events)}: {event}")
        return event        


    def add_lobby_event(self, lobby_event: LobbyEventType, payload: dict) -> LobbyEvent:
        try:
            names = self.get_player_names()
        except GameException:
            names = []
        
        event = LobbyEvent(
            game_state=self.state,
            event_type=EventType.LOBBY,
            player_1=names[0] if names else None,
            player_2=names[1] if len(names) > 1 else None,
            turn_order=self.order,
            winner=self.winner,
            lobby_event=lobby_event,
            payload=payload,
        )
        return self._append_event(event) # type: ignore
    

    def add_shot_event(
        self,
        /,
        shooter: str,
        target: str,
        coords: tuple,
        shot_results: dict,
        planets_anchors: list,
        destroyed_cells: list,
    ) -> ShotEvent:
        event = ShotEvent(
            game_state=self.state,
            event_type=EventType.SHOT,
            turn=self.turn,
            shooter=shooter,
            target=target,
            coords=coords,
            shot_results=shot_results,
            planets_anchors=planets_anchors,
            destroyed_cells=destroyed_cells,
        )
        return self._append_event(event) # type: ignore


    def add_place_event(
        self,
        /,
        player_name: str,
        entity_id: int,
        entity_type: EntityType,
        anchor: tuple,
        rotation: int,
        cells_occupied: list,
        radius: Optional[int] = None,
        orbit_cells: Optional[list] = None,
        orbit_center: Optional[tuple] = None,
    ) -> PlaceEvent:
        event = PlaceEvent(
            game_state=self.state,
            event_type=EventType.PLACE,
            player_name=player_name,
            entity_id=entity_id,
            entity_type=entity_type,
            anchor=anchor,
            rotation=rotation,
            cells_occupied=cells_occupied,
            radius=radius,
            orbit_cells=orbit_cells,
            orbit_center=orbit_center,
        )
        return self._append_event(event) # type: ignore


    def _get_player(self, name: str) -> Player:
        """
        Allows to get access to player instance directly.
        Used by game. To get safe information - use get_player_meta().
        """
        if not self._players:
            raise GameException("No players in current game")
        try:
            return self._players[name]
        except KeyError:
            raise GameException(f"No Player {name} in game")


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


    def set_player(self, name: str, color: str) -> LobbyEvent:
        """
        Names are unique identificators.
        """
        self.check_state(GameState.LOBBY)

        if len(self._players) >= 2:
            raise GameException("Now game supports 2 players only")
        
        if str(name) in self._players:
            raise GameException(f"{name} is already in game. Give unique name")
        player = Player(name, color)
        
        self._players[player.name] = player
        self.order.append(player.name)

        event = self.add_lobby_event(
            lobby_event=LobbyEventType.PLAYER_ADDED,
            payload=self.get_player_meta(player.name)
        )
        return event


    def del_player(self, name: str) -> LobbyEvent:
        """
        Completely deletes player from the game. Moves order so 2nd player becomes 1st.
        """
        self.check_state(GameState.LOBBY)
        meta = self.get_player_meta(name)

        self.order.remove(name)
        del self._players[name]

        event = self.add_lobby_event(
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
        
        event = self.add_lobby_event(
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event
      

    def change_entity_list(self, name: str, etypes: dict[EntityType, int]) -> LobbyEvent:
        """
        Changes entities amount for player which are present in types dict.
        """
        player = self._get_player(name)
        self.check_state(GameState.LOBBY)

        for etype, amount in etypes.items():
            
            if not isinstance(amount, int):
                raise TypeError("Amount of entity type must be integer")
            
            amount = amount or 0
            amount = 0 if amount < 0 else amount
            player.pending_entities[etype] = int(amount)

        event = self.add_lobby_event(
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event


    def change_player_field(self, name: str, shape: str, params: list) -> LobbyEvent:
        
        self.check_state(GameState.LOBBY)
        player = self._get_player(name)
        
        player.set_field(shape, params)
        
        event = self.add_lobby_event(
            lobby_event=LobbyEventType.PLAYER_CHANGED,
            payload=self.get_player_meta(name)
        )
        return event


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
        
        radius, orbit_cells, orbit_center = None, None, None
        if entity_metadata["etype"] == EntityType.PLANET:
            radius = entity_metadata["radius"]
            orbit_cells = entity_metadata["orbit_cells"]
            orbit_center = entity_metadata["orbit_center"]
        
        event = self.add_place_event(
            player_name=name,
            entity_id=entity_metadata["eid"],
            entity_type=entity_metadata["etype"],
            anchor=entity_metadata["anchor"],
            rotation=entity_metadata["rotation"],
            cells_occupied=entity_metadata["cells_occupied"],
            radius=radius or None,
            orbit_cells=orbit_cells or None,
            orbit_center=orbit_center or None,
        )
        return event


    def autoplace(self, name: str) -> tuple[list[PlaceEvent], str]:
        """
        Autoplaces all remaining ships of player.
        Returns tuple: list of placement events proceeded during autoplace and summary.
        """
        player = self._get_player(name)
        autoplace_events = []
        attempts_limit = 50000
        all_attempts_counter = 0

        for entity, amount in reversed(player.pending_entities.items()): # starts with big ones first - planet to be exact
            
            if amount == 0:
                continue
            
            counter = 0
            for _ in range(amount):
                success = False
                while not success:
                    
                    if counter >= attempts_limit:
                        logger.info(f"Autoplacement for {player} not finished. Iteration limit({attempts_limit}) for entity reached. Took {all_attempts_counter} iterations in total.")
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
                        logger.info(f"Autoplaced {event.entity_type}-{event.entity_id} on {counter} iteration.")
                        
                        autoplace_events.append(event)
                        success = True
                    
                    except FieldException:
                        continue
        
        logger.info(f"Autoplacement for {player} finished in {all_attempts_counter} iterations.")
        return (autoplace_events, f"Autoplacement successfull. Took {all_attempts_counter} iterations in total")


    def shoot(self, shooter_name: str, coords: tuple) -> tuple[ShotEvent, ShotEvent]:
        """
        Initiates shoot event and return results for both players.
        Returns 2 events: first is for shooter field and the second is for target field.
        (Planet movements, relay refractions)
        """
        self.check_state(GameState.ACTIVE)
        shooter = self._get_player(shooter_name)
        
        if self.whos_turn() != shooter.name:
            raise GameException(f"{shooter.name} cant shoot now, it's {self.whos_turn()}'s turn")

        # getting opponent's instance
        names = self.get_player_names()
        names.remove(shooter.name)
        target = self._get_player(names[0])

        # shot itself
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

            for yx, status in planet_movement_results.items():
                
                if status == CellStatus.HIT:
                    if player == target:
                        target_field_updates.update({yx: status})
                    else:
                        shooter_field_updates.update({yx: status})
                else:
                    if player == target:
                        target_planets_positions.append(yx)
                    else:
                        shooter_planets_positions.append(yx)
        
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
        
        shooter_event = self.add_shot_event(
            shooter="Relay and Planets reaction",
            target=shooter.name,
            coords=coords,
            shot_results=shooter_field_updates,
            planets_anchors=shooter_planets_positions,
            destroyed_cells=self.get_player_meta(shooter.name)["destroyed_cells"]
        )
        target_event = self.add_shot_event(
            shooter=shooter.name,
            target=target.name,
            coords=coords,
            shot_results=target_field_updates,
            planets_anchors=target_planets_positions,
            destroyed_cells=self.get_player_meta(target.name)["destroyed_cells"]
        )
        logger.info(f"{shooter} shot {shooter.field.get_cell(coords)}: {result}")
        return (shooter_event, target_event)


    def ready(self) -> LobbyEvent:
        """
        Tries to proceed to setup state if possible.
        TODO: move sizes into entity instance
        """
        self.check_state(GameState.LOBBY)
        if len(self._players) != 2:
            raise GameException("Must be 2 players to initialize setup state")
        
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
                # empirical formula which allows to roughly evaluate if these objects can fit on given field
                estimated_cells += 3.4 * amount * sizes[etype]
            
            if estimated_cells >= cells_available:
                raise GameException(f"Can't initialize setup state: {player} wouldn't be able to place all it's entities. Change amount or entity types {estimated_cells}>={cells_available}")
            
            if estimated_cells == 0:
                raise GameException(f"Can't initialize setup state: {player} doesn't have pending entities list")
            
            players_meta.append(self.get_player_meta(player.name))

        previous_state = self.state
        self.state = GameState.SETUP
        
        event = self.add_lobby_event(
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
            if len(player.entities.values()) == 0:
                raise GameException(f"{player} doesn't have any placed entities")
            
            for amount_unplaced in player.pending_entities.values():
                if amount_unplaced != 0:
                    raise GameException(f"{player} hasn't placed all their entities")
        
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
        
                
        event = self.add_lobby_event(
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
        if not self._players:
            raise GameException("No players in current game")
        
        return list(self._players.keys())
  
    def whos_turn(self) -> str:
        """
        Converts current turn into index and returns name of player.
        """
        if not self.order:
            raise GameException("Order is empty. No players set")
        
        return self.order[(self.turn) % len(self.order)]
    
    def whos_winner(self) -> str|None:
        try:
            self.check_state(GameState.OVER)
            return self.winner
        
        except GameException:
            return

    def check_state(self, state: GameState) -> None:
        """
        Raises error if current state not match expected one.
        """
        if state != self.state:
            raise GameException(f"Wrong game state {self.state}. {state} expected")


    def __repr__(self):
        return f"{self.id} {self.state}"