"""Class containing an entry with a value box"""
from typing import Type

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import ValueBox
from QNodeEditor.themes import ThemeType, DarkTheme


class ValueBoxEntry(Entry):
    """Entry housing a value box with a value and name"""
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
        Create a value box with the entry name and value
        :param name: name for the entry
        :param value: initial value for the box
        :param minimum: minimum value of the box
        :param maximum: maximum value of the box
        :param value_type: value type of the box (TYPE_INT or TYPE_FLOAT)
        :param theme: theme for this entry
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
        Check if the value box should be visible (only when no input edges are connected)
        :return: None
        """
        if (self.entry_type == self.TYPE_INPUT and self.socket is not None and
                len(self.socket.edges) > 0):
            self.widget.set_label_only(True)
        else:
            self.widget.set_label_only(False)

    def save(self) -> dict:
        """
        Save the value and range of the value box in the entry state
        :return: dict: value box state
        """
        return {
            'value': self.widget.value,
            'minimum': self.widget.minimum,
            'maximum': self.widget.maximum,
        }

    def load(self, state: dict) -> bool:
        """
        Load the value and range of the value box from the entry state
        :param state: entry state
        :return: bool: whether setting state succeeded
        """
        self.widget.minimum = state.get('minimum', self.widget.minimum)
        self.widget.maximum = state.get('maximum', self.widget.maximum)
        self.widget.value = state.get('value', self.widget.value)
        return True
