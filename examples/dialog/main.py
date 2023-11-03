from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

from QNodeEditor import NodeEditorDialog
from nodes import ConstantNode, OperationNode, OutputNode, SquareRootNode


def run_dialog():
    # Run the dialog and if it is successful, print the result
    succeeded = dialog.exec()
    if succeeded:
        print(dialog.result)


if __name__ == '__main__':

    # Create an application and a main window with a button
    app = QApplication([])
    window = QMainWindow()

    # Create a dialog
    dialog = NodeEditorDialog()
    dialog.editor.available_nodes = {
        'Constant': ConstantNode,
        'Math': {
            'Operation': OperationNode,
            'Square root': SquareRootNode
        },
        'Output': OutputNode
    }
    dialog.editor.output_node = OutputNode

    # Load scene state from a file
    dialog.editor.load('state.json')

    # Create a button that when pressed opens the dialog
    button = QPushButton('Open node editor')
    button.clicked.connect(run_dialog)
    window.setCentralWidget(button)

    # Start the application
    window.show()
    app.exec()
