from time import sleep
from IPython.display import clear_output
from binplot import plot_bins
from copy import deepcopy
from itertools import permutations
from typing import List, Tuple
from box import Box
from bin import Bin
from load_data import load_test_data
import os
import re
from splitter import split_bin_randomly, Box, write_boxes_to_file
import random
import plotly.graph_objects as go



def pack_boxes_into_bins(boxes:List[Box], bin_size:Tuple[int, int, int], strategy="DBL"):
    """
    Put all boxes in bins using the specified placement strategy.
    """
    bins = []
    for box in boxes:
        # Try to place the box in an existing bin
        placed = False
        for bin in bins:
            if bin.add_box(box, strategy):
                placed = True
                break
        # If the box doesn't fit in any existing bin, create a new bin
        if not placed:
            new_bin = Bin(*bin_size)
            new_bin.add_box(box, strategy)
            bins.append(new_bin)
    return bins


def pack_boxes_into_bins_interactive(boxes, bin_size):
    """
    Put all boxes in bins in the given order, visualizing the process interactively.
    """
    bins = []
    for i, box in enumerate(boxes):
        placed = False
        for bin in bins:
            if bin.add_box(box):
                placed = True
                break
        if not placed:
            new_bin = Bin(*bin_size)
            new_bin.add_box(box)
            bins.append(new_bin)

        # Visualize after each box is placed
        clear_output(wait=True)
        print(f"Placing box {i + 1}/{len(boxes)}...")
        plot_bins(bins)
        sleep(1)  # Pause for a moment to make the visualization interactive

    return bins

def brute_force(boxes, bin_size, interactive=False):
    best_solution = None
    for p in permutations(boxes):
        p_copy = [deepcopy(box) for box in p]
        sol = pack_boxes_into_bins_interactive(p_copy,bin_size) if interactive else pack_boxes_into_bins(p_copy,bin_size)
        if best_solution is None or len(sol) < len(best_solution):
            best_solution = sol 
    return best_solution

def execute_bin_packing(fnc: callable, file_path:str, loader: callable = load_test_data, plot_fnc: callable = plot_bins):
    bin_size, boxes = loader(file_path)
    bins = fnc(boxes, bin_size)
    plot_fnc(bins)

    print(f"Number of bins used: {len(bins)}")
    for i, bin in enumerate(bins, 1):
        print(f"Bin {i}: {bin}")

def test_bin_packing(fnc: callable, folder_path: str, loader: callable = load_test_data):
    """
    For each file in the folder, run the bin packing function and compare the result to the expected number of bins.
    """
    total_executed = 0
    total_passed = 0
    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith('.txt'):
            continue
        file_path = os.path.join(folder_path, filename)
        # Read expected number of bins from file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        expected_bins = None
        for line in lines:
            match = re.search(r'#Number of Bins:\s*(\d+)', line)
            if match:
                expected_bins = int(match.group(1))
                break
        if expected_bins is None:
            print(f"[{filename}] No expected bin count found. Skipping.")
            continue
        total_executed = total_executed + 1
        # Run bin packing
        bin_size, boxes = loader(file_path)
        bins = fnc(boxes, bin_size)
        actual_bins = len(bins)
        # Print test result
        print(f"Test: {filename}")
        print(f"Expected bins: {expected_bins}, Actual bins: {actual_bins}")
        print("Result:", "PASS" if actual_bins == expected_bins else "FAIL")
        print("-" * 40)
        if actual_bins == expected_bins:
            total_passed = total_passed + 1
    print(f"PASSED {total_passed} of {total_executed} tests")

def genearte_example(num_bins :int = 10, w :int = 10, d:int = 10, h:int =10, max_boxes:int = 5, filename :str = "./data/example_data.txt"):
    all_boxes = []

    for i in range(num_bins):
        boxes = split_bin_randomly(w, d, h, max_boxes)
        all_boxes.extend(boxes)

    random.shuffle(all_boxes)  # Shuffle boxes to randomize their order
    write_boxes_to_file(filename, (w, d, h), all_boxes, num_bins)

def random_partition(n, num_parts):
    """Split integer n into num_parts positive integers randomly."""
    if num_parts == 1:
        return [n]
    cuts = sorted(random.sample(range(1, n), k=num_parts - 1))
    return [b - a for a, b in zip([0] + cuts, cuts + [n])]

def try_split(box: Box, position, axis, max_splits=3):
    """Attempt to split a box along the given axis into 2 or 3 pieces."""
    w, d, h = box.width, box.depth, box.height
    x, y, z = position
    new_boxes = []

    if axis == 'x' and w > 1:
        num_parts = random.randint(2, min(3, max_splits))
        cuts = random_partition(w, num_parts)
        offset = x
        for cw in cuts:
            new_box = Box(cw, d, h)
            new_boxes.append(((offset, y, z), new_box))
            offset += cw

    elif axis == 'y' and d > 1:
        num_parts = random.randint(2, min(3, max_splits))
        cuts = random_partition(d, num_parts)
        offset = y
        for cd in cuts:
            new_box = Box(w, cd, h)
            new_boxes.append(((x, offset, z), new_box))
            offset += cd

    elif axis == 'z' and h > 1:
        num_parts = random.randint(2, min(3, max_splits))
        cuts = random_partition(h, num_parts)
        offset = z
        for ch in cuts:
            new_box = Box(w, d, ch)
            new_boxes.append(((x, y, offset), new_box))
            offset += ch

    return new_boxes if new_boxes else None

