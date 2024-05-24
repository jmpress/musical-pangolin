class MenuItem():
    def __init__(self, text, x_padding = 0, y_padding = 0 ):
        self.text = text
        self.selected = False
        self.x_padding = x_padding
        self.y_padding = y_padding
        self.next = None
        self.prev = None