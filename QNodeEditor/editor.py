"""Widget containing a node scene and view"""
# pylint: disable = no-name-in-module
import os
from typing import Type, TYPE_CHECKING, overload

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from QNodeEditor import NodeScene, NodeView
from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor.node import Node

# Set scaling attributes for large screen resolutions
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


class NodeEditor(QWidget):
    """Node editor widget containing a node scene and view"""

    evaluated: pyqtSignal = pyqtSignal(dict)     # emits result once evaluation is complete
    errored: pyqtSignal = pyqtSignal(Exception)  # emits error if evaluation resulted in error

    def __init__(self, parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create a node scene and view and set the initial state (if specified)
        :param parent: parent widget
        :param theme: theme to use for the node editor
        """
        super().__init__(parent)

        # Create widget layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Create node scene and view
        self.scene: NodeScene = NodeScene(self)
        self.view: NodeView = NodeView(self.scene.graphics)
        layout.addWidget(self.view)

        # Set node editor theme
        self.theme: ThemeType = theme

        # Pass through scene signals
        self.scene.evaluated.connect(self.evaluated.emit)
        self.scene.errored.connect(self.errored.emit)

    @property
    def theme(self) -> ThemeType:
        """
        Get the current node editor theme
        :return: ThemeType: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the node editor
        :param new_theme: new theme
        :return: None
        """
        self._theme = new_theme
        self.view.theme = new_theme

    @property
    def available_nodes(self) -> dict[str, Type['Node'] or dict]:
        """
        Get the (nested) dictionary defining the names and classes of available nodes in the scene
        :return: dict[str, Type[Node] or dict]: (nested) dictionary of (name, Node class) items
        """
        return self.scene.available_nodes

    @available_nodes.setter
    def available_nodes(self, new_available_nodes: dict[str, Type['Node'] or dict]) -> None:
        """
        Set the available nodes in the scene using a (nested) dictionary of (name, Node class) items
        :param new_available_nodes: (nested) dictionary of (name, Node class) items
        :return: None
        """
        self.scene.available_nodes = new_available_nodes

    @property
    def output_node(self) -> Type['Node']:
        """
        Get the type of node that is considered the scene output node
        :return: Type[Node]: type of node that is used for output
        """
        return self.scene.output_node

    @output_node.setter
    @overload
    def output_node(self, code: int) -> None:
        """
        Set the node to use as output by its unique code
        :param code: unique code for node to use as output node
        :return: None
        """

    @output_node.setter
    @overload
    def output_node(self, node_class: Type['Node']) -> None:
        """
        Set the node to use as output by its class definition
        :param node_class: class definition of node to use as output node
        :return: None
        """

    @output_node.setter
    @overload
    def output_node(self, node: 'Node') -> None:
        """
        Set the node to use as output by an instance of the node
        :param node: node instance for which class to use as output node
        :return: None
        """

    @output_node.setter
    def output_node(self, node: 'Node' or Type['Node'] or int or None) -> None:
        """
        Set the type of node to use as the output node
        :param node: code, class definition, or node instance from which to derive output node
        :return: None
        """
        self.scene.output_node = node

    def save(self, filepath: str) -> None:
        """
        Save the scene state to a file
        :param filepath: path of file to save state to
        :return: None
        """
        self.scene.save(filepath)

    def load(self, filepath: str) -> None:
        """
        Load a scene state from a file
        :param filepath: path of file to load state from
        :return: None
        """
        self.scene.load(filepath)
