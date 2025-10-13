from enum import Enum


class EntityStatus(Enum):
    NOTPLACED = 0
    FULLHEALTH = 1
    DAMAGED = 2
    DESTROYED = 3


class EntityType(Enum):
    UNIDENTIFIED = 0
    CORVETTE = 1
    FRIGATE = 2
    DESTROYER = 3
    CRUISER = 4
    # BATTLESHIP = 5
    RELAY = 6
    PLANET = 7


class GameState(Enum):
    LOBBY = 1
    SETUP = 2
    ACTIVE = 3
    OVER = 4


class CellStatus(Enum):
    """
    Used mainly as shot results.
    """
    VOID = 0
    FREE = 1
    MISS = 2
    ENTITY = 3
    HIT = 4
    DESTROYED = 5
    ORBIT = 6
    PLANET = 7
    RELAY = 8


class EventType(Enum):
    PLACE = 1
    SHOT = 2
    LOBBY = 3


class LobbyEventType(Enum):
    STATE_CHANGED = 0
    PLAYER_ADDED = 1
    PLAYER_DELETED = 2
    PLAYER_CHANGED = 3