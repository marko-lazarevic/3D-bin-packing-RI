from typing import Tuple, List
from box import Box

def load_test_data(file_path: str) -> Tuple[Tuple[int, int, int], List[Box]]:
    """
    Load bin size and boxes from a file.
    
    Args:
        file_path (str): Path to the input file.
        
    Returns:
        Tuple[Tuple[int, int, int], List[Box]]: A tuple containing bin size and a list of boxes.
    """
    bin_size = None
    boxes = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("Bin:"):
            # Parse bin size
            _, dimensions = line.split(":")
            bin_size = tuple(map(int, dimensions.strip().split(",")))
        elif line.startswith("Box:"):
            # Parse box dimensions
            _, dimensions = line.split(":")
            w, d, h = map(int, dimensions.strip().split(","))
            boxes.append(Box(w, d, h))

    if bin_size is None:
        raise ValueError("Bin size not found in the input file.")

    return bin_size, boxes
