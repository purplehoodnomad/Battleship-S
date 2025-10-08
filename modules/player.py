import logging
from modules.field import Field
from modules.entities import Entity, Ship, Planet, Relay
from modules.enums_and_events import CellStatus, EntityType, EntityStatus, PlayerException, EntityException, FieldException


logger = logging.getLogger(__name__)



class Player:
    """
    Stores all methods and instances that player can have.
    """
    def __init__(self, name = None, color = "white"):

        if not name or name is None: raise PlayerException("Give me a name!")
        else: self.name = str(name)

        # list of entities which are must be set before game starts
        self.pending_entities = {}
        for model in list(EntityType):
            self.pending_entities[model] = 0
        del self.pending_entities[EntityType.UNIDENTIFIED]

        self.entities = {} # actual set entities {Entity.eid: Entity}

        self.field = Field()
        self.colorize(color)
        self.is_ai = False

        logger.info(f"{self} created")
    

    def colorize(self, color = "white") -> None:
        if color in ("blue", "green", "orange", "pink", "purple", "red", "yellow", "white"):
            self.color = color
            logger.info(f"{self} changed color to {self.color}.")
        else:
            self.color = "white"
            logger.info(f"{self} tried to be {color}. Changed it to {self.color} instead")


    def get_entity(self, eid: int) -> Entity:
        try: return self.entities[eid]
        except KeyError: raise PlayerException(f"{self} has no entity with eid={eid}")


    def set_field(self, shape: str, params: list) -> None:
        self.field = Field(shape, params)
        logger.info(f"{self} {self.field} was set")


    def place_entity(self, etype: EntityType, params: list) -> dict:
        """
        It creates entity instance - that's necessary for attempt to place entity where player has chosen.
        If attempt is not valid - this instace is left to garbage collector and not put to player.entities dict.
        Ships or Relay: params = [coords: tuple, rotation: int];
        Planet: params = [coords: tuple, orbit_radius: int].
        If placed - returns entity metadata dict.
        """

        if self.pending_entities[etype] <= 0: raise PlayerException(f"{self} has no {etype} available to place")
        
        if etype in (
            EntityType.CORVETTE,
            EntityType.FRIGATE,
            EntityType.DESTROYER,
            EntityType.CRUISER,
        ):
            coords = params[0] 
            rot = params[1]
            entity = Ship(etype.value)
            self.field.occupy_cells(entity, coords, rot)

        elif etype == EntityType.RELAY:
            coords = params[0] 
            rot = params[1]
            entity = Relay()
            self.field.occupy_cells(entity, coords, rot)     

        elif etype == EntityType.PLANET:
            coords = params[0]
            orbit_radius = params[1]
            entity = Planet(orbit_radius, coords)
            self.field.setup_a_planet(entity)
        else:
            raise PlayerException("Other entities which are not ships are not implemented yet")
        
        self.pending_entities[etype] -= 1
        self.entities[entity.eid] = entity
        return entity.metadata


    def take_shot(self, coords: tuple[int, int]) -> CellStatus:
        return self.field.take_shot(coords)

    def move_planets(self, value = 1) -> dict[tuple[int, int], CellStatus]:
        """
        Moves all player's planets on their orbit by value.
        Returns dict {coords: status} with updated planets position.
        Manages with planet collision either.
        """
        
        updated_cells = {}
        planets = [planet for planet in self.entities.values() if planet.type == EntityType.PLANET and planet.status != EntityStatus.DESTROYED]
        
        for planet in planets:
            planet.position += value
            updated_cells[planet.anchor] = CellStatus.PLANET

        for planet in planets:
            for entity in self.entities.values():
                if planet.eid == entity.eid:
                    continue
                
                if entity.type == EntityType.PLANET and entity.anchor == planet.anchor:
                    updated_cells[planet.anchor] = CellStatus.HIT
                    entity.status = EntityStatus.DESTROYED
                    planet.status = EntityStatus.DESTROYED

        return updated_cells

    def __str__(self):
        return f"Player {self.name}"
    
    def __repr__(self):
        return f"Player: name={self.name}, color={self.color}, field={self.field}, pending={self.pending_entities}, entities={self.entities}"
    


    # NOT USED. REFACTOR OR DELETE LATER
    # def get_field(self, *, private = False) -> dict:
    #     """
    #     Returns field state in readable format {(y,x): "state"}
    #     """
    #     if self.field is None: raise PlayerException(f"{self} has no field")

    #     public_field = {}
    #     for coords in self.field:
    #         cell = self.field.get_cell(coords)
            
    #         match (cell.is_void, cell.occupied_by, cell.was_shot):
    #             case (True, _, _):
    #                 symb = CellStatus.VOID
    #             case (_, occupied_by, True):
    #                 if occupied_by is None:
    #                     symb = CellStatus.MISS
    #                 else:
    #                     symb = CellStatus.HIT
    #             case (_, occupied_by, False):
    #                 if private and occupied_by is not None:
    #                     if occupied_by.type == EntityType.PLANET:
    #                         if coords == occupied_by.anchor:
    #                             symb = CellStatus.PLANET
    #                         else:
    #                             symb = CellStatus.ORBIT
    #                     elif occupied_by.type == EntityType.RELAY:
    #                         symb = CellStatus.RELAY
    #                     else:
    #                         symb = CellStatus.ENTITY
    #                 else:
    #                     symb = CellStatus.FREE
    #         public_field[coords] = symb
    #     return public_field


    # NOT USED. REFACTOR OR DELETE LATER
    # def normalize_eids(self) -> dict:
    #     """
    #     Placing ships wrong creates a lot of gc instances
    #     This method brings eid back to numeration from 0
    #     """
    #     counter = 0
    #     normilized_entities = {}
    #     for entity in self.entities.values():
    #         entity.eid = counter
    #         normilized_entities[counter] = entity
    #         counter += 1
    #         logger.info(f"Normalization: {entity}")
        
    #     self.entities = normilized_entities
    #     Entity._counter = counter + 1
    #     return self.entities