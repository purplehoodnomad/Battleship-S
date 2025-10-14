from collections.abc import Iterable
from math import sin, cos, atan2, pi, ceil


def convert_input(coords: str) -> tuple[int, int]:
    """
    Converts human input to game expected parameters.
    E.g.: A10 →(9, 0); J2 →(3, 9).
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
    E.g.: (9, 0) →A10; (3, 9) →J2.
    """
    if not coords:
        return coords

    if not isinstance(coords, tuple) or not isinstance(coords[0], int) or not isinstance(coords[1], int):
        raise ValueError(f"{coords}: Must be tuple of two integers: (y, x)")
    
    y, x = coords
    
    letter = chr(x + ord("A"))
    num = str(y + 1)
    
    return letter + num


def circle_coords(radius: int, center = (0, 0)) -> list:
    """
    Uses Bresenghem algorithm to draw circle border with given radius and center.
    Returns list of (y, x) of drawn edges.
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


def sort_circle_coords(center: tuple[int, int], coords: Iterable[tuple[int, int]]) -> list:
    """
    Sorts circle coords by angle.
    Supposes that circle has to gaps.
    Makes it possible to move planet by iterating coords list.
    """
    points_with_angles = []
    y0, x0 = center

    for point in coords:
        y, x = point
        angle = atan2(y - y0, x - x0)
        
        if angle < 0:
            angle += 2 * pi # normilizes to start from 0 to 2pi
        
        points_with_angles.append((angle, point))

    points_with_angles.sort(key=lambda point: point[0])
    return [point for angle, point in points_with_angles] 


def ngon_coords(*, n: int, radius: int, center = (0, 0), angle = 0.0) -> list[tuple[int, int]]:
    """
    Uses Bresenghem algorithm to draw polygon border with given radius, center and angle.
    Returns list of (y, x) of drawn edges.
    """
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