class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def copy(self):
        return Position(self.x, self.y, self.z)
    def move(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Dimension:
    def __init__(self, width, height, length):
        self.width = width
        self.length = length
        self.height = height
    def copy(self):
        return Dimension(self.width, self.height, self.length)
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
    def __init__(self, id, pos, dim, value, weight, isFragile, eta):
        self.id = id
        self.pos = pos.copy()
        self.dim = dim.copy()
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta
    def is_valid(self):
        return (self.pos.x >= 0 and 
                self.pos.y >= 0 and 
                self.pos.z >= 0 and
                self.dim.width > 0 and
                self.dim.length > 0 and
                self.dim.height > 0)
    def is_overlap(self, other):
        return (self.pos.x < other.pos.x + other.dim.width and
                self.pos.x + self.dim.width > other.pos.x and
                self.pos.y < other.pos.y + other.dim.height and
                self.pos.y + self.dim.height > other.pos.y and
                self.pos.z < other.pos.z + other.dim.length and
                self.pos.z + self.dim.length > other.pos.z)
    def is_above(self, other):
        if(self.pos.y != other.pos.y + other.height):
            return False
        return (self.pos.x < other.pos.x + other.dim.width and
                self.pos.x + self.dim.width > other.pos.x and
                self.pos.z < other.pos.z + other.dim.length and
                self.pos.z + self.dim.length > other.pos.z)

class TruckState:
    def __init__(self, dim, cap, packs):
        self.dim = dim.copy()
        self.cap = cap
        self.packs = packs.copy()
    def is_floating(self, pack):
        if(pack.pos.y == 0): 
            return False, None
        for _, i_pack in enumerate(self.packs):
            if i_pack.id == pack.id:
                continue
            if pack.is_above(i_pack):
                return False, i_pack
        return True, None
    def is_outside(self, pack):
        return not (pack.pos.x < self.dim.width and 
                    pack.pos.x + pack.dim.width <= self.dim.width and
                    pack.pos.y < self.dim.height and 
                    pack.pos.y + pack.dim.height <= self.dim.height and
                    pack.pos.z < self.dim.length and 
                    pack.pos.z + pack.dim.length <= self.dim.length)
    def is_overlap(self, pack):
        for _, i_pack in enumerate(self.packs):
            if i_pack.id == pack.id:
                continue
            if pack.is_overlap(i_pack):
                return True, i_pack
        return False, None
    def validate_state(self):
        weight = 0
        for _, pack in enumerate(self.packs):
            if not pack.is_valid():
                return False
            if self.is_overlap(pack):
                return False
            isfloat, under = self.is_floating(pack)
            if isfloat:
                return False
            if under is not None:
                if under.isFragile:
                    return False
            if self.is_outside(pack):
                return False
            weight += pack.weight
        return weight <= self.cap