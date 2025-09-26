from __future__ import annotations
from blessed import Terminal
from functools import partial
from modules.game import Game
import random



class STerminal:
    """
    Superclass with general fields all subclasses required
    """

    def __init__(self):
        self.term = Terminal()
        self.colors = {
            "blue":     {"main": self.deepskyblue,  "side": self.deepskyblue4},
            "green":    {"main": self.green2,       "side": self.webgreen},
            "orange":   {"main": self.darkorange1,  "side": self.darkorange3},
            "pink":     {"main": self.hotpink,      "side": self.violetred3},
            "purple":   {"main": self.purple2,      "side": self.purple4},
            "red":      {"main": self.firebrick2,   "side": self.firebrick4},
            "yellow":   {"main": self.yellow2,      "side": self.yellow4},
            "white":    {"main": self.white,        "side": self.dimgray},
        } # colors from blessed.Terminal
        self.pr = partial(print, end='')
        self.fl = partial(print, end="", flush=True)
    
    def paint(self, obj, color: str, *, side = False) -> str:
        if color not in self.colors: color = "white"
        if obj is None: return ""
        if not side: return f"{self.colors[color]['main']}{obj}{self.normal}"
        else: return f"{self.colors[color]['side']}{obj}{self.normal}"

    def __getattr__(self, name):
        return getattr(self.term, name)


class CLIField:
    FIELD_SIZE_Y = 27 # 26 + 1
    FIELD_SIZE_X = 56 # 2*26 + 4

    
    def __init__(self, term: STerminal, position: int, name: str, color: str):
        self.y0 = 0
        if not position: self.x0 = 0
        else: self.x0 = CLIField.FIELD_SIZE_X
        self.name = name
        self.color = color
        self.term = term
        self._cells = {}
        self.height = None
        self.width = None
    

    @property
    def cells(self): return(self._cells)

    @cells.setter
    def cells(self, value):
        self._cells = value
        self.height = max([coords[0] for coords in value.keys()]) + 1
        self.width = max([coords[1] for coords in value.keys()]) + 1      

    
    def wipe(self):
        line = " " * CLIField.FIELD_SIZE_X
        wiper = ""
        for y in range(CLIField.FIELD_SIZE_Y):
            wiper += (self.term.move_yx(self.y0 + y, self.x0) + line)
        return wiper

    def draw(self):
        if self.width is None or self.height is None: return
        y_now = self.y0 + (CLIField.FIELD_SIZE_Y - 1 - self.height) // 2
        x_now = self.x0 + (CLIField.FIELD_SIZE_X - 4 - self.width*2) // 2
        output = ""

        # letter row printer
        for x in range(self.width):
            letter = chr(x + 65) # → A, B, C ...
            output += f"{self.term.move_yx(y_now, x_now + x*2 + 3)}{self.term.paint(letter, 'white', side=True)}"
        y_now += 1 # drawing field itself under the row

        for y in range(self.height):
            # every line starts with a number
            output += self.term.move_yx(y_now + y, x_now) + self.term.paint(y+1, "white", side=True)
            
            for x in range(self.width):
                symb = ""
                match self.cells[(y, x)]:
                    case "void":    symb = " "
                    case "free":    symb = "."
                    case "miss":    symb = "o"
                    case "object":  symb = self.term.paint("■", self.color)
                    case "hit":     symb = self.term.paint("X", self.color, side=True)
                output += self.term.move_yx(y_now + y, x_now+3 + x*2) + symb
        return output     


class CLIDrawer:
    """
    Draws everything
    """

    def __init__(self, term: STerminal):
        self.term = term

    def draw_separator(self):
        horizontal = self.term.move_yx(CLIField.FIELD_SIZE_Y, 0) + "─" * self.term.width
        
        vertical = ""
        x = CLIField.FIELD_SIZE_X * 2
        for y in range(CLIField.FIELD_SIZE_Y + 1):
            vertical += self.term.move_yx(y, x) + "│"
        vertical = vertical[:-1] + "┴"

        title = self.term.move_yx(CLIField.FIELD_SIZE_Y, CLIField.FIELD_SIZE_X * 2 + 6) + r"→ Battleship-S ←" # r"⚝ 𝗕𝗮𝘁𝘁𝗹𝗲𝘀𝗵𝗶𝗽-𝗦 ⚝"

        return horizontal + vertical + self.term.paint(title, "white", side=False)      
    

    def wipe_screen(self):
        return self.term.move_yx(0, 0) + self.term.clear


