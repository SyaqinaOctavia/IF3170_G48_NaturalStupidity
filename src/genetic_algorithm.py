from copy import deepcopy
import random
import time
from typing import List
from utils import *
from state import *
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

def crossover(parent1, parent2, crossover_point=None): # Default crossover_point untuk one-point crossover otomatis
    #One-point crossover
    if crossover_point is None:
        crossover_point = random.randint(1, len(parent1.packs) - 1) if len(parent1.packs) > 1 else 0
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    for i in range(crossover_point):
        child1.packs[i], child2.packs[i] = child2.packs[i], child1.packs[i]
    
    return child1, child2


def mutate(state: TruckState, mutation_rate: float = 0.20) -> TruckState:
    #apply 1 random neighbor move
    if random.random() > mutation_rate: #lebih sering tidak mutate
        return state
    neighbor = state.get_random_neighbor(max_attempts=20)

    return neighbor if neighbor else state


def genetic_algorithm(base_truck: TruckState, pop_size: int, iterations: int, mutation_rate: float = 0.20, seed: int = 21) -> SearchResult:
    start_time = time.perf_counter()
    
    # Kosongkan salinan truk terlebih dahulu karena generate_population -> randomize_pack mengasumsikan truk kosong
    empty_truck = base_truck.copy()
    for p in empty_truck.packs:
        p.isInside = False
        p.pos.move(0, 0, 0)
    pop = generate_population(empty_truck, pop_size, seed=seed)
    initial_state = pop[0].copy()
    
    history_max = []
    history_avg = []
    best_state_per_gen = []
    
    best_overall = max(pop, key=lambda s: s.count_value())
    
    for _ in range(iterations):
        # Evaluate
        fitness = [s.count_value() if s.validate_state() else 0 for s in pop]
        max_fit = max(fitness)
        avg_fit = sum(fitness) / len(fitness)
        gen_best = pop[fitness.index(max_fit)]
        
        history_max.append(max_fit)
        history_avg.append(avg_fit)
        best_state_per_gen.append(gen_best.copy())
        
        if max_fit > best_overall.count_value():
            best_overall = gen_best.copy()
        
        # Elitism untuk yang best value
        if pop_size % 2 == 1:
            # Ganjil: 1 elite (best_overall dari generasi sebelumnya)
            elitism = 1
            elites = [best_overall.copy()]
        else:
            # Genap: 2 elite (best_overall + gen_best)
            elitism = 2
            elites = [best_overall.copy(), gen_best.copy()]
        
        # Selection
        selected_pop = selection(pop)
        
        # Crossover
        next_gen = []
        
        idx = 0
        attempts = 0
        while len(next_gen) < pop_size - elitism:
            # Seleksi ulang jika indeks melewati batas selected_pop
            if idx + 1 >= len(selected_pop):
                selected_pop = selection(pop)
                idx = 0
            p1 = selected_pop[idx]
            p2 = selected_pop[idx + 1]
            idx += 2
            attempts += 1
            
            c1, c2 = crossover(p1, p2)
            for child in (c1, c2):
                if child:
                    child = mutate(child, mutation_rate)
                    if child.validate_state():
                        next_gen.append(child)
                        if len(next_gen) >= pop_size - elitism:
                            break
            # Fallback ke mutasi parent jika crossover berulang kali menghasilkan state tidak valid
            if attempts > pop_size * 2 and len(next_gen) < pop_size - elitism:
                fallback = mutate(p1.copy(), mutation_rate)
                if fallback.validate_state():
                    next_gen.append(fallback)
        
        # Next generation
        pop = elites + next_gen[:pop_size - elitism]
        assert len(pop) == pop_size #pastiin jumlah sesuai
    
    duration = time.perf_counter() - start_time
    final_state = best_overall
    
    # Results metrics tambahan
    metrics = {
        'avg_fitness': history_avg,
        'avg_obj_history': history_avg, # Key tambahan agar kompatibel dengan plot_metrics_2d di visualizer.py
        'best_fitness_per_gen': history_max,
        'best_state_per_gen': best_state_per_gen,
        'pop_size': pop_size,
        'iterations': iterations,
        'max_iter': iterations, # Key tambahan agar kompatibel dengan tabel ringkasan di app.py
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
        result = genetic_algorithm(base_truck, pop_size, iteration, 0.20, seed=seed)
        results.append(result)
    return results