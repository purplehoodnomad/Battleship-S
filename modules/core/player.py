import logging

from modules.core.field import Field
from modules.core.entities import Entity, Ship, Planet, Relay

from modules.common.enums import CellStatus, EntityType, EntityStatus
from modules.common.exceptions import PlayerException
from modules.common.utils import invert_output


logger = logging.getLogger(__name__)


class Player:
    """
    Stores all methods and instances that player can have.
    """
    def __init__(self, name = None, color = "white"):

        if not name or name is None:
            raise PlayerException("Give me a name!")
        else: self.name = str(name)

        # list of entities which are must be set before game starts
        self.pending_entities = {}
        for model in list(EntityType):
            self.pending_entities[model] = 0
        del self.pending_entities[EntityType.UNIDENTIFIED]

        self.entities: dict[int, Entity] = {} # actual set entities {Entity.eid: Entity}

        self.field = Field(name=self.name)
        self.colorize(color)

        logger.info(f"Created {self}")
    

    def colorize(self, color = "white") -> None:
        if color in ("blue", "green", "orange", "pink", "purple", "red", "yellow", "white"):
            self.color = color
            logger.info(f"Changed color to {self.color} for {self}")
        else:
            self.color = "white"
            logger.info(f"{self} tried to be unsupported {color}. Changed it to {self.color} instead")


    def get_entity(self, eid: int) -> Entity:
        """
        Returns entity instance by given entity id.
        """
        try:
            return self.entities[eid]
        except KeyError:
            raise PlayerException(f"{self} has no entity with eid={eid}")


    def set_field(self, shape: str, params: list) -> None:
        """
        Sets field by parsing parameters to field method.
        """
        self.field = Field(shape, params, name=self.name)
        
        logger.info(f"Field {self.field} set for {self}")


    def place_entity(self, etype: EntityType, params: list) -> dict:
        """
        It creates entity instance - that's necessary for attempt to place entity where player has chosen.
        If attempt is not valid - this instace is left to garbage collector and not put to player.entities dict.
        Ships or Relay: params = [coords: tuple, rotation: int];
        Planet: params = [coords: tuple, orbit_radius: int].
        If placed - returns entity metadata dict.
        """

        if self.pending_entities[etype] <= 0:
            raise PlayerException(f"{self} has no {etype} available to place")
        
        if etype in (
            EntityType.CORVETTE,
            EntityType.FRIGATE,
            EntityType.DESTROYER,
            EntityType.CRUISER,
            EntityType.RELAY
        ):
            coords = params[0] 
            rot = params[1]
            if etype == EntityType.RELAY:
                entity = Relay()
            else:
                entity = Ship(etype)
            self.field.occupy_cells(entity, coords, rot)   

        elif etype == EntityType.PLANET:
            coords = params[0]
            orbit_radius = params[1]
            entity = Planet(orbit_radius, coords)
            self.field.setup_a_planet(entity)
        else:
            raise PlayerException(f"{etype} is not implemented")
        
        self.pending_entities[etype] -= 1
        self.entities[entity.eid] = entity
        
        logger.info(f"{self} placed: {entity}")

        return entity.metadata


    def take_shot(self, coords: tuple[int, int]) -> CellStatus:
        """
        Parses shot parameters to Field method.
        """
        return self.field.take_shot(coords)


    def move_planets(self, value = 1) -> dict[tuple[int, int], CellStatus]:
        """
        Moves all player's planets on their orbit by value.
        Returns dict {coords: status} with updated planets position.
        Manages with planet collision either.
        """
        
        # gets all planets on the field which are not destroyed yet
        planets = [planet for planet in self.entities.values() if planet.type == EntityType.PLANET and planet.status != EntityStatus.DESTROYED]
        
        updated_cells = {}
        for planet in planets:
            planet.position += value # moves planet forward on their orbits, usually with default step 1
            updated_cells[planet.anchor] = CellStatus.PLANET

        # takes all pairs of planets and checks if they're collided
        for planet1 in planets:
            for planet2 in planets:
                # it's basically same object - skips
                if planet1.eid == planet2.eid:
                    continue
                
                if planet1.anchor == planet2.anchor and planet1.anchor:
                    logger.info(f"{self} Planets collided on cell {invert_output(planet1.anchor)}{planet1.anchor}: {planet1} with {planet2}")
                    updated_cells[planet1.anchor[:]] = CellStatus.HIT # rewrites information on this cell as hit event
                    planet1.status = EntityStatus.DESTROYED
                    planet2.status = EntityStatus.DESTROYED

        return updated_cells


    def __str__(self):
        return f"{self.name}"
    
    def __repr__(self):
        return f"Player: name={self.name}, color={self.color}, field={self.field}, pending={self.pending_entities}, entities={self.entities}"