def split_bin_limited(bin: Bin, max_pieces: int = 6):
    """Split a bin into up to max_pieces boxes randomly (1 to max_pieces)."""
    target_pieces = random.randint(1, max_pieces)

    box_queue = [((0, 0, 0), Box(bin.width, bin.depth, bin.height))]
    result = []

    while len(result) + len(box_queue) < target_pieces and box_queue:
        pos, box = box_queue.pop(0)
        axis = random.choice(['x', 'y', 'z'])
        remaining_splits = target_pieces - len(result) - len(box_queue)
        new_boxes = try_split(box, pos, axis, max_splits=min(3, remaining_splits + 1))

        if new_boxes:
            box_queue.extend(new_boxes)
        else:
            box.position = pos
            result.append(box)

    for pos, box in box_queue:
        box.position = pos
        result.append(box)

    bin.boxes = result


def visualize_bin(bin: Bin):
    fig = go.Figure()

    colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'yellow', 'pink']

    for i, box in enumerate(bin.boxes):
        x, y, z = box.position
        fig.add_trace(go.Mesh3d(
            x=[x, x+box.width, x+box.width, x, x, x+box.width, x+box.width, x],
            y=[y, y, y+box.depth, y+box.depth, y, y, y+box.depth, y+box.depth],
            z=[z, z, z, z, z+box.height, z+box.height, z+box.height, z+box.height],
            color=colors[i % len(colors)],
            opacity=0.5,
            alphahull=0
        ))

    fig.update_layout(scene=dict(
        xaxis_title='Width',
        yaxis_title='Depth',
        zaxis_title='Height',
    ))
    fig.show()

def initialize_permutation(n):
    """Return a random permutation of n elements."""
    perm = list(range(n))
    random.shuffle(perm)
    return perm

def calc_fitness_perm(perm, boxes, bin_size):
    """Fitness = number of bins used for this permutation of boxes."""
    permuted_boxes = [deepcopy(boxes[i]) for i in perm]
    bins = pack_boxes_into_bins(permuted_boxes, bin_size)
    return len(bins)

def neighbor_operations(perm):
    """Enhanced neighbor generation with multiple operations for better solution diversity."""
    n = len(perm)
    if n < 2:
        return perm.copy()
    
    # Choose operation type randomly
    operation = random.choice(['swap', 'insert', 'reverse', 'scramble', 'shift'])
    new_perm = perm.copy()
    
    if operation == 'swap':
        # Basic swap operation
        i, j = random.sample(range(n), 2)
        new_perm[i], new_perm[j] = new_perm[j], new_perm[i]
        
    elif operation == 'insert':
        # Remove element and insert at different position
        i = random.randint(0, n-1)
        j = random.randint(0, n-1)
        if i != j:
            element = new_perm.pop(i)
            new_perm.insert(j, element)
            
    elif operation == 'reverse':
        # Reverse a subsequence
        if n >= 3:
            i = random.randint(0, n-3)
            j = random.randint(i+2, n-1)
            new_perm[i:j+1] = reversed(new_perm[i:j+1])
            
    elif operation == 'scramble':
        # Scramble a small subsequence
        if n >= 3:
            size = min(random.randint(2, 4), n)
            start = random.randint(0, n-size)
            subseq = new_perm[start:start+size]
            random.shuffle(subseq)
            new_perm[start:start+size] = subseq
            
    elif operation == 'shift':
        # Shift elements left or right
        if n >= 3:
            direction = random.choice(['left', 'right'])
            positions = random.randint(1, n//2)
            if direction == 'left':
                new_perm = new_perm[positions:] + new_perm[:positions]
            else:
                new_perm = new_perm[-positions:] + new_perm[:-positions]
    
    return new_perm

def simulated_annealing_binpacking(boxes, bin_size, num_iters=100):
    """
    Enhanced simulated annealing for 3D bin packing with better neighbor generation.
    """
    n = len(boxes)
    perm = initialize_permutation(n)
    fitness = calc_fitness_perm(perm, boxes, bin_size)
    best_perm = deepcopy(perm)
    best_fitness = fitness

    for it in range(2, num_iters + 2):
        new_perm = neighbor_operations(perm)
        new_fitness = calc_fitness_perm(new_perm, boxes, bin_size)
        
        if new_fitness < fitness:
            perm = new_perm
            fitness = new_fitness
            if new_fitness < best_fitness:
                best_fitness = new_fitness
                best_perm = deepcopy(new_perm)
        else:
            p = random.random()
            q = 1 / it
            if p < q:
                perm = new_perm
                fitness = new_fitness
                
    # Convert best permutation back to actual box sequence
    best_boxes = [deepcopy(boxes[i]) for i in best_perm]
    best_bins = pack_boxes_into_bins(best_boxes, bin_size)
    return best_bins

def simulated_annealing(boxes, bin_size, num_iters=1000):
    """SA wrapper function compatible with test framework."""
    return simulated_annealing_binpacking(boxes, bin_size, num_iters)    
def fast_simulated_annealing(boxes, bin_size, num_iters=100):
    """Fast SA with reduced iterations for testing."""
    return simulated_annealing_binpacking(boxes, bin_size, num_iters)
