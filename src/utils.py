class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Dimension:
    def __init__(self, width, length, height):
        self.width = width
        self.length = length
        self.height = height

class Package:
    def __init__(self, ident, pos[3], coord[3], value, weight, isFragile, eta):
        self.ident = ident
        self.pos = pos
        self.coord = coord
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta