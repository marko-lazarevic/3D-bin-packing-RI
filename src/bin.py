from box import Box 
from typing import List

class Bin:
    def __init__(self, w: int, d: int, h: int):
        self.width: int = w
        self.depth: int = d
        self.height: int = h
        self.boxes: List[Box] = []  # List of boxes in the bin
        self.top_surface: List[List[int]] = [[0] * d for _ in range(w)]  # Tracks the height at each (x, y) position


    def can_fit(self, b: Box, x: int, y: int, z: int) -> bool:
        """
        Check if the box can fit at position (x, y, z) without overlapping others,
        staying within the bin's dimensions, and being properly supported.
        """
        # Check if the box fits within the bin boundaries
        if x + b.width > self.width or y + b.depth > self.depth or z + b.height > self.height:
            return False

        # Check for overlap with existing boxes
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if not (
                x + b.width <= px or px + placed_box.width <= x or
                y + b.depth <= py or py + placed_box.depth <= y or
                z + b.height <= pz or pz + placed_box.height <= z
            ):
                return False

        # Check if the box is supported (must rest on the bottom or another box)
        for dx in range(b.width):
            for dy in range(b.depth):
                if z > self.top_surface[x + dx][y + dy]:
                    return False

        return True

    def add_box(self, b: Box, strategy="DBL") -> bool:
        """
        Try to place the box in the bin using the specified strategy.
        If successful, assign its position and return True. Otherwise, return False.
        """
        candidates = []

        for x in range(self.width - b.width + 1):
            for y in range(self.depth - b.depth + 1):
                z = max(self.top_surface[x + dx][y + dy] for dx in range(b.width) for dy in range(b.depth))
                if self.can_fit(b, x, y, z):
                    candidates.append((x, y, z))

        if not candidates:
            return False

        # Apply the placement strategy
        if strategy == "DBL":
            # Deepest-bottom-leftmost: prioritize low z, then y, then x
            candidates.sort(key=lambda pos: (pos[2], pos[1], pos[0]))
        elif strategy == "MC":
            # Maximum contact: prioritize positions with maximum contact area
            candidates.sort(key=lambda pos: -self.contact_score(b, pos))
        elif strategy == "SE":
            # Smallest extrusion: prioritize low z with minimal z-axis extrusion
            candidates.sort(key=lambda pos: (pos[2], self.z_extrusion_score(b, pos)))
        elif strategy == "NS":
            # Neighbour score: prioritize touching boxes with equal or lower z
            candidates.sort(key=lambda pos: -self.neighbour_score(b, pos))

        # Place the box at the best candidate position
        x, y, z = candidates[0]
        b.position = (x, y, z)
        self.boxes.append(b)

        # Update the top surface
        for dx in range(b.width):
            for dy in range(b.depth):
                self.top_surface[x + dx][y + dy] = z + b.height

        return True

    def contact_score(self, b: Box, pos: tuple) -> int:
        """
        Calculate the contact area score for the box at a given position.
        """
        x, y, z = pos
        contact = 0
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if z == pz + placed_box.height:
                # Check overlap in x-y plane
                overlap_x = max(0, min(x + b.width, px + placed_box.width) - max(x, px))
                overlap_y = max(0, min(y + b.depth, py + placed_box.depth) - max(y, py))
                contact += overlap_x * overlap_y
        return contact

    def z_extrusion_score(self, b: Box, pos: tuple) -> int:
        """
        Calculate the extrusion score (how much the box extrudes on the z-axis).
        """
        x, y, z = pos
        return z

    def neighbour_score(self, b: Box, pos: tuple) -> int:
        """
        Calculate the neighbour score: count how many touching boxes have equal or lower z.
        """
        x, y, z = pos
        score = 0
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if (
                (px <= x < px + placed_box.width or x <= px < x + b.width) and
                (py <= y < py + placed_box.depth or y <= py < y + b.depth)
            ):
                if pz <= z:
                    score += 1
        return score

    def __repr__(self):
        return f"Bin(w={self.width}, d={self.depth}, h={self.height}, boxes={self.boxes})"