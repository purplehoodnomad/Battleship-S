import random

from cli.cli_terminal import STerminal
from cli.cli_renderer import CLIRenderer

from modules.core.game import Game

from modules.common.enums import EntityType
from modules.common.exceptions import GameException, FieldException 


class CLIIO:
    """
    Contains all commands which connect user commands and renderer methods
    """
    def __init__(self):

        self.term = STerminal()
        self.r = CLIRenderer(self.term)
        self.talker = self.r.talker
        self.game_active = False
        self.show_all = False
        self.arrow_coords = (3, 0) # position of input crusor
    commands = {}
    
    def upd(self):
        self.arrow_coords = self.r.update_screen(self.show_all)
    
    @property
    def arrow(self):
        """
        Returns cursor with position of arrow_coords
        """
        return f"{self.term.move_yx(self.arrow_coords[0], self.arrow_coords[1])}{self.term.paint('  >> ', 'green')}"


    def run(self):
        while True:
            self.upd()

            # makes bots trying to autoshoot when game's started
            if self.game_active:
                while self.r.game.whos_turn() in self.r.bots:
                    try:
                        self.r.automove()
                    except GameException:
                        break
                    except FieldException as e:
                        self.talker.talk(repr(e))
                        break
                    self.upd()
                

            try:
                line = input(self.arrow).strip() # waits for user command
                if not line: continue
                
                cmd, *args = line.split()
                match cmd:

                    case "help" | "h":
                        self.helper(*args)
                        continue
                    
                    case "exit":
                        self.term.fl(self.term.paint(f'{self.term.move_yx(self.term.height - 4, 0)}Game has been suspended!', 'red'))
                        break
                    
                    case _:
                        if cmd not in self.commands:
                            self.talker.talk(f"Wrong command {self.term.paint(cmd,'red', side = True)}. Type {self.term.paint('`help`', 'green')} for command list")
                            continue
                        self.commands[cmd]["command"](self, *args)
            
            except Exception as e:
                self.talker.talk(f"Error: {repr(e)}")


    def helper(self, com = None):

        if com is None or not com: # help about all commands
            help_line = (f"{self.term.green}Available commands:{self.term.normal}\n")
            for name, info in self.commands.items():
                help_line += f"  > {name}: \t{self.term.paint(info['usage'], "white", side=True)}\n"
            self.talker.talk("\n" + help_line.strip())
            return
        
        if com not in self.commands:
            self.talker.talk(f"Wrong command {self.term.paint(com,'red', side = True)}. Type {self.term.paint('`help`', 'green')} for command list.")
            return
        
        info = self.commands[com]
        if not info["options"]:
            info["options"] = ["None"]

        help_line = f"""> {self.term.paint(com,'green', side = True)}: {info['description']}
Usage: {self.term.paint(info['usage'], "white", side=True)}
Options:
 {self.term.paint("\n ".join(info["options"]), "white", side=True)}"""
        self.talker.talk("\n" + help_line)
        
    
    @classmethod
    def command(cls, usage: str, description: str, options: list[str]):
        """
        Fabric of decorators. Automatically adds help information and command to the command list.
        """
        def wrapper(func):
            cls.commands[func.__name__] = {
                "command": func,
                "usage": usage,
                "description": description,
                "options": options
            }
            return func
        return wrapper


