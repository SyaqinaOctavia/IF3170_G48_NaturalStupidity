from utils import *
from state import *
from search_result import SearchResult
import random
import math
import time

def schedule(t, T0=200.0, alpha=0.995):
    return T0 * (alpha ** t)

def accept_probability(delta, temp):
    return math.exp(delta / temp)

def simmulate_annealing(truck: TruckState, T0: float = 200.0, alpha: float = 0.995) -> SearchResult:
    start_time = time.perf_counter()

    initial_state = truck.copy()
    current_state = truck.copy()
    best_state = current_state.copy()
    cache = None

    """ 
    The cache is for the edgecase where there is only 1 valid neighbor
    from the current state (almost doomed state but not quite) and then
    that 1 valid neighbor is rejected (thus current state is the same).
    It's to prevent calling get_neighbors() twice on the same state (since
    that function is expensive af)
    """

    obj_history = [current_state.count_value()]
    e_delta_t_history = []
    stuck_count = 0

    t = 1
    while True:
        T = schedule(t, T0=T0, alpha=alpha)
        t += 1
        if T < 1e-3:
            break

        if cache is None:
            next_state = current_state.get_random_neighbor(max_attempts=100)
            if next_state is None:
                all_neighbors = current_state.get_neighbors()
                cache = all_neighbors
                if not all_neighbors:
                    break
                next_state = random.choice(all_neighbors)
        else:
            next_state = random.choice(cache)

        delta = next_state.count_value() - current_state.count_value()
        if delta > 0:
            e_delta_t_history.append(1.0)
            current_state = next_state
            cache = None
            if next_state.count_value() > best_state.count_value():
                best_state = next_state.copy()
        else:
            prob = accept_probability(delta, T)
            e_delta_t_history.append(prob)
            if random.random() < prob:
                current_state = next_state
                cache = None
            else:
                stuck_count += 1

        obj_history.append(current_state.count_value())

    duration = time.perf_counter() - start_time

    return SearchResult(
        initial_state=initial_state,
        final_state=best_state,
        obj_history=obj_history,
        duration=duration,
        metrics={
            "iterations": len(obj_history) - 1,
            "e_delta_t_history": e_delta_t_history,
            "stuck_count": stuck_count,
            "final_current_value": current_state.count_value(),
            "best_value": best_state.count_value(),
        }
    )

    

