from operator import add, sub, mul, truediv

from QNodeEditor import Node


class OperationNode(Node):
    """Operation node"""
    code = 2

    operations = {
        'Add': add,
        'Subtract': sub,
        'Multiply': mul,
        'Divide': truediv
    }

    def create(self) -> None:
        self.title = 'Operation'
        self.add_label_output('Output')
        self.add_combo_box_entry('Operation', self.operations)
        self.add_value_input('Value 1')
        self.add_value_input('Value 2')

    def evaluate(self, entry_values: dict) -> None:
        operation = entry_values['Operation']
        value1 = entry_values['Value 1']
        value2 = entry_values['Value 2']

        result = operation(value1, value2)
        self.set_output_value('Output', result)