@CLIIO.command(
    usage="rules [ru]",
    description="Prints rules",
    options=["ru, optional: prints rules in russian"]
)
def rules(self, *args):

    if not args:
        
        rules = f"""
{self.term.paint("Goal", "blue", side=True)}  
Destroy all enemy ships and relays before your own fleet is eliminated.  
Planets are decoys and are not required to destroy for victory.

{self.term.paint("Fleet Composition", "blue", side=True)}  
Each player has:
  • 4 single-cell ships (Corvette)
  • 3 double-cell ships (Frigate)
  • 2 triple-cell ships (Destroyer)
  • 1 four-cell ship (Cruiser)
  • 1 Relay (Relay)
  • 1 Planet (Planet)

{self.term.paint("Placement Rules", "blue", side=True)}  
  • Ships cannot touch each other, even diagonally.  
  • Ships and relays may touch planets but cannot cross their orbits.  
  • Planets move along their orbits every turn.  
  • Orbits may overlap and go beyond the visible field.

{self.term.paint("Shooting", "blue", side=True)}  
Players take turns firing at coordinates on the opponent’s field:
  • Miss – empty cell  
  • Hit – ship part or planet (planets imitate ship hits)  
  • Sunk – all segments of a ship are hit  
  • Relay – reflects the shot back to the same coordinate on the attacker’s field  
    If a reflected shot hits another relay on the same coordinate, a "black hole" forms and the game ends in a draw.

{self.term.paint("Planets", "blue", side=True)}  
  • Planets automatically move along their orbits at the end of each turn.  
  • Movement direction (clockwise or counterclockwise) is random per planet.  
  • Hitting a planet looks like a normal hit but it is never destroyed.  
  • If two planets collide, both are destroyed and a hit mark appears on that cell.

{self.term.paint("Victory Conditions", "blue", side=True)}  
  • A player wins by destroying all enemy ships and relays.  
  • If the last relay reflects a shot into the opponent’s last ship, the game ends in a draw.  
  • Planets do not affect victory conditions.
"""
    else:
        rules = f"""{self.term.paint("Цель игры", "blue", side=True)}  
Уничтожить все корабли и реле противника раньше, чем он уничтожит ваши.  
Планеты — обманки, их уничтожать не нужно.

{self.term.paint("Состав флота", "blue", side=True)}  
У каждого игрока по умолчанию:
  • 4 одноклеточных корабля (Corvette)
  • 3 двухклеточных (Frigate)
  • 2 трёхклеточных (Destroyer)
  • 1 четырёхклеточный (Cruiser)
  • 1 реле (Relay)
  • 1 планета (Planet)

{self.term.paint("Размещение", "blue", side=True)}  
  • Корабли не могут соприкасаться даже по диагонали.  
  • Корабли и реле могут соприкасаться с планетами, но нельзя пересекать их орбиты.  
  • Планеты двигаются по орбитам каждый ход.  
  • Орбиты могут пересекаться и выходить за пределы экрана.

{self.term.paint("Стрельба", "blue", side=True)}  
Игроки стреляют поочерёдно по координатам противника:
  • Мимо – пустая клетка  
  • Попадание – часть корабля или планета (планета имитирует корабль)  
  • Уничтожен – все части корабля подбиты  
  • Реле – отражает выстрел в ту же координату на поле стрелявшего  
    Если отражённый выстрел попадает в реле на той же координате, образуется «чёрная дыра» — игра завершается ничьёй.

{self.term.paint("Планеты", "blue", side=True)}  
  • Планеты автоматически двигаются по орбитам в конце каждого хода.  
  • Направление движения (влево или вправо) случайное для каждой планеты.  
  • Попадание по планете отображается как обычное попадание, но она не разрушается.  
  • Если две планеты сталкиваются, обе уничтожаются, а в этой клетке появляется метка попадания.

{self.term.paint("Победа", "blue", side=True)}  
  • Побеждает игрок, уничтоживший все корабли и реле противника.  
  • Если последнее реле отражает выстрел в последний корабль противника, происходит ничья.  
  • Планеты не влияют на условия победы.
"""
    self.talker.talk("\n" + self.term.paint("   > Rules", "blue"))
    self.talker.talk("\n" + rules)


@CLIIO.command(
    usage="add <name> [<color>] [<ai>]",
    description="Adds a new player with <name> and <color> to the game with or without <ai>",
    options=[
        "color: optional: blue|green|red|yellow|orange|purple|white|pink, default: white",
        "ai: optional: randomer|hunter"
    ]
)
def add(self, name, color = "white", ai_type = None):
    self.r.set_player(name, color, ai_type)


@CLIIO.command(
    usage="players",
    description="Prints player list",
    options=[]
)
def players(self):
    self.r.get_players()


@CLIIO.command(
    usage="delete <name>",
    description="Deletes player <name>",
    options=[]
)
def delete(self, name):
    self.r.delete_player(name)


@CLIIO.command(
    usage="color <name> <color>",
    description="Changes <name> player's color. Can be used midgame",
    options=[
        "color: blue|green|red|yellow|orange|purple|white|pink, default: white"
    ]
)
def color(self, name, color):
    self.r.color(name, color)



