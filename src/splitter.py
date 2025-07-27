import random
from typing import List, Tuple
from box import Box
from bin import Bin
import plotly.graph_objects as go

def try_split(box: Box, pos: tuple, axis: str, max_splits: int) -> List[Box]:
    # Minimum size for any box dimension to be considered splittable
    MIN_SIZE = 2
    
    dim = {'x': box.width, 'y': box.depth, 'z': box.height}[axis]
    if dim < MIN_SIZE:
        return []

    # Number of splits between 1 and min(5, max_splits)
    num_splits = random.randint(1, min(5, max_splits))

    if dim <= num_splits:
        return []  # can't split evenly

    # Generate unique random cut points inside the dimension
    cuts = sorted(random.sample(range(1, dim), num_splits))
    cuts = [0] + cuts + [dim]
    sizes = [cuts[i+1] - cuts[i] for i in range(len(cuts) - 1)]

    # Check min size for all pieces
    if any(size < MIN_SIZE for size in sizes):
        return []  # Reject split that creates too small pieces

    new_boxes = []
    offset = 0
    for size in sizes:
        if axis == 'x':
            new_box = Box(size, box.depth, box.height)
            new_box.position = (pos[0] + offset, pos[1], pos[2])
        elif axis == 'y':
            new_box = Box(box.width, size, box.height)
            new_box.position = (pos[0], pos[1] + offset, pos[2])
        else:
            new_box = Box(box.width, box.depth, size)
            new_box.position = (pos[0], pos[1], pos[2] + offset)
        new_boxes.append(new_box)
        offset += size

    return new_boxes


def split_bin_randomly(w: int, d: int, h: int, max_boxes: int = 10) -> List[Box]:
    my_bin = Bin(w, d, h)
    initial_box = Box(w, d, h)
    initial_box.position = (0, 0, 0)
    my_bin.boxes.append(initial_box)

    max_attempts = 20

    for _ in range(max_attempts):
        if len(my_bin.boxes) >= max_boxes:
            break
        if not my_bin.boxes:
            break

        idx = random.randint(0, len(my_bin.boxes) - 1)
        box_to_split = my_bin.boxes.pop(idx)
        pos = box_to_split.position or (0, 0, 0)

        # Weight axis selection by box size (prefer splitting along larger dimension)
        dims = {'x': box_to_split.width, 'y': box_to_split.depth, 'z': box_to_split.height}
        axes = list(dims.keys())
        weights = [dims[axis] for axis in axes]
        total = sum(weights)
        weights = [w / total for w in weights]
        axis = random.choices(axes, weights=weights, k=1)[0]

        remaining = max_boxes - len(my_bin.boxes)
        new_boxes = try_split(box_to_split, pos, axis, max_splits=remaining)

        if new_boxes and len(new_boxes) + len(my_bin.boxes) <= max_boxes:
            my_bin.boxes.extend(new_boxes)
        else:
            box_to_split.position = pos
            my_bin.boxes.append(box_to_split)

    return my_bin.boxes

def write_boxes_to_file(filename: str, bin_size: tuple, boxes: list[Box], num_bins: int):
    with open(filename, 'w') as f:
        f.write(f"Bin: {bin_size[0]}, {bin_size[1]}, {bin_size[2]}\n")
        for b in boxes:
            f.write(f"Box: {b.width}, {b.depth}, {b.height}\n")
        f.write("####################\n")
        f.write(f"#Expected Output: {num_bins}\n")
        f.write(f"#Number of Bins: {num_bins}.\n")
