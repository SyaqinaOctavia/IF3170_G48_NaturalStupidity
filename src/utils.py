import random
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
    def copy(self):
        return Package(self.id, self.pos, self.dim, self.value, self.weight,
                       self.isFragile, self.eta, self.isInside)
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
    def _find(self, packid):
        for pack in self.packs:
            if pack.id == packid:
                return pack
        raise ValueError(f"package id {packid} not found")
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
    def validate_change(self, changed, old):
        # anggep old valid
        inside = [p for p in self.packs if p.isInside]
        if sum(p.weight for p in inside) > self.cap:
            return False
        for pack in changed:
            if not pack.isInside:
                continue
            if not pack.is_valid() or self.is_outside(pack):
                return False
            if any(pack.is_overlap(other) for other in inside if other.id != pack.id):
                return False
            floating, under = self.is_floating(pack)
            if floating or any(un.isFragile for un in under):
                return False
        changed_ids = {pack.id for pack in changed}

        footprints = [pack for pack in old if pack.isInside] + [pack for pack in changed if pack.isInside]
        for pack in inside:
            if pack.id in changed_ids:
                continue
            if any(pack.is_above(flt) for flt in footprints):
                floating, under = self.is_floating(pack)
                if floating or any(u.isFragile for u in under):
                    return False
        return True
    def move_pack(self, packid, newpos):
        pack = self._find(packid)
        if pack.isInside and pack.pos.equal(newpos.x, newpos.y, newpos.z):
            return None
        old = pack.copy()
        pack.pos.move(newpos.x, newpos.y, newpos.z)
        pack.isInside = True
        try:
            return self.copy() if self.validate_change([pack], [old]) else None
        finally:
            pack.pos = old.pos
            pack.isInside = old.isInside
    def rotate_pack(self, packid, axis=0):
        # axis 0 = x, 1 = y, 2 = z
        if axis < 0 or axis > 2:
            return None
        pack = self._find(packid)
        if not pack.isInside:
            return None
        dim = pack.dim
        if (axis == 0 and dim.length == dim.height) or \
            (axis == 1 and dim.width == dim.length) or \
            (axis == 2 and dim.width == dim.height):
            return None
        old = pack.copy()
        if axis == 0:
            pack.dim.rotate_x()
        elif axis == 1:
            pack.dim.rotate_y()
        else:
            pack.dim.rotate_z()
        try:
            return self.copy() if self.validate_change([pack], [old]) else None
        finally:
            pack.dim = old.dim
    def swap_pack(self, id1, id2):
        if (id1 == id2):
            return None
        pack1, pack2 = self._find(id1), self._find(id2)
        if not pack1.isInside and not pack2.isInside:
            return None
        olds = [pack1.copy(), pack2.copy()]
        pack1.isInside, pack2.isInside = pack2.isInside, pack1.isInside
        pack1.pos,pack2.pos = pack2.pos.copy(), pack1.pos.copy()
        try:
            return self.copy() if self.validate_change([pack1, pack2], olds) else None
        finally:
            pack1.pos, pack2.pos = olds[0].pos, olds[1].pos
            pack1.isInside, pack2.isInside = olds[0].isInside, olds[1].isInside

    def drop_height(self, pack, x, z):
        y = 0
        for i_pack in self.packs:
            if (i_pack.isInside and i_pack.id != pack.id and
                x < i_pack.pos.x + i_pack.dim.width and x + pack.dim.width > i_pack.pos.x and
                z < i_pack.pos.z + i_pack.dim.length and z + pack.dim.length > i_pack.pos.z):
                y = max(y, i_pack.pos.y + i_pack.dim.height)
        return y
    def _move_candidates(self, pack):
        w, h, l = pack.dim.width, pack.dim.height, pack.dim.length
        for x in range(self.dim.width - w + 1):
            for z in range(self.dim.length - l + 1):
                y = self.drop_height(pack, x, z)
                if y + h <= self.dim.height:
                    yield Position(x, y, z)
    def get_neighbors(self):
        neighbors = []
        for pack in self.packs:

            for pos in self._move_candidates(pack):
                state = self.move_pack(pack.id, pos)
                if state is not None:
                    neighbors.append(state)
            
            if pack.isInside:
                for axis in range(3):
                    state = self.rotate_pack(pack.id, axis)
                    if state is not None:
                        neighbors.append(state)

        for i in range(len(self.packs)):
            for j in range(i+1, len(self.packs)):
                state = self.swap_pack(self.packs[i].id, self.packs[j].id)
                if state is not None:
                    neighbors.append(state)

        return neighbors
    
    def get_random_neighbor(self,max_attempts = 25):
        """
        Pake ini kalo mau dapat 1 random neighbor secara cepat ges. Kalo pake
        random.choice(get_neighbors()) lama banget cuz get_neighbors itu generate 
        all possible neighbors dulu
        """
        if not self.packs:
            return None
        
        for _ in range(max_attempts):
            selected_function = random.randint(1, 3)
            pack = random.choice(self.packs)

            match selected_function:
                case 1:  # move_pack
                        w, h, l = pack.dim.width, pack.dim.height, pack.dim.length
                        if w <= self.dim.width and h <= self.dim.height and l <= self.dim.length:
                            for _ in range(10):
                                x = random.randint(0, self.dim.width - w)
                                z = random.randint(0, self.dim.length - l)
                                y = self.drop_height(pack, x, z)
                                if y + h <= self.dim.height:
                                    state = self.move_pack(pack.id, Position(x, y, z))
                                    if state is not None:
                                        return state
                case 2:  # rotate_pack
                        axes = [0, 1, 2]
                        random.shuffle(axes)
                        for axis in axes:
                            state = self.rotate_pack(pack.id, axis)
                            if state is not None:
                                return state
                case 3:  # swap_pack
                        others = [p.id for p in self.packs if p.id != pack.id]
                        random.shuffle(others)
                        for other_id in others:
                            state = self.swap_pack(pack.id, other_id)
                            if state is not None:
                                return state
        return None


    def count_value(self):
        # only filter with the isInside boolean since the other helper functions
        # will not flag isInside as true without it being valid first
        return sum(pack.value for pack in self.packs if pack.isInside)