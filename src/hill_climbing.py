from utils import *
from state import *
from search_result import SearchResult
import random
import time

# ASUMSI truk kosong
def steepest_ascent(truck: TruckState) -> SearchResult:
    start_time = time.perf_counter()

    initial_state = truck.copy()
    current_state = truck.copy()

    maxval = current_state.count_value()
    prevval = maxval

    obj_history = [maxval]
    while True:
        states = current_state.get_neighbors()
        for state in states:
            curval = state.count_value()
            if curval > maxval:
                maxval = curval
                current_state = state
        if maxval == prevval:
            break
        prevval = maxval
        obj_history.append(current_state.count_value())

    duration = time.perf_counter() - start_time

    return SearchResult(
        initial_state=initial_state,
        final_state=current_state,
        obj_history=obj_history,
        duration=duration,
        metrics={
            "iterations": len(obj_history) - 1,
        }
    )

# ASUMSI truk kosong
def stochastic(truck: TruckState) -> SearchResult:
    start_time = time.perf_counter()
    
    initial_state = truck.copy()
    current_state = truck.copy()

    val = current_state.count_value()

    obj_history = [val]
    while True:
        better_state = []
        states = current_state.get_neighbors()
        for state in states:
            curval = state.count_value()
            if curval > val:
                better_state.append(state)
        if len(better_state) == 0:
            break
        current_state = random.choice(better_state)
        val = current_state.count_value()
        obj_history.append(current_state.count_value())

    duration = time.perf_counter() - start_time

    return SearchResult(
        initial_state=initial_state,
        final_state=current_state,
        obj_history=obj_history,
        duration=duration,
        metrics={
            "iterations": len(obj_history) - 1,
        }
    )

def random_restart(truck: TruckState, max_restart = 50) -> SearchResult:
    start_time = time.perf_counter()

    initial_state = truck.copy()
    current_state = truck.copy()
    best_state = initial_state

    restart_count = 0
    maxval = current_state.count_value()
    global_max = maxval
    obj_history = [maxval]

    prevval = maxval
    iter_per_restart = []
    iteration = 0
    while True:
        iteration += 1
        states = current_state.get_neighbors()
        for state in states:
            curval = state.count_value()
            if curval > maxval:
                maxval = curval
                current_state = state
        if maxval == prevval:
            iter_per_restart.append(iteration)
            iteration = 0
            if maxval > global_max:
                best_state = current_state
                global_max = maxval

            if restart_count == max_restart:
                break
            restart_count += 1
            current_state = randomize_pack(truck)
            maxval = current_state.count_value()
            prevval = current_state.count_value()
            
        prevval = maxval
        obj_history.append(current_state.count_value())

    duration = time.perf_counter() - start_time

    return SearchResult(
        initial_state=initial_state,
        final_state=best_state,
        obj_history=obj_history,
        duration=duration,
        metrics={
            "iterations": len(obj_history) - 1,
            "restarts": max_restart,
            "iter_per_restart": iter_per_restart
        }
    )

def sideways_move(truck: TruckState, max_sideways = 50) -> SearchResult:
    start_time = time.perf_counter()

    initial_state = truck.copy()
    current_state = initial_state

    maxval = current_state.count_value()

    obj_history = [maxval]
    prevval = maxval
    side_count = 0
    total_side = 0
    while True:
        side_state = []
        for state in current_state.get_neighbors():
            curval = state.count_value()
            if curval > maxval:
                maxval = curval
                current_state = state
            elif curval == maxval:
                side_state.append(state)
        if maxval == prevval:
            if len(side_state) == 0 or side_count == max_sideways:
                break
            current_state = random.choice(side_state)
            side_count += 1
            total_side += 1
        else:
            side_count = 0
        prevval = maxval
        obj_history.append(current_state.count_value())

    duration = time.perf_counter() - start_time

    return SearchResult(
        initial_state=initial_state,
        final_state=current_state,
        obj_history=obj_history,
        duration=duration,
        metrics={
            "iterations": len(obj_history) - 1,
            "sideways_count": total_side
        }
    )