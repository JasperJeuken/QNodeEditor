"""
Module containing class for an entry with a value box
"""
from typing import Type

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import ValueBox
from QNodeEditor.themes import ThemeType, DarkTheme


class ValueBoxEntry(Entry):
    """
    Entry housing a value box with a value and name

    The value box is a number (float or integer) input. The user can drag their mouse to change the
    value, or click on the box to enter a custom input manually. The value box can have a minimum
    and/or maximum value.

    Examples
    --------
    .. code-block:: python

        entry = ValueBoxEntry('Some entry', value=5, minimum=0, maximum=10, value_type=int)

        node = MyNode()
        node.add_entry(entry)

    The :py:class:`~QNodeEditor.node.Node` class also contains helper methods to create value box
    entries:

    .. code-block:: python

        node = MyNode()

        node.add_value_entry('Some entry', Entry.TYPE_INPUT, value=5)
        node.add_value_input('Some input', value=10.0, minimum=0.0)
        node.add_value_output('Some output', value=15)

    Note that the default value type is ``int``.
    """
    widget: ValueBox  # set widget type for type hints

    def __init__(self,
                 name: str,
                 entry_type: int = Entry.TYPE_INPUT,
                 value: int or float = 0,
                 minimum: int or float = -100,
                 maximum: int or float = 100,
                 value_type: Type[int] or Type[float] = float,
                 theme: ThemeType = DarkTheme,
                 **kwargs):
        """
        Create a new value box entry.

        Parameters
        ----------
        name : str
            Name of the entry
        entry_type : int
            The type of the entry (:py:attr:`~QNodeEditor.entry.Entry.TYPE_STATIC`,
            :py:attr:`~QNodeEditor.entry.Entry.TYPE_INPUT`, or
            :py:attr:`~QNodeEditor.entry.Entry.TYPE_OUTPUT`)
        value : int or float
            Initial value of the entry
        minimum : int or float
            Minimum value of the entry
        maximum : int or float
            Maximum value of the entry
        value_type : Type[int] or Type[float]
            Type of value of the entry (``int`` or ``float``)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the entry (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(name, entry_type, **kwargs)

        # Add a value box with the name and value of the entry
        self.widget: ValueBox = ValueBox(self.name, theme=theme)
        self.widget.value_type = ValueBox.TYPE_INT if value_type is int else ValueBox.TYPE_FLOAT
        self.widget.minimum = minimum
        self.widget.maximum = maximum
        self.widget.value = value

        # Set the entry theme
        self.theme: ThemeType = theme

        # Connect edge (dis)connect signals to show/hide the value box
        self.edge_connected.connect(self.check_visible)
        self.edge_disconnected.connect(self.check_visible)

    def check_visible(self) -> None:
        """
        Hide/show the value box depending on input connections.

        If the entry is an input and an edge is connected, hide the value box and only show a label.
        Otherwise, show the value box.

        Returns
        -------
            None
        """
        if (self.entry_type == self.TYPE_INPUT and self.socket is not None and
                len(self.socket.edges) > 0):
            self.widget.set_label_only(True)
        else:
            self.widget.set_label_only(False)

    def save(self) -> dict:
        """
        Save the value, minimum, and maximum of the value box in the entry state.

        Returns
        -------
        dict
            State of the value box
        """
        return {
            'value': self.widget.value,
            'minimum': self.widget.minimum,
            'maximum': self.widget.maximum,
        }

    def load(self, state: dict) -> bool:
        """
        Load the value, minimum, and maximum of the value box from an entry state.

        Parameters
        ----------
        state : dict
            Entry state

        Returns
        -------
        bool
            Whether setting state succeeded
        """
        self.widget.minimum = state.get('minimum', self.widget.minimum)
        self.widget.maximum = state.get('maximum', self.widget.maximum)
        self.widget.value = state.get('value', self.widget.value)
        return True
