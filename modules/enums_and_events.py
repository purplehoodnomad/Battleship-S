# from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from modules.entities import Entity

EntityType = Entity.Type
EntityStatus = Entity.Status
class GameState(Enum):
    LOBBY = 1
    SETUP = 2
    ACTIVE = 3
    OVER = 4

class CellStatus(Enum):
    VOID = 0
    FREE = 1
    MISS = 2
    ENTITY = 3
    HIT = 4
    DESTROYED = 5

class EventType(Enum):
    PLACEMENT = 1
    SHOT = 2
    LOBBY = 3

class LobbyEventType(Enum):
    PLAYER_ADDED = 1
    PLAYER_DELETED = 2
    PLAYER_CHANGED = 3


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
    shot_result: CellStatus

@dataclass
class LobbyEvent(Event):
    player_1: str
    player_2: str
    winner: str
    lobby_event: LobbyEventType
    payload: dict