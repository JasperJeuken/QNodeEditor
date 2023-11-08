"""
Module containing a class for an entry with a combo box
"""
from typing import Iterable, Any

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import ComboBox
from QNodeEditor.themes import ThemeType, DarkTheme


class ComboBoxEntry(Entry):
    """
    Entry housing a combo box with a set of items and a name.

    The combo box menu is forced to be displayed on top of other items. The bottom of the drop-down
    menu shows the name of the combo box.

    Examples
    --------
    Example usage:

    .. code-block:: python

        entry = ComboBoxEntry('Some entry', ['Option 1', 'Option 2', 'Option 3'])

        node = MyNode()
        node.add_entry(entry)

    The :py:class:`~QNodeEditor.node.Node` class also contains helper methods to create combo box
    entries:

    .. code-block:: python

        node = MyNode()

        node.add_combo_box_entry('Some entry', {'Option 1': 10, 'Option 2': 5, 'Option 3': 15})

    Note that combo box entries can only be static.
    """
    widget: ComboBox

    def __init__(self, *args, items: Iterable[str] or dict[str, Any] = None,
                 theme: ThemeType = DarkTheme, **kwargs):
        """
        Create a new combo box entry.

        Parameters
        ----------
        items : Iterable[str] or dict[str, Any]
            Items to add to the combo box.

            If ``items`` is an iterable of strings, they will be used as the names of the options,
            and the selected name is returned as the value of the combo box entry.

            If ``items`` is a dictionary, the keys will be used as the names of the options, and the
            values as the data associated with those options. The data associated to the selected
            option is then returned as the value of the combo box entry.
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the entry (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(*args, **kwargs)

        # Add a combo box with the name of the entry
        self.widget: ComboBox = ComboBox(self.name, theme=theme)
        if isinstance(items, dict):
            for text, data in items.items():
                self.widget.addItem(text, data)
        elif items is not None:
            self.widget.addItems(items)

        # Set the entry theme
        self.theme: ThemeType = theme

        # Ensure drop-down popup is drawn on top of everything else
        self.widget.popup_changed.connect(self.set_z_order)

        # Only allow static combo boxes
        if self.entry_type != self.TYPE_STATIC:
            raise ValueError('Combo box entries can only be static')

    def set_z_order(self, popup_visible: bool) -> None:
        """
        Change the z-value of the combo box popup to ensure it is drawn on top..

        Parameters
        ----------
        popup_visible : bool
            Whether the popup is visible

        Returns
        -------
            None
        """
        if popup_visible:
            self.widget.graphicsProxyWidget().setZValue(999)
        else:
            self.widget.graphicsProxyWidget().setZValue(0)

    def save(self) -> dict:
        """
        Save the current index of the combo box in the entry state

        Returns
        -------
        dict
            State of the combo box
        """
        return {
            'index': self.widget.currentIndex()
        }

    def load(self, state: dict) -> bool:
        """
        Load the current combo box index from an entry state

        Parameters
        ----------
        state : dict
            Entry state

        Returns
        -------
        bool
            Whether setting state succeeded
        """
        self.widget.setCurrentIndex(state.get('index', self.widget.currentIndex()))
        return True
