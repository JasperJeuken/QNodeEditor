"""Container storing elements for a node entry"""
# pylint: disable = no-name-in-module
from typing import TYPE_CHECKING, Optional, Any

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal

from QNodeEditor.widgets import EmptyWidget
from QNodeEditor.socket import Socket
from QNodeEditor.themes import ThemeType, DarkTheme
from QNodeEditor.metas import ObjectMeta
from QNodeEditor.util import get_widget_value, NoValue
from QNodeEditor.graphics.entry import EntryGraphics
if TYPE_CHECKING:
    from QNodeEditor.node import Node


class Entry(QObject, metaclass=ObjectMeta):
    """Entry container storing entry layout and sockets"""

    TYPE_STATIC: int = 0
    TYPE_INPUT: int = 1
    TYPE_OUTPUT: int = 2

    # Create entry signals
    edge_connected: pyqtSignal = pyqtSignal()
    edge_disconnected: pyqtSignal = pyqtSignal()
    value_changed: pyqtSignal = pyqtSignal(Any)
    name_changed: pyqtSignal = pyqtSignal(str)
    theme_changed: pyqtSignal = pyqtSignal()
    resized: pyqtSignal = pyqtSignal(float)

    def __init__(self, name: str, entry_type: int = TYPE_STATIC, theme: ThemeType = DarkTheme):
        """
        Create a new entry with the specified type
        :param name: name for this entry (unique in node)
        :param entry_type: type of entry (input, output, or static (default))
        :param theme: theme for the entry
        """
        super().__init__()

        # Add a graphics proxy and an empty entry widget
        self.graphics: EntryGraphics = EntryGraphics(self)
        self._widget = EmptyWidget()

        # Store entry properties
        self._name: str = name
        self._theme: ThemeType = theme
        self.node: Optional['Node'] = None
        self.entry_type: int = entry_type
        self.value: Any = NoValue

        # Add an input or output socket (or no socket for static entries)
        if entry_type in (self.TYPE_INPUT, self.TYPE_OUTPUT):
            self._socket: Socket = Socket(self)
            self._socket.connected.connect(self.edge_connected.emit)
            self._socket.disconnected.connect(self.edge_disconnected.emit)
        else:
            self._socket: None = None

    @property
    def name(self) -> str:
        """
        Get the name of the entry
        :return: str: name of entry
        """
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """
        Set a new name for the entry
        :param new_name: new name for the entry
        :return: None
        """
        self._name = new_name
        self.name_changed.emit(new_name)

    def calculate_value(self) -> Any:
        """
        Calculate the value of this entry (either through its widget or a connected edge)
        :return: Any: value of the entry
        """
        # If this entry is static/output or there are no edges connected, return the widget value
        if self.entry_type in (self.TYPE_STATIC, self.TYPE_OUTPUT) or len(self.socket.edges) == 0:
            return get_widget_value(self.widget)

        # Otherwise, obtain the value from the connected edge
        return self._get_connected_value()

    def _get_connected_value(self) -> Any:
        """
        Get the value of the output entry that is connected to this input entry
        :return: Any: value of connected entry
        """
        # Get the entry that is connected to the input socket
        edge = self.socket.edges[0]
        if edge.start == self.socket:
            connected_entry = edge.end.entry
        else:
            connected_entry = edge.start.entry

        # Get the output from the node the connected entry is in and return the relevant value
        output = connected_entry.node.output
        return output[connected_entry.name]

    @property
    def theme(self) -> ThemeType:
        """
        Get the theme of the entry
        :return: ThemeType: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the entry
        :param new_theme: new entry theme
        :return: None
        """
        self._theme = new_theme
        self.update_padding()

        # Update the widget theme (if it has an attribute) and run custom function
        if hasattr(self.widget, 'theme'):
            self.widget.theme = new_theme

        # Update socket theme (if entry has a socket)
        if self.socket is not None:
            self.socket.graphics.theme = new_theme

        # Send signal for updated theme
        self.theme_changed.emit()

    @property
    def node(self) -> Optional['Node']:
        """
        Get the node this entry is part of (or None if not part of a node)
        :return: Node or None: node this entry is part of (or None)
        """
        return self._node

    @node.setter
    def node(self, new_node: Optional['Node']) -> None:
        """
        Set the node this entry is part of
        :param new_node: new node to set as parent
        :return: None
        """
        # Disconnect any signals from the old scene
        self.disconnect_signal()

        # Set the node
        self._node = new_node

        # Add proxy widget to node
        if new_node is not None:
            self.graphics.setParentItem(new_node.graphics)
            self.node.update_entries()

        # Reconnect signals to the scene
        self.connect_signal()

    @property
    def widget(self) -> QWidget:
        """
        Get the widget that is displayed in this entry
        :return: QWidget: entry widget
        """
        return self._widget

    @widget.setter
    def widget(self, new_widget: QWidget) -> None:
        """
        Set a new widget to display in this entry
        :param new_widget: new entry widget
        :return: None
        """
        # Disconnect any signals from the old widget
        self.disconnect_signal()

        # Make the widget background transparent and set it
        new_widget.setAttribute(Qt.WA_TranslucentBackground)
        self._widget = new_widget

        # Update the padding on the widget and set it as the proxy graphic widget
        self.graphics.setWidget(new_widget)
        self.update_padding()

        # Recenter the socket vertically in the entry
        if self.socket is not None:
            self.socket.graphics.update_position()

        # Update the position of all entries in the node
        if self.node is not None:
            self.node.update_entries()

        # Reconnect editing flag signals to the scene
        self.connect_signal()

    @property
    def socket(self) -> Socket or None:
        """
        Get the socket for this entry (or None if there is none)
        :return: Socket or None: entry socket (or None)
        """
        return self._socket

    @socket.setter
    def socket(self, new_socket: Optional[Socket]) -> None:
        """
        Set a new socket for this entry
        :param new_socket: new entry socket
        :return: None
        """
        # Disconnect edge signals from old socket
        if self.socket is not None:
            try:
                self.socket.connected.disconnect()
            except TypeError:
                pass
            try:
                self.socket.disconnected.disconnect()
            except TypeError:
                pass

        # Set new socket and attach signals
        self._socket = new_socket
        if new_socket is not None:
            self._socket.connected.connect(self.edge_connected.emit)
            self._socket.disconnected.connect(self.edge_disconnected.emit)

    def update_geometry(self) -> None:
        """
        Update the geometry of the entry based on the node settings
        :return: None
        """
        # Set position and width of entry in the node
        pos, width = self.node.graphics.get_entry_geometry(self)
        self.graphics.setPos(pos)
        self.widget.setMaximumWidth(width)
        self.resized.emit(width)

        # Update the position of the entry socket (if it exists)
        if self.socket is not None:
            self.socket.graphics.update_position()
            self.socket.update_edges()

    def update_padding(self) -> None:
        """
        Update the padding for the widget based on the theme
        :return: None
        """
        self.widget.setContentsMargins(self.theme.node_padding[0], 0, self.theme.node_padding[0], 0)

    def disconnect_signal(self) -> None:
        """
        Disconnect editing signal from the scene
        :return: None
        """
        # Disconnect custom widgets with editing signal
        if hasattr(self.widget, 'editing'):
            try:
                self.widget.editing.disconnect()
            except TypeError:
                pass

        # TODO: disconnect PyQt5 widgets

    def connect_signal(self) -> None:
        """
        Connect editing signal to the scene
        :return: None
        """
        # Disconnect signals and ensure node and scene are set
        self.disconnect_signal()
        if self.node is None or self.node.scene is None:
            return

        # Connect custom widgets with editing signal
        if hasattr(self.widget, 'editing'):
            self.widget.editing.connect(self.node.scene.set_editing_flag)

    def remove(self) -> None:
        """
        Remove this entry from the node
        :return: None
        """
        # Disconnect any edges connected to this entry
        if self.socket is not None:
            self.socket.remove_all_edges()

        if self.node is not None:

            # Remove all graphics for this entry from the scene
            if self.node.scene is not None:
                if self.socket is not None:
                    self.node.scene.graphics.removeItem(self.socket.graphics)
                self.node.scene.graphics.removeItem(self.graphics)

            # Remove the entry from the node
            if self in self.node.entries:
                self.node.entries.remove(self)
                self.node.update_entries()

            self.node = None

    def add_socket(self) -> Socket:
        """
        Add a socket to the entry
        :return: Socket: added socket
        """
        return Socket(self)

    def __str__(self) -> str:
        """
        Get a string representation of the entry
        :return: str: string representation of the entry
        """
        type_names = ['Static', 'Input', 'Output']
        return f"<{type_names[self.entry_type]} entry '{self.name})>"

    def save(self) -> dict:
        """
        Override to save any additional values to the entry state
        :return: dict: representation of additional values to save (has to be JSON-safe)
        """
        return {}

    def load(self, state: dict) -> bool:
        """
        Override to load any saved additional values from the entry state (as saved in save())
        :param state: representation of saved additional values to load
        :return: bool: whether setting state succeeded
        """
        return True

    def get_state(self) -> dict:
        """
        Get the state of the entry as a dictionary
        :return: dict: representation of the entry state
        """
        return {
            'socket': None if self.socket is None else self.socket.get_state(),
            'custom': self.save()
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of the entry from a dictionary
        :param state: representation of the entry state
        :param restore_id: whether to restore the object id from state
        :return: bool: whether setting state succeeded
        """
        # Call custom function that could be overloaded by derived classes
        result = self.load(state.get('custom', {}))

        # Set socket state (if entry has a socket)
        if self.socket is not None:
            result &= self.socket.set_state(state.get('socket', {}), restore_id)

        return result
