import random
from cli_terminal import STerminal, CLITalker, CLIDrawer, CLIField
from cli_renderer import CLIRenderer
# from ..modules.game import Game
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.game import Game


class CLIIO:
    """
    Contains all commands which connect user commands and renderer methods
    """
    def __init__(self):
        self.term = STerminal()
        self.r: CLIRenderer = CLIRenderer(self.term)
        self.talker = self.r.talker
        self.upd = self.r.update_screen
        self.upd()
        self.game_active = False

        self.arrow = f"{self.term.move_yx(self.term.height-3, 0)}{self.term.paint('>> ', 'green')}"
    commands = {}

    
    def run(self):
        while True:
            if self.game_active:
                # TODO bot tries to move if it's turn
                pass

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

@CLIIO.command(help_info = "Add a new player: add <name> <color> <ai>")
def add(self, name, color = "white", *args):
    ai_flag = bool(args)
    self.r.set_player(name, color, ai_flag)
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

@CLIIO.command(help_info = "Autoplaces remaining entities: apl <name>")
def apl(self, name):
    self.r.autoplace(name)
    self.upd()

@CLIIO.command(help_info = "Proceeds to actual playing the game: start")
def start(self):
    self.r.start()
    self.game_active = True
    self.upd()

@CLIIO.command(help_info = "Proceeds to actual playing the game: start")
def sh(self, shooter, target, coords):
    self.r.shoot(shooter, target, coords)
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
    self.r.set_player(name2, color2, True)

    # случайные размеры полей
    for name in [name1, name2]:
        width = 10 # random.randint(9, 26)
        height = 10 # random.randint(9, 26)
        # пусть всегда прямоугольник
        self.r.set_player_field(name, "1", (height, width))
        self.r.game.get_player(name).pending_entities = self.r.game.default_entities.copy()
    
    self.r.get_players()
    self.r.proceed_to_setup()
    for name in (name1, name2):
        self.r.autoplace(name)
    self.r.start()
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
