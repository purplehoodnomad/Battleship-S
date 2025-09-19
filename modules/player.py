from modules.field import Field
from modules.entities import Entity, Ship

import logging


logger = logging.getLogger(__name__)

class PlayerException(Exception): pass
class Player:
    """
    Stores all methods and instances that player can have.
    """
    def __init__(self, name = None, color = "white"):

        if name is None: raise PlayerException("Give me a name!")
        else: self.name = str(name)
        logger.info(f"{self} created.")
        self.is_ready = False
        self.field = None
        self.colorize(color)

        self.pending_entities = {}
        for model in list(Entity.Type):
            self.pending_entities[model] = 0

        self.entities = {} # {Entity.eid: Entity}
    

    def colorize(self, color = "white"):
        if color in ("blue", "green", "orange", "pink", "purple", "red", "yellow", "white"):
            self.color = color
            logger.info(f"{self} changed color to {self.color}.")
        else: 
            self.color = "white"
            logger.info(f"{self} tried to take unsupported {color}. Changed it to white instead.")


    def setup_entity(self, model: Entity.Type, coords: tuple, rot: int):
        if model not in Entity.Type: raise PlayerException("Entity of this type does not exist.")
        if self.pending_entities[model] <= 0: raise PlayerException(f"No {entity} available to place.")
        try:
            if model.value in (1, 2, 3, 4, 5):
                entity = Ship(entity.value)
            self.field.occupy_cells(entity, coords, rot)
            self.pending_entities[model] -= 1
            self.entities[entity.eid] = entity
        except: raise PlayerException(f"Can't place {entity} here.")




    def get_entity(self, eid: int): return self.entities[eid]


    def __repr__(self):
        return f"Player {self.name}"
    

    def set_field(self, params): self.field = Field(params)