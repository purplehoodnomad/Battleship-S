from dataclasses import dataclass
from modules.common.enums import CellStatus, GameState, EventType, LobbyEventType


@dataclass
class Event:
    """
    Base event class
    """
    game_state: GameState
    event_type: EventType

@dataclass
class ShotEvent(Event):
    turn: int
    shooter: str
    target: str
    coords: tuple
    shot_results: dict[tuple[int, int], CellStatus]
    planets_anchors: list[tuple[int, int]]
    destroyed_cells: list[tuple[int, int]]

@dataclass
class LobbyEvent(Event):
    player_1: str
    player_2: str
    turn_order: list
    winner: str
    lobby_event: LobbyEventType
    payload: dict

@dataclass
class PlaceEvent(Event):
    player_name: str
    entity_id: int
    entity_type: str
    anchor: tuple
    rotation: int
    cells_occupied: list
    radius: int
    orbit_cells: list
    orbit_center: tuple