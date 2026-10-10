class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def move(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Dimension:
    def __init__(self, width, length, height):
        self.width = width
        self.length = length
        self.height = height
    def rotate_x(self):
        temp = self.length
        self.length = self.height
        self.height = temp
    def rotate_y(self):
        temp = self.width
        self.width = self.height
        self.height = temp
    def rotate_z(self):
        temp = self.length
        self.length = self.width
        self.width = temp

class Package:
    def __init__(self, ident, pos, dim, value, weight, isFragile, eta):
        self.ident = ident
        self.pos = pos.copy()
        self.dim = dim.copy()
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta
    def is_overlap(self, other):
        return (self.pos.x < other.pos.x + other.width and
                self.pos.x + self.width > other.pos.x and
                self.pos.y < other.pos.y + other.height and
                self.pos.y + self.height > other.pos.y and
                self.pos.z < other.pos.z + other.length and
                self.pos.z + self.length > other.pos.z)