import random
from cli.cli_terminal import STerminal, CLITalker, CLIDrawer, CLIField
from cli.cli_renderer import CLIRenderer
from modules.game import Game

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
        self.game_active = False

        self.arrow = f"{self.term.move_yx(self.term.height-3, 0)}{self.term.paint('>> ', 'green')}"
    commands = {}

    
    def run(self): 
        while True:
            if self.game_active:
                for bot_name in self.r.bots.keys():
                    try:
                        result = "hit"
                        while result == "hit":
                            result = self.r.automove(bot_name)
                    except Exception as e:
                        self.talker.talk(e)
                        continue
                self.upd()
                

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
def add(self, name, color = "white", ai_type = None):
    self.r.set_player(name, color, ai_type)
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
def sh(self, shooter, coords):
    self.r.shoot(shooter, coords)
    self.upd()



@CLIIO.command(help_info = "Quick start game: q")
def q(self):
    """
    Autosetup random players adn parameters for debugging
    """
    self.__init__()
    # picks random colors from supported
    colors = list(self.term.colors.keys())
    random.shuffle(colors)
    color1, color2 = colors[:2]

    # players setup
    name1 = "hunter1"
    name2 = "hunter2"
    self.r.set_player(name1, color1, "hunter")
    self.r.set_player(name2, color2, "hunter")

    # field creation for both players
    for name in [name1, name2]:
        width = 9 # random.randint(9, 26)
        height = 9 # random.randint(9, 26)
        self.r.set_player_field(name, "1", (height, width))
        self.r.game.get_player(name).pending_entities = self.r.game.default_entities.copy()
    
    self.r.proceed_to_setup()
    for name in (name1, name2):
        self.r.autoplace(name)
    
    self.game_active = True
    self.r.start()
    self.upd()

def main():
    io = CLIIO()
    io.run()

if __name__ == "__main__":
    main()