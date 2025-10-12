from dataclasses import dataclass
from enum import Enum

class EntityException(Exception): pass
class FieldException(Exception): pass
class PlayerException(Exception): pass
class GameException(Exception): pass


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
    radius: int = None
    orbit_cells: list = None
    orbit_center: tuple = None



def convert_input(coords: str) -> tuple[int, int]:
    """
    Converts human input to game expected parameters.
    E.g.: A10 →(9, 0); J2 →(3, 9)
    """
    Y_coord, X_coord = -1, -1
    for i in range (26):
        letter = chr(i + ord("A"))
        if coords[0] == letter:
            X_coord = ord(letter) - ord("A")
            Y_coord = int(coords.replace(letter, "")) - 1
            break
    if X_coord == -1:
        raise ValueError(f"{coords}: Coordinates must be in 'CRR' format")
    return (Y_coord, X_coord)

def invert_output(coords: tuple[int, int]) -> str:
    """
    Inverts game coordinates format to human one.
    E.g.: (9, 0) →A10; (3, 9) →J2
    """
    if not isinstance(coords, tuple) or not isinstance(coords[0], int) or not isinstance(coords[1], int):
        raise ValueError(f"{coords}: Must be tuple of two integers: (y, x)")
    y, x = coords
    letter = chr(x + ord("A"))
    num = str(y + 1)
    return letter + num


def circle_coords(radius: int, center = (0, 0)) -> list:
    """
    Uses Bresenghem algorithm to draw circle border with given radius and center.
    Returns list of (y, x) of drawn edges
    """
    y0, x0 = center
    if radius == 0:
        return [center]

    circle = set()
    x = 0
    y = radius
    d = 1 - radius

    while x <= y:
        points_of_symmetry = [
            (y0 + y, x0 + x), (y0 - y, x0 + x),
            (y0 + y, x0 - x), (y0 - y, x0 - x),
            (y0 + x, x0 + y), (y0 - x, x0 + y),
            (y0 + x, x0 - y), (y0 - x, x0 - y),
        ]
        for p in points_of_symmetry:
            circle.add(p)    
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return list(circle)

def sort_circle_coords(center: tuple, coords) -> list:
    """
    Sorts circle coords by angle.
    Suggests that circle has to gaps.
    Makes it possible to move planet by iterating coords list.
    """
    from math import atan2, pi
    points_with_angles = []
    y0, x0 = center

    for point in coords:
        y, x = point
        angle = atan2(y - y0, x - x0)
        if angle < 0: angle += 2 * pi # normilizes to start from 0 to 2pi
        points_with_angles.append((angle, point))

    points_with_angles.sort(key=lambda point: point[0])
    return [point for angle, point in points_with_angles] 


def ngon_coords(*, n: int, radius: int, center = (0, 0), angle = 0) -> list:
    """
    Uses Bresenghem algorithm to draw polygon border with given radius, center and angle
    Returns list of (y, x) of drawn edges
    """
    from math import sin, cos, pi, ceil
    angle = angle/180 * pi
    y0, x0 = center
    if radius == 0:
        return [center]
    
    points = []
    if n == 3:
        for i in range(n):
            y = int(ceil(y0 + radius*sin(2*pi*i/n + angle)))
            x = int(ceil(x0 + radius*cos(2*pi*i/n + angle)))
            points.append((y, x))
    else:
        for i in range(n):
            y = int(round(y0 + radius*sin(2*pi*i/n + angle)))
            x = int(round(x0 + radius*cos(2*pi*i/n + angle)))
            points.append((y, x))       
    
    coords = set()
    for i in range(-1, len(points)-1):
        y1, x1 = points[i]
        y2, x2 = points[i+1]

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            coords.add((y1, x1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    return list(coords) 