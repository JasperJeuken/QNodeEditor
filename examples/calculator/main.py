import traceback

from PyQt5.QtWidgets import QApplication
from QNodeEditor import NodeEditor, Edge

from nodes import ConstantNode, OperationNode, OutputNode, SquareRootNode


def handle_result(result: dict):
    """Function that handles the result from scene evaluation"""
    print(result)


def handle_error(error: Exception):
    """Function that handles in any errors that occur during scene evaluation"""
    traceback.print_exception(error)


if __name__ == '__main__':
    # Create an application and a node editor
    app = QApplication([])
    editor = NodeEditor()

    # Add the node definitions to the scene and set the output node
    editor.available_nodes = {
        'Constant': ConstantNode,
        'Math': {
            'Operation': OperationNode,
            'Square root': SquareRootNode
        },
        'Output': OutputNode
    }
    editor.output_node = OutputNode

    # Create two nodes
    node_constant = ConstantNode('Constant')
    node_output = OutputNode('Output')
    node_constant.graphics.setPos(-200, 0)
    node_output.graphics.setPos(200, 0)
    editor.scene.add_nodes([node_constant, node_output])

    # Add an edge between the nodes
    edge = Edge(node_constant['Value'], node_output['Value'])

    # Connect functions to scene evaluation and errors
    editor.evaluated.connect(handle_result)
    editor.errored.connect(handle_error)

    # Start the application
    editor.show()
    app.exec()
