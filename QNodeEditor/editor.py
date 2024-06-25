"""
Widget containing a node scene and view.

This module contains a class derived from QWidget. The widget contains an interactive node scene
which can be edited at runtime by the user.
"""
# pylint: disable = no-name-in-module
import os
from typing import Type, TYPE_CHECKING, overload

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtCore import Qt
except ImportError:
    import warnings
    warnings.warn("No Installation of PySide6 found falling back to PyQt5")
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
    from PyQt5.QtCore import pyqtSignal, Qt

from QNodeEditor import NodeScene, NodeView
from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor.node import Node

# Set scaling attributes for large screen resolutions
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


class NodeEditor(QWidget):
    """
    Node editor widget containing a node scene and view

    Widget that contains a :py:class:`~QNodeEditor.scene.NodeScene` and a
    :py:class:`~QNodeEditor.graphics.view.NodeView` of that scene. To change the node editor, access
    the :py:attr:`scene` attribute to modify the node scene.

    Attributes
    ----------
    scene : :py:class:`~QNodeEditor.scene.NodeScene`
        Node scene
    view : :py:class:`~QNodeEditor.graphics.view.NodeView`
        View of the node scene
    """

    evaluated: pyqtSignal = pyqtSignal(dict)
    """pyqtSignal -> dict: Signal that emits the evaluation result if successful"""
    errored: pyqtSignal = pyqtSignal(Exception)
    """pyqtSignal -> Exception: Signal that emits the error if evaluation failed"""

    def __init__(self, parent: QWidget = None,
                 theme: ThemeType = DarkTheme,
                 allow_multiple_inputs: bool = False):
        """
        Create a new node editor widget.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget for this node editor (if any)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the node editor (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        allow_multiple_inputs : bool
            If set to True, multiple edges can be connected to the same node input. Otherwise, only
            a single edge can be connected to any input.
        """
        super().__init__() # parent=parent

        # Create widget layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Create node scene and view
        self.scene: NodeScene = NodeScene(self)
        self.view: NodeView = NodeView(self.scene.graphics,
                                       allow_multiple_inputs=allow_multiple_inputs)
        layout.addWidget(self.view)

        # Set node editor theme
        self.theme: ThemeType = theme
        self.view.setFocusPolicy(Qt.StrongFocus)

        # Pass through scene signals
        self.scene.evaluated.connect(self.evaluated.emit)
        self.scene.errored.connect(self.errored.emit)

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the theme of the node editor.

        Setting the theme of the node editor widget affects all child elements.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self.view.theme = new_theme

    @property
    def available_nodes(self) -> dict[str, Type['Node'] or dict]:
        """
        Get or set the available nodes in the scene.

        This is a (nested) dictionary with pairs of (name, Type[:py:class:`~.node.Node`]). These
        names are displayed in the context menu in the node editor when adding new nodes. The added
        node is then of the type provided in the pair with it. Use a nested dictionary to create
        sub-menus in the context menu.

        See Also
        --------
        :py:attr:`~.scene.NodeScene.available_nodes` : more detailed explanation
        """
        return self.scene.available_nodes

    @available_nodes.setter
    def available_nodes(self, new_available_nodes: dict[str, Type['Node'] or dict]) -> None:
        self.scene.available_nodes = new_available_nodes

    @property
    def output_node(self) -> Type['Node']:
        """
        Get or set the node that should be used as the output node.

        This node will not be evaluated, but is used to create the evaluation result. The preceding
        nodes are evaluated, and the resulting value(s) wired to the output node are recorded and
        emitted through the :py:attr:`evaluated` signal.
        """
        return self.scene.output_node

    @output_node.setter
    @overload
    def output_node(self, code: int) -> None:
        pass

    @output_node.setter
    @overload
    def output_node(self, node_class: Type['Node']) -> None:
        pass

    @output_node.setter
    @overload
    def output_node(self, node: 'Node') -> None:
        pass

    @output_node.setter
    def output_node(self, node: 'Node' or Type['Node'] or int or None) -> None:
        self.scene.output_node = node

    def save(self, filepath: str) -> None:
        """
        Save the node scene state to a file.

        Parameters
        ----------
        filepath : str
            Path to file to save node scene state in

        Returns
        -------
            None
        """
        self.scene.save(filepath)

    def load(self, filepath: str) -> None:
        """
        Load a node scene state from a file

        Parameters
        ----------
        filepath : str
            Path to file to load node scene state from

        Returns
        -------
            None
        """
        self.scene.load(filepath)
