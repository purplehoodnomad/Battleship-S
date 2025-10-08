import logging
from functools import partial
from blessed import Terminal
from modules.enums_and_events import CellStatus

logger = logging.getLogger(__name__)

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
    def __init__(self, term: STerminal, cells_to_draw: list[tuple[int, int]], height: int, width: int):
        self.term = term
        self.height = height
        self.width = width
        
        # this separation is made so planets upon moving not erasig data what was under them before
        self.cells = {coord: CellStatus.FREE for coord in cells_to_draw} # cells of general entity objects
        self.orbits = [] # orbit cells are side-layered - the're drewn under the main objects (misses, hits)
        self.planets = [] # planets always move they're on the highest layer


    def mark_cells_as(self, cells, cell_status: CellStatus):
        """
        Changes status of given cells in local self.cells storage.
        It's supposed that events update information.
        """
        for coords in cells:
            if not isinstance(coords, tuple):
                raise ValueError(f"Coords expected to be in (y, x) format, not {coords}")
            if coords not in self.cells:
                continue
            self.cells[coords] = cell_status


    def draw(self, lu: tuple[int, int], color: str):
        """
        Draws field from given lu coordinates of left upper corner.
        """
        if not self.cells:
            return ""
        y0, x0 = lu
        
        y_now = y0
        x_now = x0
        output = ""

        # letter row printer
        for x in range(self.width):
            letter = chr(x + 65) # → A, B, C ...
            output += f"{self.term.move_yx(y_now, x_now + x*2 + 3)}{self.term.paint(letter, 'white', side=False)}"
        y_now += 1 # drawing field itself under the row

        for y in range(self.height):
            # every line starts with a number
            output += self.term.move_yx(y_now + y, x_now) + self.term.paint(y+1, "white", side=False)
            
            for x in range(self.width):
                symb = ""
                coords = (y, x)

                if coords not in self.cells:
                    output += self.term.move_yx(y_now + y, x_now+3 + x*2) + " "
                    continue
                else:
                    symb = "."
                
                if coords in self.orbits:
                    symb = self.term.paint("•", color)
                
                match self.cells[coords]:
                    case CellStatus.MISS:
                        if coords in self.orbits:
                            symb = self.term.paint("o", color, side=True)
                        else:
                            symb = self.term.paint("o", "white", side=True)
                    case CellStatus.ENTITY:  symb = self.term.paint("■", color)
                    case CellStatus.RELAY:   symb = self.term.paint("#", color)
                    case CellStatus.HIT:     symb = self.term.paint("X", color)

                if coords in self.planets:
                    symb = self.term.paint("@", color, side=True)             
                
                output += self.term.move_yx(y_now + y, x_now+3 + x*2) + symb
        return output


class CLIDrawer:
    """
    Draws everything
    """

    def __init__(self, term: STerminal):
        self.term = term

    def draw_separator(self, y: int, x: int):
        horizontal = self.term.move_yx(y, x) + "─" * self.term.width
        # title = self.term.move_yx(CLIField.FIELD_SIZE_Y, CLIField.FIELD_SIZE_X * 2 + 6) + r"→ Battleship-S ←" # r"⚝ 𝗕𝗮𝘁𝘁𝗹𝗲𝘀𝗵𝗶𝗽-𝗦 ⚝"
        return horizontal  

    def wipe_screen(self):
        return self.term.move_yx(0, 0) + self.term.clear


class CLITalker:
    def __init__(self, term: STerminal):
        self.term = term
        self.y0 = 30 + 1
        self.x0 = 0
        self.history = ["", "", "", "", "", "", "", "", ""]
    
    def talk(self, text = "", loud = False):
        """
        Always returns console update string, but it can be just not used when no need to
        """
        if text:
            text = str(text)
            for i in range(1, len(self.history)):
                self.history[i-1] = self.history[i]
            self.history[-1] = text
        
        if loud and text:
            self.history = ["" for _ in self.history]
            self.history[-1] = text

        output = self.term.move_yx(self.y0, self.x0) + "\n".join(self.history)
        return output.strip()
    
    def show_winner(self, name: str):
        output = self.term.move_yx(self.y0, self.x0) + self.term.clear_eos
        lines = (
            "╔═══════════════╗",
            "║     Winner    ║",
            "╠═══════════════╣",
           f"║    {name:<9}  ║",
            "╚═══════════════╝"
        )
        output += self.term.move_yx(self.y0, self.x0)
        for line in lines:
            output += line + "\n"
        return output + "game is over - type `exit` or `restart`"