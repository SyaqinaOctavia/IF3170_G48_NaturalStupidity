from utils import *
import random

def min_height(truck, x, z, w, l):
    y = 0
    for pack in truck.packs:
        if (pack.isInside and 
        x < pack.pos.x + pack.dim.width and x + w > pack.pos.x and
        z < pack.pos.z + pack.dim.length and z + l > pack.pos.z):
            y = max(y, pack.pos.y + pack.dim.height)
    return y

# randomize truck state
def random_state(truck_dim, cap, n_packs, max_attempts=50, fragile_prob=0.2, seed=None):
    rng = random.Random(seed)
    W, H, L = truck_dim.width, truck_dim.height, truck_dim.length

    packs = []
    for i in range(n_packs):
        dim = Dimension(rng.randint(1, max(1, W // 2)),
                        rng.randint(1, max(1, H // 2)),
                        rng.randint(1, max(1, L // 2)))
        packs.append(Package(
            i, Position(0, 0, 0), dim,
            value=rng.randint(1, 100),
            weight=rng.randint(1, max(1, cap // 3)),
            isFragile=rng.random() < fragile_prob,
            eta=rng.randint(1, 10),
            isInside=False,
        ))
    state = TruckState(truck_dim, cap, packs)

    order = list(range(n_packs))
    rng.shuffle(order)
    for pid in order:
        pack = next(p for p in state.packs if p.id == pid)
        w, h, l = pack.dim.width, pack.dim.height, pack.dim.length
        if w > W or l > L or h > H:
            continue
        for _ in range(max_attempts):
            x = rng.randint(0, W - w)
            z = rng.randint(0, L - l)
            y = min_height(state, x, z, w, l)
            if y + h > H:
                continue
            new_state = state.move_pack(pid, Position(x, y, z))
            if new_state is not None:   # valid → accept
                state = new_state
                break

    assert state.validate_state()
    return state

# randomize packs inside truck
# ASUMSI truk kosong
def randomize_pack(truck, max_attempts=50, seed=None):
    rng = random.Random(seed)
    W, H, L = truck.dim.width, truck.dim.height, truck.dim.length
    state = truck.copy()

    order = list(range(len(truck.packs)))
    rng.shuffle(order)
    for pid in order:
        pack = next(p for p in state.packs if p.id == pid)
        w, h, l = pack.dim.width, pack.dim.height, pack.dim.length
        if w > W or l > L or h > H:
            continue
        for _ in range(max_attempts):
            x = rng.randint(0, W - w)
            z = rng.randint(0, L - l)
            y = min_height(state, x, z, w, l)
            if y + h > H:
                continue
            new_state = state.move_pack(pid, Position(x, y, z))
            if new_state is not None:
                state = new_state
                break

    assert state.validate_state()
    return state

def generate_population( base_truck, K, max_attempts=50, max_retries=100, seed=None,
):
    """
    Menghasilkan K kromosom untuk populasi awal GA.
    Return: List berisi K objek TruckState yang valid.
    """
    if K <= 0:
        raise ValueError("K harus lebih besar dari 0.")

    rng = random.Random(seed)
    population = []

    for i in range(K):
        chromosome = None

        for _ in range(max_retries):
            candidate = randomize_pack(
                base_truck,
                max_attempts=max_attempts,
                seed=rng.randint(0, 2**32 - 1),
            )

            if candidate is not None and candidate.validate_state():
                chromosome = candidate
                break

        if chromosome is None:
            raise RuntimeError(
                f"Gagal menghasilkan kromosom ke-{i + 1} "
                f"setelah {max_retries} percobaan."
            )

        population.append(chromosome)

    assert len(population) == K
    return population