"""Class containing an entry with a combo box"""
from typing import Iterable, Any

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import ComboBox
from QNodeEditor.themes import ThemeType, DarkTheme


class ComboBoxEntry(Entry):
    """Entry housing a combo box with a set of items and a name"""
    widget: ComboBox

    def __init__(self, *args, items: Iterable[str] or dict[str, Any] = None,
                 theme: ThemeType = DarkTheme, **kwargs):
        """
        Create a combo box with the entry name
        :param items: items to add to the combo box (either only texts or (text, data) pairs)
        :param theme: theme for this entry
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
        Change the z-value of the widget popup to ensure it is drawn on top
        :return: None
        """
        if popup_visible:
            self.widget.graphicsProxyWidget().setZValue(999)
        else:
            self.widget.graphicsProxyWidget().setZValue(0)

    def save(self) -> dict:
        """
        Save the current index of the combo box in the entry state
        :return: dict: combo box state
        """
        return {
            'index': self.widget.currentIndex()
        }

    def load(self, state: dict) -> bool:
        """
        Load the current index of the combo box from the entry state
        :param state: entry state
        :return: whether setting state succeeded
        """
        self.widget.setCurrentIndex(state.get('index', self.widget.currentIndex()))
        return True
