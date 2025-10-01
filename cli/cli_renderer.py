from cli.cli_terminal import STerminal, CLIDrawer, CLIField, CLITalker
from modules.game import Game
from modules.bots import Randomer, Hunter


class CLIRenderer:
    def __init__(self, term: STerminal):
        self.term = term
        self.game = Game()
        self.talker = CLITalker(term)
        self.drawer = CLIDrawer(term)
        self.p1_field: CLIField = None
        self.p2_field: CLIField = None
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

        if self.p1_field is not None: # tries to add latest state of field if player has it
            if names[0] not in self.bots: show_player_ships = True
            else: show_player_ships = show_ships
            self.p1_field.cells = self.game.get_player_field(names[0], private = show_player_ships)
            screen += self.p1_field.draw()
       
        if self.p2_field is not None:
            if names[1] not in self.bots: show_player_ships = True
            else: show_player_ships = show_ships
            self.p2_field.cells = self.game.get_player_field(names[1], private = show_player_ships)
            screen += self.p2_field.draw()

        screen += self.drawer.draw_separator() # draws board lines and game title
        screen += self.talker.talk() # prints all line history available

        if winner is not None:
            screen += self.talker.show_winner(winner)
        
        self.term.fl(screen)
    

    # def get_player_field(self, name: str, visible: bool) -> list:
    #     """
    #     Returns tuple of field dicts
    #     """
    #     return self.game.get_player_field(name, private=visible)



    def set_player(self, name: str, color: str, ai = None):
        """
        Tries to add Player instance to Game.
        Prints result.
        """
        meta = self.game.set_player(name, color)
        if ai is not None:
            if ai == "randomer": self.bots[name] = Randomer(name, self.game)
            else: self.bots[name] = Hunter(name, self.game)
        self.talker.talk(f"Player <{self.term.paint(meta["name"], meta["color"])}> was created")

    def get_players(self):
        """
        Prints a list of all added players.
        """
        try:
            output = "Players:\n"
            names = self.game.get_player_names()
            
            for name in names:
                meta = self.game.get_player_meta(name)
                output += f"  > {self.term.paint(meta['name'], meta['color'])}:\t"
                for etype, amount in meta["pending"].items():
                    output += f"{etype}: {amount}, "
                output = output[:-2] + "\n"

            self.talker.talk(output.strip("\n"))
        except: self.talker.talk(f"No players. Use 'add playername' first")

    def delete_player(self, name):
        meta = self.game.del_player(name)
        
        if meta['order'] == 1:
            self.p1_field = self.p2_field
            if self.p1_field is not None: self.p1_field.x0 = 0
        self.p2_field = None
        
        try: del self.bots[name]
        except KeyError: pass
        self.talker.talk(f"Player <{self.term.paint(meta['name'], meta['color'])}> deleted")

    def color(self, name: str, color: str):
        player = self.game.get_player(name)
        player.colorize(color)
        meta = self.game.get_player_meta(name)
        if meta["order"] == 0:
            if self.p1_field is not None: self.p1_field.color = meta["color"]
        else:
            if self.p2_field is not None: self.p2_field.color = meta["color"]
        self.talker.talk(f"{self.term.paint(name, color)} color changed")


    def set_player_field(self, name: str, shape: str, params: tuple, ):
        meta = self.game.get_player_meta(name)

        match shape:
            case "1": shape = "rectangle"
            case "2": shape = "circle"
            case "3": shape = "triangle"
            case _: shape = "<WRONG SHAPE ID>"
        if params is None: params = [0, 0]
        self.game.change_player_field(name, shape, list(params))

        order = int(meta["order"])
        field = CLIField(self.term, int(meta["order"]), meta["name"], meta["color"])
        if not order:
            self.p1_field = field
            self.p1_field.cells = self.game.get_player_field(name, private=True)
        else:
            self.p2_field = field
            self.p2_field.cells = self.game.get_player_field(name, private=True)

        self.talker.talk(f"<{self.term.paint(meta['name'], meta['color'])}> field now is {shape}: {params}")
    

    def entity_amount(self, name, etype, amount):
        self.game.change_entity_list(name, {etype: amount})

    
    def proceed_to_setup(self):
        self.game.ready()
        self.talker.talk(self.term.paint("Setup state is running. Use `place` to place your ships.", "orange"), loud = True)

    def place_entity(self, name: str, etype: str, icoords: str, rot: str):

        coords = self.convert_input(icoords)
        
        etype, rot = int(etype), int(rot)
        self.game.place_entity(name, etype, coords, rot)
        meta = self.game.get_player_meta(name)
        self.talker.talk(f"<{self.term.paint(name, meta["color"])}> placed entity sucsessfully")
    

    def autoplace(self, name: str):
        """
        Autoplaces all remain ships
        """
        self.game.autoplace(name)
        self.talker.talk(f"Autoplaced ships for <{name}>")


    def convert_input(self, coords: str):
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
    

    def start(self):
        self.game.start()
        self.talker.talk(self.term.paint("Game started. Use `sh` to shoot.", "blue"), loud = True)

    
    def shoot(self, shooter: str, coords):
        """
        Can take both coord formats: (y,x) and "A1"
        """
        if not isinstance(coords, tuple): coords = self.convert_input(coords)
        result = self.game.shoot(shooter, coords)
        self.talker.talk(f"{shooter} shot {coords}. Result - {result}")
        return result


    def automove(self, name: str) -> str:
        if name not in self.bots: return
        names = self.game.get_player_names()
        del names[names.index(name)]
        victim = names[0]
        bots_coords_choose = self.bots[name].shoot(self.game.get_player_field(victim))
        return self.shoot(name, bots_coords_choose)