@CLIIO.command(
    usage="field <name> <shape> <param1> <param2>",
    description="Changes <name> player's field with <shape> and given parameters",
    options=[
        "shape: rectangle|circle|triangle|rhombus|pentagon|hexagon|heptagon",
        "param1: rectangle → height, int;  others → radius, int",
        "param2: rectangle → width, int;   others → angle, float",
        "IMPORTANT: supported field size variety depends on console window dimensions. Make it fullscreen for fields 30+ cells."
    ]
)
def field(self, name, shape_id = 1, *params):
    self.r.set_player_field(name, shape_id, params)


@CLIIO.command(
    usage="getships <name> [<flag>]",
    description="Starts entity choose sequence for <name> player. Use flag to set defaults",
    options=[
        "flag, optional: any value"
    ]
)
def getships(self, name, *flag):
        meta = self.r.game.get_player_meta(name)
        if flag: # for debugging
            self.r.game._get_player(name).pending_entities = self.r.game.default_entities.copy()
        else:
            for etype in list(Game.default_entities):
                
                self.talker.talk(f"Choose amount of {str(etype)}: ")
                self.upd()
                amount = input(self.arrow).strip()
                self.r.entity_amount(name, etype, amount)
        self.talker.talk(f"Entity pick sequence for <{self.term.paint(meta['name'], meta['color'])}> finished.")


@CLIIO.command(
    usage="ready",
    description="Proceeds game state to ship placement. Use it after `getships` and `field`",
    options=[]
)
def ready(self):
    self.r.proceed_to_setup()


@CLIIO.command(
    usage="place <name> <entity> <cell> <r>",
    description="Places <entity> for <name> player on <cell> anchor and <r> direction",
    options=[
        "entity: CORVETTE|FRIGATE|DESTROYER|CRUISER|RELAY|PLANET",
        "coords: combination of letter and number. E.g.: A10; G3, H6, etc.",
        "r: rotation for ships and relay: CORVETTE, FRIGATE, DESTROYER, CRUISER, RELAY;   radius of orbit: PLANET",
        "IMPORTANT: placement requires coordinates of anchor point (lowest point of ship and center of planet orbit) and rotation or radius in which direction other tiles must be placed\n E.g.: `A1 right` will occupy A1, A2, A3... cells depending on size of entity"
    ]
)
def place(self, name, etype, coords, rot):
    self.r.place_entity(name, etype, coords, rot)


@CLIIO.command(
    usage="apl <name>",
    description="Autoplaces all remaining entities for <name>",
    options=[]
)
def apl(self, name):
    self.r.autoplace(name)


@CLIIO.command(
    usage="start",
    description="Proceeds game state to active. Use it after all players `place` their entities",
    options=[]
)
def start(self):
    self.r.start()
    self.game_active = True


@CLIIO.command(
    usage="shoot <coords>",
    description="Tries to shoot in <coords> for player of current turn",
    options=["coords: combination of letter and number. E.g.: A10; G3, H6, etc."]
)
def shoot(self, coords):
    self.r.shoot(coords)


@CLIIO.command(
    usage="restart",
    description="Restarts game",
    options=[]
)
def restart(self):
    self.__init__()


