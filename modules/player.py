import logging
from modules.field import Field
from modules.entities import Entity, Ship


logger = logging.getLogger(__name__)


class PlayerException(Exception): pass
class Player:
    """
    Stores all methods and instances that player can have.
    """
    def __init__(self, name = None, color = "white"):

        if not name or name is None: raise PlayerException("Give me a name!")
        else: self.name = str(name)
        self.field = None
        self.colorize(color)

        # list of entities which are must be set before game starts
        self.pending_entities = {}
        for model in list(Entity.Type):
            self.pending_entities[model] = 0
        del self.pending_entities[Entity.Type.UNIDENTIFIED]

        self.entities = {} # actual set entities {Entity.eid: Entity}

        logger.info(f"{self} created")
    

    def colorize(self, color = "white") -> None:
        if color in ("blue", "green", "orange", "pink", "purple", "red", "yellow", "white"):
            self.color = color
            logger.info(f"{self} changed color to {self.color}.")
        else:
            self.color = "white"
            logger.info(f"{self} tried to be {color}. Changed it to {self.color} instead")


    def place_entity(self, type_value: int, coords: tuple, rot: int) -> None:
        """
        It creates entity instance - that's necessary for attempt to place entity where player has chosen
        If attempt is not valid - this instace is left to garbage collector and not placed to player.entities dict
        Note that entity id numeration starts to be messed up at that point which is not big deal
        """
        try: etype = Entity.Type(type_value)
        except ValueError: raise PlayerException(f"{self}: tried to place non-existing type {type_value}")

        if self.pending_entities[etype] <= 0: raise PlayerException(f"{self} has no {etype} available to place")
        
        if type_value in (1, 2, 3, 4):
            entity = Ship(type_value)
        else: raise PlayerException("Other entities which are not ships are not implemented yet")

        self.field.occupy_cells(entity, coords, rot)
        self.pending_entities[etype] -= 1
        self.entities[entity.eid] = entity
        logger.info(f"{self} placed {self.entities[entity.eid].__repr__()}")
    

    def replace_entity(self, eid: int, coords: tuple, rot: int) -> None:
        """
        Allows to replace already placed 
        """
        entity = self.get_entity(eid)
        previous = entity.cells_occupied
        self.field.occupy_cells(entity, coords, rot)
        logger.info(f"{self} moved replaced {entity} from {previous} to {entity.cells_occupied}")

    
    def set_field(self, shape: str, params: list) -> None:
        self.field = Field(shape, params)
        logger.info(f"{self} {self.field} was set")


    def get_entity(self, eid: int) -> Entity:
        try: return self.entities[eid]
        except KeyError: raise PlayerException(f"{self} has no entity with eid={eid}")

    
    def get_field(self, *, private = False) -> dict:
        """
        Returns field state in readable format {(y,x): "state"}
        """
        if self.field is None: raise PlayerException(f"{self} has no field")

        public_field = {}
        for coords in self.field:
            cell = self.field.get_cell(coords)
            
            match (cell.is_void, cell.occupied_by, cell.was_shot):
                case (True, _, _):          symb = "void"
                case (_, occupied_by, True):
                    if occupied_by is None: symb = "miss"
                    else:                   symb = "hit"
                case (_, occupied_by, False):
                    if private and occupied_by is not None: symb = "object"
                    else:                   symb = "free"
            public_field[coords] = symb
        return public_field


    def take_shot(self, coords: tuple) -> str:
        return self.field.take_shot(coords)


    def str(self):
        return f"Player {self.name}"
    
    def __repr__(self):
        return f"Player: name={self.name}, color={self.color}, field={self.field}, pending={self.pending_entities}, entities={self.entities}"