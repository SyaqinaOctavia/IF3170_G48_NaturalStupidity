from utils import *
from state import *
import random

import math

def schedule(t, T0=200.0, alpha=0.995):
    return T0 * (alpha ** t)

def accept_probability(delta, temp):
    return math.exp(delta / temp)


def simmulate_annealing(truck: TruckState) -> TruckState:
    current_state = truck.copy()
    best_state = current_state
    cache = None

    """ 
    The cache is for the edgecase where there is only 1 valid neighbor
    from the current state (almost doomed state but not quite) and then
    that 1 valid neighbor is rejected (thus current state is the same).
    It's to prevent calling get_neighbors() twice on the same state (since
    that function is expensive af)
    """

    t = 1
    while(True):
        T = schedule(t)
        t+=1
        if (T < 1e-3):
            return best_state
        
        if(cache==None):
            next_state = current_state.get_random_neighbor(max_attempts=100)
            if next_state is None:
                all_neighbors = current_state.get_neighbors()
                cache = all_neighbors
                if not all_neighbors:
                    return best_state
                next_state = random.choice(all_neighbors)
        else:
            next_state = random.choice(cache)

        delta = next_state.count_value() - current_state.count_value()
        if(delta>0):
            current_state = next_state
            cache = None
            if next_state.count_value() > best_state.count_value():
                best_state = next_state
        else:
            if (random.random() < accept_probability(delta,T)):
                current_state = next_state
                cache = None

    
        

        

    

