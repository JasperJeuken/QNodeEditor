from math import sqrt

from QNodeEditor import Node


class SquareRootNode(Node):
    """Square root node"""
    code = 3

    def create(self) -> None:
        self.title = 'Square root'
        self.add_label_output('Output')
        self.add_value_input('Value')

    def evaluate(self, entry_values: dict) -> None:
        result = sqrt(entry_values['Value'])
        self.set_output_value('Output', result)
