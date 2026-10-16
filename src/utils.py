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
    def equal(self, x, y, z):
        return self.x == x and self.y == y and self.z == z

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
        self.width = self.length
        self.length = temp
    def rotate_z(self):
        temp = self.height
        self.height = self.width
        self.width = temp
    def equal(self, width, height, length):
        return self.length == length and self.height == height and self.width == width

class Package:
    def __init__(self, ident, pos, dim, value, weight, isFragile, eta, isInside):
        self.id = ident
        self.pos = pos.copy()
        self.dim = dim.copy()
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta
        self.isInside = isInside
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
        if(self.pos.y != other.pos.y + other.dim.height):
            return False
        return (self.pos.x < other.pos.x + other.dim.width and
                self.pos.x + self.dim.width > other.pos.x and
                self.pos.z < other.pos.z + other.dim.length and
                self.pos.z + self.dim.length > other.pos.z)

class TruckState:
    def __init__(self, dim, cap, packs):
        self.dim = dim.copy()
        self.cap = cap
        self.packs = [
                        Package(
                            pack.id,
                            pack.pos,
                            pack.dim,
                            pack.value,
                            pack.weight,
                            pack.isFragile,
                            pack.eta,
                            pack.isInside
                        )
                        for pack in packs
                    ]
    def copy(self):
        return TruckState(
            self.dim,
            self.cap,
            [
                Package(
                    pack.id,
                    pack.pos,
                    pack.dim,
                    pack.value,
                    pack.weight,
                    pack.isFragile,
                    pack.eta,
                    pack.isInside
                )
                for pack in self.packs
            ]
        )
    def is_floating(self, pack):
        if(pack.pos.y == 0): 
            return False, []
        supports = [p for p in self.packs if p.isInside and p.id != pack.id and pack.is_above(p)]
        return len(supports) == 0, supports
    def is_outside(self, pack):
        return not (pack.pos.x < self.dim.width and 
                    pack.pos.x + pack.dim.width <= self.dim.width and
                    pack.pos.y < self.dim.height and 
                    pack.pos.y + pack.dim.height <= self.dim.height and
                    pack.pos.z < self.dim.length and 
                    pack.pos.z + pack.dim.length <= self.dim.length)
    def validate_state(self):
        weight = 0
        inside = [p for p in self.packs if p.isInside]
        for i, pack in enumerate(inside):
            if not pack.is_valid() or self.is_outside(pack):
                return False
            for other in inside[i + 1:]:
                if pack.is_overlap(other):
                    return False
            weight += pack.weight
            if weight > self.cap:
                return False

        for pack in inside:
            floating, under = self.is_floating(pack)
            if floating or any(u.isFragile for u in under):
                return False
            
        return True
    def move_pack(self, packid, newpos):
        for pack in self.packs:
            if pack.id == packid:
                if pack.isInside and pack.pos.equal(newpos.x, newpos.y, newpos.z):
                    return None
                old_pos = pack.pos.copy()
                old_inside = pack.isInside
                pack.pos.move(newpos.x, newpos.y, newpos.z)
                pack.isInside = True
                try:
                    return self.copy() if self.validate_state() else None
                finally:
                    pack.pos = old_pos
                    pack.isInside = old_inside
        return None
    def rotate_pack(self, packid, axis=0):
        # axis 0 = x, 1 = y, 2 = z
        if axis < 0 or axis > 2:
            return None
        inside = [p for p in self.packs if p.isInside]
        for pack in inside:
            if pack.id == packid:
                old_dim = pack.dim.copy()
                if axis == 0:
                    pack.dim.rotate_x()
                elif axis == 1:
                    pack.dim.rotate_y()
                else:
                    pack.dim.rotate_z()
                try:
                    return self.copy() if self.validate_state() else None
                finally:
                    pack.dim = old_dim
        return None
    def swap_pack(self, id1, id2):
        swapping = []
        for _, pack in enumerate(self.packs):
            if pack.id == id1 or pack.id == id2:
                swapping.append(pack)
        if len(swapping) != 2:
            raise ValueError(f"package id invalid: expected 2, found {len(swapping)}")
        if not swapping[0].isInside and not swapping[1].isInside:
            return None
        temp = swapping[0].isInside
        swapping[0].isInside = swapping[1].isInside
        swapping[1].isInside = temp
        
        temppos = swapping[0].pos.copy()
        swapping[0].pos = swapping[1].pos.copy()
        swapping[1].pos = temppos

        try:
            return self.copy() if self.validate_state() else None
        finally:
            temp = swapping[0].isInside
            swapping[0].isInside = swapping[1].isInside
            swapping[1].isInside = temp

            temppos = swapping[0].pos.copy()
            swapping[0].pos = swapping[1].pos.copy()
            swapping[1].pos = temppos