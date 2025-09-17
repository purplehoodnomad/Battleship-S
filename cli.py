from blessed import Terminal
from functools import partial

if __name__ == "__main__":
    from field import Field, Cell
    from entities import Entity, Ship

# getting rid of \n and making controlable different
# print content buffeing and flushing it manually
pr = partial(print, end='')
fl = partial(print, end="", flush=True)

class CliWriter:
    """
    Used to easily operate with Battle-S interfaces. Field in particularly.
    """
    def __init__(self, player_colors: tuple):
        self.term = Terminal()
        self.color_p1, self.color_p2 = self.get_colors(player_colors)
    
    # blessed doesn't allow inheritance from Terminal class
    # alternative - make wrapper class and redirect attribute getting to Terminal
    def __getattr__(self, name): 
        return getattr(self.term, name)
    
    def get_colors(self, colors):
        out = []
        for color in colors:
            match color:
                case "blue": out.append({"main": self.deepskyblue, "side": self.deepskyblue4})
                case "green": out.append({"main": self.green2, "side": self.webgreen})
                case "orange": out.append({"main": self.darkorange1, "side": self.darkorange3})
                case "pink": out.append({"main": self.hotpink, "side": self.violetred3})
                case "purple": out.append({"main": self.purple2, "side": self.purple4})
                case "red": out.append({"main": self.firebrick2, "side": self.firebrick4})
                case "yellow": out.append({"main": self.yellow2, "side": self.yellow4})
        return out



    def get_cell_teplate(self, cell: Cell, color):
        match (cell.is_void, cell.occupied_by, cell.was_shot):
            case (True, _, _):          return " "
            case (_, None, False):      return "."
            case (_, None, True):       return "o"
            case (_, Ship(), False):    return f"{color["main"]}■{self.normal}"
            case (_, Ship(), True):     return f"{color["side"]}Х{self.normal}"
            
            case _: raise KeyError("Add this cell a drawing pattern")
    
    
    def draw_field(self, field: Field, coords: tuple, color: dict, *, title = "Field",):
        """
        Draws full field with given y,x of upper left corner.
        Easier and more secure to redraw whole field on every update.
        """
        y0, x0 = coords

        output = f"{self.move_yx(y0, x0 + 4)}{color["main"]}{title}{self.normal}" # adding title and one line underneath

        y0 = y0 + 1
        # adding letters horizontally
        for x in range(field.dimensions["width"]):
            output += f"{self.move_yx(y0 + 1, x0 + x*2 + 3)}{self.dimgray}{chr(x + 65)}{self.normal}"

        y0 = y0 + 2
         # updating reference ordinate
        for y in range(field.dimensions["height"]):
            # every line starts with a number
            output += self.move_yx(y0 + y, x0) + self.dimgray + str(y+1) + self.normal

            for x in range(field.dimensions["width"]):
                symb = self.get_cell_teplate(field.get_cell((y, x)), color)
                output += self.move_yx(y0 + y, x0 + x*2 + 3) + symb
        
        fl(output)

        