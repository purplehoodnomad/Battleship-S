from abc import ABC, abstractmethod

class Entity(ABC):
    def __init__(self):

        self.isPlaced = False
        self.x = 0
        self.y = 0

class Ship(Entity):
    pass

class Space_Object(Entity):
    pass

class Construction(Entity):
    pass