from QNodeEditor import Node


class ConstantNode(Node):
    """Constant value node"""
    code = 1

    def create(self) -> None:
        self.title = 'Constant'
        self.add_value_output('Value')

    def evaluate(self, entry_values: dict) -> None:
        value = entry_values['Value']
        self.set_output_value('Value', value)
