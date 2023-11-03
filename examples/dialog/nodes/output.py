from QNodeEditor import Node


class OutputNode(Node):
    """Output node"""
    code = 0

    def create(self) -> None:
        self.title = 'Output'
        self.add_label_input('Value 1')
        self.add_label_input('Value 2')