@CLIIO.command(
    usage="preset <preset_name> [<flag>] [<autoplay>]",
    description="Starts game as player-hunter in with defaults",
    options=[
        "preset_name: classic|standart|random|planet_mayhem|relay_madness",
        "flag, optional: any value - skips ship placement",
        "autoplay, optional: any value -enables ai for player - autoplay mode"
    ]
)
def preset(self, mode, flag = None, autoplay = None):
    self.__init__()
    
    player_name, bot_name = "Player", "Bot"
    bot_ai = "hunter"
    player_ai = random.choice(("randomer", "hunter")) if autoplay is not None else ""
    if autoplay is not None:
        self.show_all = True
    
    options = {player_name: {}, bot_name: {}}
    
    colors = list(self.term.colors.keys())
    random.shuffle(colors)
    colors.remove("white")
    options[player_name]["color"], options[bot_name]["color"] = colors[:2]

    self.r.set_player(player_name, options[player_name]["color"], player_ai)
    self.r.set_player(bot_name, options[bot_name]["color"], bot_ai)

    match mode:
        case "classic":
            for name in options.keys():
                options[name]["entities"] = {
                    EntityType.CORVETTE: 4,
                    EntityType.FRIGATE: 3,
                    EntityType.DESTROYER: 2,
                    EntityType.CRUISER: 1,
                }
                options[name]["shape"] = "1"
                options[name]["params"] = ["10", "10"]
        
        case "standart":
            for name in options.keys():
                options[name]["entities"] = {
                    EntityType.CORVETTE: 5,
                    EntityType.FRIGATE: 4,
                    EntityType.DESTROYER: 3,
                    EntityType.CRUISER: 2,
                    EntityType.RELAY: 7,
                    EntityType.PLANET: 1,
                }
                options[name]["shape"] = "1"
                options[name]["params"] = ["12", "12"]
        
        case "random":
            for name in options.keys():
                options[name]["entities"] = {
                    EntityType.CORVETTE: random.randint(0, 10),
                    EntityType.FRIGATE: random.randint(0, 8),
                    EntityType.DESTROYER: random.randint(0, 5),
                    EntityType.CRUISER: random.randint(0, 3),
                    EntityType.RELAY: random.randint(0, 8),
                    EntityType.PLANET: random.randint(0, 4),
                }
                options[name]["shape"] = str(random.choice((1, 2, 3, 4, 5, 6, 7)))
                if options[name]["shape"] == "1":
                    height = str(random.randint(10, 15))
                    width = str(random.randint(10, 15))
                else:
                    height = str(random.randint(7, 10))
                    width = str(random.randint(1, 360))
                
                options[name]["params"] = [height, width]

        case "planet_mayhem":
            for name in options.keys():
                options[name]["entities"] = {
                    EntityType.CORVETTE: 4,
                    EntityType.FRIGATE: 0,
                    EntityType.DESTROYER: 0,
                    EntityType.CRUISER: 0,
                    EntityType.RELAY: 0,
                    EntityType.PLANET: 21,
                }
                options[name]["shape"] = "2"
                options[name]["params"] = ["6", "0"]
        
        case "relay_madness":
            for name in options.keys():
                options[name]["entities"] = {
                    EntityType.CORVETTE: 1,
                    EntityType.FRIGATE: 0,
                    EntityType.DESTROYER: 0,
                    EntityType.CRUISER: 0,
                    EntityType.RELAY: 40,
                    EntityType.PLANET: 0,
                }
                options[name]["shape"] = "3"
                options[name]["params"] = ["12", "145"]

    
    for name, config in options.items():
        self.r.set_player_field(name, config["shape"], config["params"])
        for etype, amount in config["entities"].items():
            self.r.entity_amount(name, etype, amount)

    self.r.proceed_to_setup()
    self.r.autoplace(bot_name)
    if flag is not None:
        self.r.autoplace(player_name)
        self.r.start()
        self.game_active = True
    

    


@CLIIO.command(
    usage="q",
    description="Quick start game",
    options=[]
)
def q(self):
    """
    Autosetup random players adn parameters for debugging
    """
    self.__init__()
    # picks random colors from supported
    colors = list(self.term.colors.keys())
    random.shuffle(colors)
    del colors[colors.index("white")]
    color1, color2 = colors[:2]

    # players setup
    name1 = "randomer"
    name2 = "hunter"
    self.r.set_player(name1, color1, "randomer")
    self.r.set_player(name2, color2, "hunter")

    # field creation for both players
    for name in [name1, name2]:
        shape = str(random.randint(1, 7))
        if shape == "1":
            height = str(random.randint(9, 15))
            width = str(random.randint(9, 15))
        else:
            height = str(random.randint(6, 8))
            width = str(random.randint(1, 360))           

        self.r.set_player_field(name, shape, [height, width])
        for type, amount in self.r.game.default_entities.items():
            self.r.entity_amount(name, type, amount)
    

    self.r.proceed_to_setup()
    for name in (name1, name2):
        # self.r.place_entity(name, "planet", "A7", "2")
        # self.r.place_entity(name, "planet", "G7", "4")
        # self.r.place_entity(name, "planet", "E7", "2")
        # self.r.place_entity(name, "corvette", "A1", "0")
        self.r.autoplace(name)
    
    self.r.start()
    self.game_active = True


def main():
    io = CLIIO()
    io.run()

if __name__ == "__main__":
    main()