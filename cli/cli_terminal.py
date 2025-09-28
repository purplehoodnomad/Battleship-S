from blessed import Terminal
from functools import partial


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
                    case "miss":    symb =  self.term.paint("o", "white", side=True)
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