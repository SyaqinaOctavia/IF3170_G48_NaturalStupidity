import random
import time
from utils import *
from state import *
from typing import List, Tuple
from search_result import SearchResult

def selection(population):
    #Roulette Wheel Selection (bobot berdasarkan fitness)
    if not population:
        return []
    fitness_values = [ch.count_value() for ch in population]
    total_fitness = sum(fitness_values)

    if total_fitness == 0:
            return random.choices(population, k=len(population))
    
    selection_probs = [f / total_fitness for f in fitness_values]
    selected_indices = random.choices(range(len(population)), weights=selection_probs, k=len(population))
    
    return [population[i] for i in selected_indices]

def crossover_one_child(parent1: TruckState, parent2: TruckState, base_state: TruckState) -> TruckState:
    child = base_state.copy()
    n = len(child.packs)
    
    for i in range(n):
        
        # i ganjil -> cek p1 dulu
        if i % 2 == 1: 
            first, second = parent1, parent2
        else:      
            first, second = parent2, parent1
        
        child.packs[i] = first.packs[i].copy()
        if child.validate_state():
            continue  
        #jika parent 1 tidak bikin valid, coba parent 2
        child.packs[i] = second.packs[i].copy()
        if child.validate_state():
            continue  
        
        child.packs[i].isInside = False
    
    return child

def crossover(parent1: TruckState, parent2: TruckState, base_state: TruckState) -> Tuple[TruckState, TruckState]:
    child1 = crossover_one_child(parent1, parent2, base_state)
    child2 = crossover_one_child(parent2, parent1, base_state)
    return child1, child2


def mutate(state: TruckState, mutation_rate: float = 0.20) -> TruckState:
    #apply 1 random neighbor move
    if random.random() > mutation_rate: #lebih sering tidak mutate
        return state
    neighbor = state.get_random_neighbor(max_attempts=20)

    return neighbor if neighbor else state


def genetic_algorithm(base_truck: TruckState, pop_size: int, iterations: int, mutation_rate: float, seed: int = 21) -> SearchResult:
    start_time = time.perf_counter()
    
    empty_truck = base_truck.copy()
    for p in empty_truck.packs:
        p.isInside = False
        p.pos.move(0, 0, 0)

    population = generate_population(empty_truck, pop_size, seed=seed)
    initial_state = max(population, key=lambda s: s.count_value()).copy()
    
    history_max = []
    history_avg = []
    best_state_per_gen = []
    
    for _ in range(iterations):
        # Evaluate
        fitness = [s.count_value() if s.validate_state() else 0 for s in population]
        max_fit = max(fitness)
        avg_fit = sum(fitness) / len(fitness)
        gen_best = population[fitness.index(max_fit)]
        
        history_max.append(max_fit)
        history_avg.append(avg_fit)
        best_state_per_gen.append(gen_best.copy())

        # Elitism hanya jika pop_size ganjil
        if pop_size % 2 == 1:
            elitism = 1
            elites = [population[-1].copy()] 
        else:
            elitism = 0
            elites = []
        
        # Selection
        selected_pop = selection(population)
        
        # Crossover
        next_gen = []
        
        idx = 0
        attempts = 0
        max_attempts = max(pop_size * 10, 100)
        n_parents = len(selected_pop)
        while len(next_gen) < pop_size - elitism and attempts < max_attempts:
            p1 = selected_pop[idx % n_parents]
            p2 = selected_pop[(idx + 1) % n_parents]
            idx += 2
            attempts += 1
            
            c1, c2 = crossover(p1, p2, base_truck)
            for child in (c1, c2):
                if child:
                    child = mutate(child, mutation_rate)
                    if child.validate_state():
                        next_gen.append(child)
                        if len(next_gen) >= pop_size - elitism:
                            break
        
        # gabung dengan elit nya
        while len(next_gen) < pop_size - elitism:
            next_gen.append(gen_best.copy())

        # Next generation
        population = elites + next_gen[:pop_size - elitism]
        assert len(population) == pop_size #pastiin jumlah sesuai
    
    duration = time.perf_counter() - start_time
    final_state = gen_best
    
    # Results metrics tambahan
    metrics = {
        'avg_fitness': history_avg,
        'avg_obj_history': history_avg, 
        'best_fitness_per_gen': history_max,
        'best_state_per_gen': best_state_per_gen,
        'pop_size': pop_size,
        'iterations': iterations,
        'max_iter': iterations, 
        'mutation_rate': mutation_rate,
        'final_fitness': final_state.count_value(),
    }
    
    return SearchResult(
        initial_state=initial_state,
        final_state=final_state,
        obj_history=history_max,
        duration=duration,
        metrics=metrics
    )

def run_ga(base_truck: TruckState, pop_size: int, iteration: int, n_runs: int = 3) -> List[SearchResult]:
    results = []
    seed_base = 21
    for i in range(n_runs):
        seed = seed_base + i
        result = genetic_algorithm(base_truck, pop_size, iteration, 0.2, seed=seed)
        results.append(result)
    return results