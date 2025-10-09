import logging
from cli.cli_terminal import STerminal, CLIDrawer, CLIField, CLITalker
from modules.game import Game
from modules.bots import Randomer, Hunter
from modules.enums_and_events import CellStatus, EntityType

logger = logging.getLogger(__name__)

class CLIRenderer:
    def __init__(self, term: STerminal):
        self.term = term
        self.game = Game()
        self.talker = CLITalker(term)
        self.drawer = CLIDrawer(term)
        self.players: dict[str, dict]= {} # {name: {info: value}}
        self.bots = {} # {playername: BotType}
    

    def update_screen(self) -> None:
        """
        Uses strings got from cli_terminal methods
        Collects them into one large string and prints it
        Completely redraws whole CLI
        """
        screen = ""
        screen += self.drawer.wipe_screen()

        try: names = self.game.get_player_names()
        except: pass

        winner = self.game.whos_winner() # used to show winscreen and decide whether or not showing enemy ships
        show_ships = winner is not None

        y, x = 0, 0
        y_end = y
        if self.players:
            for player in self.players.values():
                screen += player["field"].draw((y, x), player["color"])
                x += player["width"] * 2 + 4
                y_end = max((y_end, player["height"]))
        y = y_end + 1
        x = 0
        screen += self.drawer.draw_separator(y, x) # draws board lines and game title
        screen += self.talker.talk() # prints all line history available

        if winner is not None:
            screen += self.talker.show_winner(winner)
        
        self.term.fl(screen)
        

    def set_player(self, name: str, color: str, ai = None):
        """
        Tries to add Player instance to Game.
        Prints result.
        """
        event = self.game.set_player(name, color)
        player = self.players[name] = event.payload
        player["field"] = CLIField(self.term, player["real_cells"], player["height"], player["width"])

        if ai is not None:
            if ai == "randomer":
                self.bots[name] = Randomer()
            elif ai == "hunter":
                self.bots[name] = Hunter()

        self.talker.talk(f"<{self.term.paint(name, self.players[name]['color'])}> added")

    def get_players(self):
        """
        Prints a list of all added players.
        """
        output = "Players:\n"
        if not self.players:
            self.talker.talk("No players in game. Type `add`")
            return
        
        for name in self.players:
            output += f"  > {self.term.paint(name, self.players[name]["color"])}:\t"
            output = output[:-2] + "\n"

        self.talker.talk(output.strip("\n"))

    def delete_player(self, name):
        event = self.game.del_player(name)
        payload = event.payload
        
        del self.players[name]
        
        if payload['order'] == 0:
            for name in self.players.keys():
                self.players[name]["order"] -= 1
        
        self.talker.talk(f"<{self.term.paint(payload['name'], payload['color'])}> deleted")

    def color(self, name: str, color: str):
        event = self.game.change_player_color(name, color)
        self.players[name].update(event.payload)
        self.talker.talk(f"<{self.term.paint(name, color)}> color changed")


    def set_player_field(self, name: str, shape: str, params = [9, 9]):

        event = self.game.change_player_field(name, shape, params)
        player = self.players[name] = event.payload
        player["field"] = CLIField(self.term, player["real_cells"], player["height"], player["width"])
        self.talker.talk(f"<{self.term.paint(name, self.players[name]["color"])}> field now is {shape}: {params}")
    

    def entity_amount(self, name, etype, amount):
        event = self.game.change_entity_list(name, {etype: amount})
        self.players[name].update(event.payload)

    
    def proceed_to_setup(self):
        event = self.game.ready()
        payload = event.payload
        
        for name in self.game.get_player_names():
            player_data = payload[name]
            self.players[name].update(payload[name])
            self.players[name]["field"] = CLIField(self.term, player_data["real_cells"], player_data["height"], player_data["width"])
        
        self.talker.talk(self.term.paint("Setup state is running. Use `place` to place your ships.", "orange"), loud = True)
    
    
    def place_entity(self, name: str, type_value: str, icoords: str, r: str):
        match type_value.upper():
            case "1"|"CORVETTE":
                etype = EntityType.CORVETTE
            case "2"|"FRIGATE":
                etype = EntityType.FRIGATE
            case "3"|"DESTROYER":
                etype = EntityType.DESTROYER
            case "4"|"CRUISER":
                etype = EntityType.CRUISER
            case "6"|"RELAY":
                etype = EntityType.RELAY
            case "7"|"PLANET":
                etype = EntityType.PLANET
            case _:
                etype = EntityType.UNIDENTIFIED

        coords = self.convert_input(icoords)
        event = self.game.place_entity(name, etype, coords, int(r))
        if etype == EntityType.PLANET:
            self.players[name]["field"].orbits.append(event.orbit_cells)
            self.players[name]["field"].planets.append(event.anchor)
        else:
            self.players[name]["field"].mark_cells_as(event.cells_occupied, CellStatus.ENTITY)

        self.talker.talk(f"<{self.term.paint(name, self.players[name]["color"])}> placed entity sucsessfully")
    

    def autoplace(self, name: str):
        """
        Autoplaces all remain ships
        """
        events, result = self.game.autoplace(name)
        for event in events:
            if event.entity_type == EntityType.PLANET:
                self.players[name]["field"].orbits.append(event.orbit_cells)
                self.players[name]["field"].planets.append(event.anchor)
            else:
                self.players[name]["field"].mark_cells_as(event.cells_occupied, CellStatus.ENTITY)

        self.talker.talk(f"<{name}>: {result}")


    def convert_input(self, coords: str) -> tuple[int, int]:
        """
        Converts human input to game expected parameters.
        E.g. A10 to (9, 0); J2 to (3, 9)
        """
        Y_coord, X_coord = None, None
        for i in range (26):
            letter = chr(i + ord("A"))
            if coords.upper()[0] == letter:
                X_coord = ord(letter) - ord("A")
                Y_coord = int(coords.replace(letter, "")) - 1
                break
        if X_coord is None: raise ValueError("Coordinates must be in 'CRR' format")
        return (Y_coord, X_coord)
    
    def invert_output(self, coords: tuple[int, int]) -> str:
        """
        
        """
        y, x = coords
        letter = chr(x + ord("A"))
        num = str(y + 1)
        return letter + num


    def start(self):
        event = self.game.start()
        payload = event.payload
        
        for name in self.players.keys():
            player_data = payload[name]
            self.players[name].update(player_data)
            self.players[name]["field"] = CLIField(self.term, player_data["real_cells"], player_data["height"], player_data["width"])
            self.players[name]["field"].orbits = player_data["orbit_cells"]
            self.players[name]["field"].planets = player_data["planets"]
            
            for entity, cells_occupied in player_data["entities"]:
                if entity == EntityType.RELAY:
                    self.players[name]["field"].mark_cells_as(cells_occupied, CellStatus.RELAY)
                elif entity == EntityType.PLANET:
                    continue
                else:
                    self.players[name]["field"].mark_cells_as(cells_occupied, CellStatus.ENTITY)

        
        self.talker.talk(self.term.paint("Game started. Use `sh` to shoot.", "blue"), loud = True)

    
    def shoot(self, shooter: str, coords: tuple[int, int] | str):
        """
        Can take both coord formats: (y,x) and "A1"
        """
        if isinstance(coords, str):
            coords = self.convert_input(coords)
        
        events = self.game.shoot(shooter, coords)
        results = {}
        for event in events:
            results[event.target] = []
            for coords, result in event.shot_results.items():
                self.players[event.target]["field"].mark_cells_as([coords], result)
                results[event.target].append((coords, result))
                self.players[event.target]["field"].planets = event.planets_anchors
        
        self.talker.talk(f"{shooter} shot {self.invert_output(coords)}.")

        output: dict[str, str] = {}
        for name, shots in results.items():
            parts: list[str] = []
            for position, status in shots:
                parts.append(f"{self.invert_output(position)}: {str(status).replace('CellStatus.', '')}")
            output[name] = ";\n".join(parts) + (";" if parts else "")

        self.talker.talk(f" Results: {output}")

        return events


    def automove(self, name: str):
        if name not in self.bots:
            return

        names = list(self.players.keys())
        names.remove(name)
        target = names[0]

        bot = self.bots[name]
        if not bot.opponent_field:
            bot.opponent_field = {coords: CellStatus.FREE for coords in self.players[target]["real_cells"]}

        bots_coords_choose = self.bots[name].shoot()
        events = self.shoot(name, bots_coords_choose)
        for event in events:
            if event.target == target:
                for coords, result in event.shot_results.items():
                    if result in (CellStatus.MISS, CellStatus.HIT):
                        bot.shot_result(coords, result)
                bot.validate_destruction(event.destroyed_cells)
                break
                    
