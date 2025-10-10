import logging
from functools import partial
from blessed import Terminal
from modules.enums_and_events import CellStatus


logger = logging.getLogger(__name__)


class STerminal:
    """
    Basically - patch for blessed.Terminal.
    Previously was base class for all CLIElements. Now only manages with coloring and custom print methods.
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
        
        # same as print, but with manual control
        self.pr = partial(print, end='')
        self.fl = partial(print, end="", flush=True)
    
    def paint(self, obj, color: str, *, side = False) -> str:
        """
        Method to color text. Returns same str object colored with supported STerminal.colors
        """
        if color not in self.colors:
            color = "white"
        if obj is None:
            return ""
        if not side:
            return f"{self.colors[color]['main']}{obj}{self.normal}"
        else:
            return f"{self.colors[color]['side']}{obj}{self.normal}"
    
    
    def draw_separator(self, y: int):
        horizontal = self.move_yx(y, 0) + "─" * self.width
        horizontal += self.move_yx(y, 8) + r"→ Battleship-S ←" # r"⚝ 𝗕𝗮𝘁𝘁𝗹𝗲𝘀𝗵𝗶𝗽-𝗦 ⚝"
        return horizontal

    def wipe_screen(self):
        return self.move_yx(0, 0) + self.clear
    
    
    def __getattr__(self, name):
        return getattr(self.term, name)


class CLIField:
    """
    Class for drawing field in CLI.
    Contains local copy of field and can redraw it any time.
    Stores information about:
    - all non-void field cells;
    - orbit cells;
    - planets cells.
    """
    def __init__(
            self,
            term: STerminal,
            cells_to_draw: list[tuple[int, int]],
            height: int,
            width: int
    ):
        self.term = term
        self.height = height
        self.width = width
        
        # this separation is made so planets upon moving not erasig data what was under them before
        self.cells = {coord: CellStatus.FREE for coord in cells_to_draw} # cells of general entity objects
        self.orbits = [] # orbit cells are side-layered - the're drewn under the main objects (misses, hits)
        self.planets = [] # planets always move they're on the highest layer


    def mark_cells_as(self, cells, cell_status: CellStatus):
        """
        Changes status of given cells in self.cells.
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

                if coords not in self.cells: # void cells
                    output += self.term.move_yx(y_now + y, x_now+3 + x*2) + " "
                    continue
                else: # free cells
                    symb = "."
                
                if coords in self.orbits: # orbit cells as midlayer
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

                if coords in self.planets: # planet is highest layer
                    symb = self.term.paint("@", color, side=True)             
                
                output += self.term.move_yx(y_now + y, x_now+3 + x*2) + symb
        return output


class CLITalker:
    """
    Console under fields. Shows results of user commands.
    """
    def __init__(self, term: STerminal):
        self.term = term
        self.history = []
    
    def talk(self, text = "", /, coords = (31,0), payload_size = 7, loud = False):
        """
        Always returns console update string, but it can be just not used when no need to
        """
        y, x = coords
        if text:
            self.history.append(str(text))
        payload_size if payload_size < len(self.history) else len(self.history)
        output = self.term.move_yx(y, x) + "\n".join(self.history[-payload_size:])
        if loud and text:
            output = self.term.move_yx(y, x) + text
        
        return output.strip()

    
    def show_winner(self, name: str, /, coords = (31, 30)):
        y, x = coords
        lines = (
            "╔═══════════════╗",
            "║     Winner    ║",
            "║═══════════════║",
           f"     {name}      ",
            "╚═══════════════╝"
        )
        output = "" 
        for n in range(len(lines)):
            output += self.term.move_yx(y + n, x) + lines[n]
        return output + "\ngame is over - type `exit` or `restart`"