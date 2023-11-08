"""
Entry containing widgets and optionally a socket for inputs/outputs.

This module contains a class derived from QObject. The object contains a widget and optionally a
socket, depending on the set entry type.
"""
# pylint: disable = no-name-in-module
from abc import abstractmethod
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
    """
    Entry container holding a widget and an optional socket for input/output.

    This class is abstract and cannot be used by itself. To define entries to use in nodes, inherit
    from this class and override the ``__init__`` method (making sure to call
    ``super().__init__()``) to set the entry properties.

    Examples
    --------
    To define an entry with a QLabel and an input socket:

    .. code-block:: python

            from PyQt5.QtWidgets import QLabel


            class MyEntry(Entry):

                def __init__(self, name):
                    super().__init__(name, Entry.TYPE_INPUT)

                    self.widget = QLabel(name)

    The :py:attr:`widget` property can be set to add a widget to the entry. This can be any widget.
    The widget is constrained in width by the node, but not in height.

    We can connect to signals in the entry to update our widget if required:

    .. code-block:: python
        :emphasize-lines: 3, 5, 6

        def __init__(self, name):
            ...
            self.name_changed.connect(self.handle_name_change)

        def handle_name_change(self, new_name):
            self.widget.setText(new_name)

    The available signals are:

    - :py:attr:`edge_connected`: Emitted when an edge is connected to this entry
    - :py:attr:`edge_disconnected`: Emitted when an edge is disconnected from this entry
    - :py:attr:`name_changed`: Emitted when the name of this entry is changed
    - :py:attr:`theme_changed`: Emitted when the theme of this entry is changed
    - :py:attr:`resized`: Emitted when the entry width is resized

    Attributes
    ----------
    graphics : :py:class:`~.graphics.entry.EntryGraphics`
        Graphics object that is shown in the scene representing this entry
    value : Any
        Output value of this entry (if not set: :py:class:`~.util.NoValue`)
    """

    # Possible types of entry
    TYPE_STATIC: int = 0
    """int: Static entry type with no input or output"""
    TYPE_INPUT: int = 1
    """int: Input entry type with an input socket"""
    TYPE_OUTPUT: int = 2
    """int: Output entry type with an output socket"""

    # Create entry signals
    edge_connected: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when an edge is connected to this entry"""
    edge_disconnected: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when an edge is disconnected from this entry"""
    value_changed: pyqtSignal = pyqtSignal(Any)
    """pyqtSignal -> Any: Signal that emits the new value of the entry widget if it changed"""
    name_changed: pyqtSignal = pyqtSignal(str)
    """pyqtSignal -> str: Signal that emits the new name of then entry if it changed"""
    theme_changed: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the theme of the entry is changed"""
    resized: pyqtSignal = pyqtSignal(float)
    """pyqtSignal -> float: Signal that is emitted when the width of the entry is changed"""

    def __init__(self, name: str, entry_type: int = TYPE_STATIC, theme: ThemeType = DarkTheme):
        """
        Create a new entry.

        Parameters
        ----------
        name : str
            The name for the entry
        entry_type : int
            The type of the entry (:py:attr:`TYPE_STATIC`, :py:attr:`TYPE_INPUT`, or
            :py:attr:`TYPE_OUTPUT`)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the entry (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
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
        Get or set the name of the entry
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
        Calculate the value of this entry.

        There are two cases:

        - If this entry is an input and an edge is connected, evaluate the connected node and take
          its value.
        - Otherwise, use the value of the widget in the entry (None if unable to retrieve value).

        See :py:func:`~.util.get_widget_value` for the supported widgets.

        Returns
        -------
        Any
            Value of this entry
        """
        # If this entry is static/output or there are no edges connected, return the widget value
        if self.entry_type in (self.TYPE_STATIC, self.TYPE_OUTPUT) or len(self.socket.edges) == 0:
            return get_widget_value(self.widget)

        # Otherwise, obtain the value from the connected edge
        return self._get_connected_value()

    def _get_connected_value(self) -> Any:
        """
        Get the value of the output entry that is connected to this input entry.

        Returns
        -------
        Any
            Value of the connected output entry.
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
        Get or set the theme of the entry.

        Setting the theme of the entry affects all child elements.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        # Set the theme and update the entry padding
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
        Get or set the node this entry is part of.
        """
        return self._node

    @node.setter
    def node(self, new_node: Optional['Node']) -> None:
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
        Get or set the widget that is displayed in this entry.

        Setting the widget will automatically attach signals to detect a value change (if possible).
        """
        return self._widget

    @widget.setter
    def widget(self, new_widget: QWidget) -> None:
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
        Get or set the socket for this entry (None if there is no socket)

        Setting the socket will automatically attach signals to detect edge changes.
        """
        return self._socket

    @socket.setter
    def socket(self, new_socket: Optional[Socket]) -> None:
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
        Update the position and width of the entry based on the node settings.

        After this update, update all connected edges in case the socket positions changed.

        Returns
        -------
            None
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
        Update the padding for the entry widget based on the set theme

        Returns
        -------
            None
        """
        self.widget.setContentsMargins(self.theme.node_padding[0], 0, self.theme.node_padding[0], 0)

    def disconnect_signal(self) -> None:
        """
        Disconnect the editing signal from the entry widget.

        Returns
        -------
            None
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
        Connect an editing signal to the entry widget.

        Returns
        -------
            None
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
        Remove this entry from the node it is part of.

        Any edges connected to this entry are also removed.

        Returns
        -------
            None
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
        Create a socket for the entry

        Returns
        -------
        :py:class:`~.socket.Socket`
            Created socket
        """
        return Socket(self)

    def __str__(self) -> str:
        """
        Get a string representation of the entry

        Returns
        -------
        str
            Representation of the entry
        """
        type_names = ['Static', 'Input', 'Output']
        return f"<{type_names[self.entry_type]} entry '{self.name})>"

    def save(self) -> dict:
        """
        Override this method to save any additional values to the entry state.

        The dictionary returned by this function is saved along with the rest of the entry state. It
        is provided back to the :py:meth:`load` method when the node is loaded again.

        Use this method to add any variables to the node state that are needed to restore the entry
        to the desired state when the entry is loaded.

        Returns
        -------
        dict
            Additional values to save (key, value) pairs.

            Must be JSON-safe

        :meta abstract:
        """
        return {}

    def load(self, state: dict) -> bool:
        """
        Override this method to load the saved additional values and restore the entry state.

        The received ``state`` is the same as the dictionary returned by the :py:meth:`save`
        method (an empty dictionary if not overridden).

        Use this method to use the saved values to restore the entry to the desired state.

        Parameters
        ----------
        state : dict
            Saved additional values by :py:meth:`save`

        Returns
        -------
        bool
            Whether the method executed successfully
        """
        return True

    def get_state(self) -> dict:
        """
        Get the state of this entry as a (JSON-safe) dictionary.

        The dictionary contains:

        - ``socket``: state of the entry socket
        - ``custom``: additional values saved through the :py:meth:`save` method

        Returns
        -------
        dict
            JSON-safe dictionary representing entry state
        """
        return {
            'socket': None if self.socket is None else self.socket.get_state(),
            'custom': self.save()
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of this entry from a state dictionary.

        The dictionary contains:

        - ``socket``: state of the entry socket
        - ``custom``: additional values saved through the :py:meth:`save` method

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired entry state
        restore_id : bool
            Whether to restore the internal IDs of the entry sockets (used to reconnect saved edges)

        Returns
        -------
        bool
            Whether setting the entry state succeeded
        """
        # Call custom function that could be overloaded by derived classes
        result = self.load(state.get('custom', {}))

        # Set socket state (if entry has a socket)
        if self.socket is not None:
            result &= self.socket.set_state(state.get('socket', {}), restore_id)

        return result