class CLITalker:
    def __init__(self, term: STerminal):
        self.term = term
        self.y0 = CLIField.FIELD_SIZE_Y + 1
        self.x0 = 0
        self.history = ["", "", ""]
    
    def talk(self, text = "", loud = False):
        """
        Always returns console update string, but it can be just not used when no need to
        """
        if text:
            self.history[0] = self.history[1]
            self.history[1] = self.history[2]
            self.history[2] = str(text)
        
        if loud and text:
            self.history = ["", "", text]

        output = self.term.move_yx(self.y0, self.x0) + "\n".join(self.history)
        return output.strip()
        



class CLIRenderer:
    def __init__(self, term: STerminal):
        self.term = term
        self.game = Game()
        self.talker = CLITalker(term)
        self.drawer = CLIDrawer(term)
        self.p1_field: CLIField = None
        self.p2_field: CLIField = None
    

    def update_screen(self):
        screen = ""
        screen += self.drawer.wipe_screen()
        try: names = self.game.get_player_names()
        except: pass
        if self.p1_field is not None:
            self.p1_field.cells = self.game.get_player_field(names[0], private = True)
            screen += self.p1_field.draw()
        if self.p2_field is not None:
            self.p2_field.cells = self.game.get_player_field(names[1], private = True)
            screen += self.p2_field.draw()
        screen += self.drawer.draw_separator()
        screen += self.talker.talk()
        self.term.fl(screen)


    def set_player(self, name: str, color: str):
        """
        Tries to add Player instance to Game.
        Prints result.
        """
        if not name: self.talker.talk(f"Give player a name")
        else:
            meta = self.game.set_player(name, color)
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
        meta = self.game.get_player_meta(name)
        self.game.del_player(name)
        self.talker.talk(meta)
        if not meta['order']:
            self.p1_field = self.p2_field
            self.p1_field.x0 = 0
        self.p2_field = None
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
        self.talker.talk(self.term.paint("Setup state is running. Use `set` to place your ships.", "orange"), loud = True)

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
        player = self.game.get_player(name)
        for entity, amount in player.pending_entities.items().__reversed__(): # starts with big ones first
            if amount == 0: continue
            counter = 0
            for _ in range(amount):
                success = False
                while not success:
                    if counter >= 50000: raise ValueError("Unable to autoplace entities - Too many iterations")
                    counter += 1
                    try:
                        y = random.randint(0, player.field.dimensions["height"] - 1)
                        x = random.randint(0, player.field.dimensions["width"] - 1) 
                        rot = random.randint(0, 3)
                        self.game.place_entity(name, entity.value, (y, x), rot)
                        success = True
                    except Exception: continue

    

    def convert_input(self, coords: str):
        """
        Converts human input to game expected parameters.
        E.g. A10 to (9, 0); J2 to (3, 9)
        """
        Y_coord, X_coord = None, None
        for i in range (26):
            letter = chr(i + ord("A"))
            if coords[0] == letter:
                X_coord = ord(letter) - ord("A")
                Y_coord = int(coords.replace(letter, "")) - 1
                break
        if X_coord is None: raise ValueError("Coordinates must be in 'C10' format")
        return (Y_coord, X_coord)

    



