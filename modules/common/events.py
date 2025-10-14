from dataclasses import dataclass
from typing import Optional, Iterable

from modules.common.enums import EntityType, CellStatus, GameState, EventType, LobbyEventType


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
    lobby_event: LobbyEventType
    turn_order: list[str]
    payload: dict
    player_1: Optional[str] = None
    player_2: Optional[str] = None
    winner: Optional[str] = None

@dataclass
class PlaceEvent(Event):
    player_name: str
    entity_id: int
    entity_type: EntityType
    anchor: tuple[int, int]
    rotation: int
    cells_occupied: list[tuple[int, int]]
    radius: Optional[int] = None
    orbit_cells: Optional[list[tuple[int, int]]] = None
    orbit_center: Optional[tuple[int, int]] = None