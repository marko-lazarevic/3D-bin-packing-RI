from typing import List, Tuple, Set
from box import Box  # Your Box class import

class Bin:
    def __init__(self, w: int, d: int, h: int):
        self.width: int = w
        self.depth: int = d
        self.height: int = h
        self.boxes: List[Box] = []
        self.top_surface: List[List[int]] = [[0] * d for _ in range(w)]

        # Initialize candidate positions: all floor positions where a box could start
        self.candidate_positions: Set[Tuple[int, int]] = {
            (x, y)
            for x in range(w)
            for y in range(d)
        }

    def _update_candidates(self, b: Box):
        x0, y0, z0 = b.position
        bw, bd = b.width, b.depth

        # Remove candidate positions inside footprint
        to_remove = set()
        for x in range(x0, min(x0 + bw, self.width)):
            for y in range(y0, min(y0 + bd, self.depth)):
                if (x, y) in self.candidate_positions:
                    to_remove.add((x, y))
        self.candidate_positions.difference_update(to_remove)

        # Add neighbors around the box footprint (+1 offset in all directions)
        neighbors = set()
        for x in range(x0 - 1, x0 + bw + 1):
            for y in range(y0 - 1, y0 + bd + 1):
                if 0 <= x < self.width and 0 <= y < self.depth:
                    neighbors.add((x, y))
        self.candidate_positions.update(neighbors)

    def can_fit(self, b: Box, x: int, y: int, z: int) -> bool:
        """
        Check if box fits at position (x, y, z) inside bin without collisions or unsupported placement.
        """
        if x + b.width > self.width or y + b.depth > self.depth or z + b.height > self.height:
            return False

        # Overlap check
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if not (
                x + b.width <= px or px + placed_box.width <= x or
                y + b.depth <= py or py + placed_box.depth <= y or
                z + b.height <= pz or pz + placed_box.height <= z
            ):
                return False

        # Support check: box bottom must rest on bin floor or existing boxes top surface
        for dx in range(b.width):
            for dy in range(b.depth):
                if z > self.top_surface[x + dx][y + dy]:
                    return False

        return True

    def add_box(self, b: Box, strategy="DBL") -> bool:
        bw, bd, bh = b.width, b.depth, b.height
        candidates = []

        # Filter candidate positions where footprint fits in bin
        valid_candidates = [
            (x, y) for (x, y) in self.candidate_positions
            if x + bw <= self.width and y + bd <= self.depth
        ]

        for (x, y) in valid_candidates:
            # Early reject positions where height + box height > bin height
            if any(self.top_surface[x + dx][y + dy] + bh > self.height
                   for dx in range(bw) for dy in range(bd)):
                continue

            # Determine z needed to place box (max top_surface in footprint)
            z = max(self.top_surface[x + dx][y + dy] for dx in range(bw) for dy in range(bd))

            # Reject if there is any cell lower than max z (would cause overhang)
            if any(self.top_surface[x + dx][y + dy] < z for dx in range(bw) for dy in range(bd)):
                continue

            # Final detailed collision and support check
            if self.can_fit(b, x, y, z):
                candidates.append((x, y, z))

        if not candidates:
            return False

        # Sort candidates according to strategy
        if strategy == "DBL":
            # Deepest-Bottom-Left: prioritize low z, then y, then x
            candidates.sort(key=lambda pos: (pos[2], pos[1], pos[0]))
        elif strategy == "MC":
            candidates.sort(key=lambda pos: -self.contact_score(b, pos))
        elif strategy == "SE":
            candidates.sort(key=lambda pos: (pos[2], self.z_extrusion_score(b, pos)))
        elif strategy == "NS":
            candidates.sort(key=lambda pos: -self.neighbour_score(b, pos))

        # Place box at best candidate
        x, y, z = candidates[0]
        b.position = (x, y, z)
        self.boxes.append(b)

        # Update top surface heights
        for dx in range(bw):
            for dy in range(bd):
                self.top_surface[x + dx][y + dy] = z + bh

        # Update candidate positions with box footprint neighbors
        self._update_candidates(b)

        return True

    def contact_score(self, b: Box, pos: Tuple[int, int, int]) -> int:
        x, y, z = pos
        contact = 0
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if z == pz + placed_box.height:
                overlap_x = max(0, min(x + b.width, px + placed_box.width) - max(x, px))
                overlap_y = max(0, min(y + b.depth, py + placed_box.depth) - max(y, py))
                contact += overlap_x * overlap_y
        return contact

    def z_extrusion_score(self, b: Box, pos: Tuple[int, int, int]) -> int:
        _, _, z = pos
        return z

    def neighbour_score(self, b: Box, pos: Tuple[int, int, int]) -> int:
        x, y, z = pos
        score = 0
        for placed_box in self.boxes:
            px, py, pz = placed_box.position
            if ((px <= x < px + placed_box.width or x <= px < x + b.width) and
                (py <= y < py + placed_box.depth or y <= py < y + b.depth)):
                if pz <= z:
                    score += 1
        return score

    def __repr__(self):
        return f"Bin(w={self.width}, d={self.depth}, h={self.height}, boxes={len(self.boxes)})"
