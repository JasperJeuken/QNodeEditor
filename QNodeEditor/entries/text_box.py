"""
Module containing class for an entry with a text box
"""
from typing import Optional

try:
    from PySide6.QtWidgets import QCompleter
    from PySide6.QtGui import QValidator
except ImportError:
    from PyQt5.QtWidgets import QCompleter
    from PyQt5.QtGui import QValidator

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import TextBox
from QNodeEditor.themes import ThemeType, DarkTheme


class TextBoxEntry(Entry):
    """
    Entry housing a text box with a value and name
    
    The text box is a string input. The user can click on the text box to type in text.
    
    Examples
    --------
    .. code-block:: python
        
        entry = TextBoxEntry('Some entry', value='Some text')
        
        node = MyNode()
        node.add_entry(entry)
        
    The :py:class:`~QNodeEditor.node.Node` class also contains helper methods to create text box
    entries.
    """
    widget: TextBox  # set widget type for type hints
    
    def __init__(self,
                 name: str,
                 entry_type: int = Entry.TYPE_INPUT,
                 value: str = '',
                 max_length: int = 32767,
                 show_clear_button: bool = False,
                 input_mask: str = '',
                 completer: Optional[QCompleter] = None,
                 validator: Optional[QValidator] = None,
                 theme: ThemeType = DarkTheme,
                 **kwargs):
        """
        Create a new text box entry.

        Parameters
        ----------
        name : str
            Name of the entry
        entry_type : int
            The type of the entry (:py:attr:`~QNodeEditor.entry.Entry.TYPE_STATIC`,
            :py:attr:`~QNodeEditor.entry.Entry.TYPE_INPUT`, or
            :py:attr:`~QNodeEditor.entry.Entry.TYPE_OUTPUT`)
        value : str
            Initial value of the entry
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the entry (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(name, entry_type, **kwargs)

        # Add a text box with the name and value of the entry
        self.widget: TextBox = TextBox(self.name, theme=theme)
        self.widget.max_length = max_length
        self.widget.show_clear_button = show_clear_button
        self.widget.input_mask = input_mask
        self.widget.completer = completer
        self.widget.validator = validator
        self.widget.value = value

        # Set the entry theme
        self.theme: ThemeType = theme

        # Connect edge (dis)connect signals to show/hide the text box
        self.edge_connected.connect(self.check_visible)
        self.edge_disconnected.connect(self.check_visible)

    def check_visible(self) -> None:
        """
        Hide/show the text box depending on the input connections.

        If the entry is an input and an edge is connected, hide the text box and only show a label.
        Otherwise, show the text box

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
        Save the value of the text box in the entry state.

        Returns
        -------
            State of the text box
        """
        return {'value': self.widget.value}

    def load(self, state: dict) -> bool:
        """
        Load the value of the text box from an entry state.

        Parameters
        ----------
        state : dict
            Entry state

        Returns
        -------
        bool
            Whether setting state succeeded
        """
        self.widget.value = state.get('value', self.widget.value)
        return True