class CLIIO:
    """
    Contains all commands which connect user commands and renderer methods
    """
    def __init__(self):
        self.term = STerminal()
        self.r = CLIRenderer(self.term)
        self.talker = self.r.talker
        self.upd = self.r.update_screen
        self.upd()

        self.arrow = f"{self.term.move_yx(self.term.height-3, 0)}{self.term.paint('>> ', 'green')}"
    commands = {}

    
    def run(self):
        while True:
            try:
                line = input(self.arrow).strip()
                if not line: continue
                
                cmd, *args = line.split()
                match cmd:
                    case "help" | "h":
                        self.helper()
                        continue
                    case "exit": # продумать мб стирать весь экран
                        self.talker.talk(f"{self.term.paint(f'{self.term.move_yx(self.term.height - 2, 0)}Game has been suspended!', 'red')}", loud = True)
                        self.upd()
                        break
                    case _:
                        if cmd not in self.commands:
                            self.talker.talk(f"Wrong command {self.term.paint(cmd,'red', side = True)}. Type '{self.term.paint('help', 'green')}'")
                            self.upd()
                            continue
                        self.commands[cmd]["command"](self, *args)
            except Exception as e:
                self.talker.talk(f"Error: {e}")
                self.upd()


    def helper(self):
        help_line = (f"{self.term.green}Available commands:{self.term.normal}\n")
        for name, info in self.commands.items():
            help_line += f"    > {name}: {info['help']}\n"
        self.talker.talk(help_line.strip(), loud = True)
        self.upd()
        
    
    @classmethod
    def command(cls, help_info: str):
        def wrapper(func):
            cls.commands[func.__name__] = {"command": func, "help": help_info}
            return func
        return wrapper

@CLIIO.command(help_info = "Add a new player: add <name> <color>")
def add(self, name, color = "white"):
    self.r.set_player(name, color)
    self.upd()

@CLIIO.command(help_info = "Print player list: players")
def players(self):
    self.r.get_players()
    self.upd()

@CLIIO.command(help_info = "Delete player: delete <name>")
def delete(self, name):
    self.r.delete_player(name)
    self.upd()

@CLIIO.command(help_info = "Change player color: color <name> <color>\n        <blue>, <green>, <red>, <yellow>, <orange>, <purple>, <white>, <pink>")
def color(self, name, color):
    self.r.color(name, color)
    self.upd()

@CLIIO.command(help_info = "Change player field: field <name> <shape_id> <param1> <param2> ...\n1 = rectangle, 2 = circle, 3 = triangle.")
def field(self, name, shape_id = 1, *params):
    self.r.set_player_field(name, shape_id, params)
    self.upd()

@CLIIO.command(help_info = "Starts choose sequence: getships <name>")
def getships(self, name, *flag):
        meta = self.r.game.get_player_meta(name)
        if flag: # for debugging
            self.r.game.get_player(name).pending_entities = self.r.game.default_entities.copy()
        else:
            for etype in list(Game.default_entities):
                
                self.talker.talk(f"Choose amount of {str(etype)}: ", loud = True)
                self.upd()
                amount = input(self.arrow).strip()
                self.r.entity_amount(name, etype, amount)
        self.talker.talk(f"Entity pick sequence for <{self.term.paint(meta['name'], meta['color'])}> finished.", loud = True)
        self.upd()

@CLIIO.command(help_info = "Proceeds to ship placement: ready")
def ready(self):
    self.r.proceed_to_setup()
    self.upd()

@CLIIO.command(help_info = "Place entity: place <name> <etype> <coords> <rot>")
def place(self, name, etype, coords, rot):
    self.r.place_entity(name, etype, coords, rot)
    self.upd()



@CLIIO.command(help_info = "Quick start game: q")
def q(self):
    self.__init__()
    colors = list(self.term.colors.keys())
    random.shuffle(colors)
    # два разных цвета
    color1, color2 = colors[:2]

    # создаём игроков
    name1 = "nhk"
    name2 = "loner"
    self.r.set_player(name1, color1)
    self.r.set_player(name2, color2)

    # случайные размеры полей
    for name in [name1, name2]:
        width = random.randint(9, 26)
        height = random.randint(9, 26)
        # пусть всегда прямоугольник
        self.r.set_player_field(name, "1", (height, width))
        self.r.game.get_player(name).pending_entities = self.r.game.default_entities.copy()
    
    self.r.get_players()
    self.r.proceed_to_setup()
    self.upd()
    for name in (name1, name2):
        self.r.autoplace(name)
    self.upd()

if __name__ == "__main__":
    import logging
    with open("log.log", "w") as file: file.write("")
    logging.basicConfig(
    filename = "log.log",
    level = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode = "a",
    )
    io = CLIIO()
    io.run()
