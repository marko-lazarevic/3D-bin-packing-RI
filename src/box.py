class Box:
    """Box is represeneted by width, height and depth."""
    def __init__(self, w:int, d:int, h:int):
        self.width = w
        self.depth = d
        self.height = h
        self.position = None
        
    def __repr__(self):
        return f"Box(w={self.width}, d={self.depth}, h={self.height}, pos={self.position})"