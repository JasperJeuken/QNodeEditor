"""Class containing an entry with a simple name label"""
# pylint: disable = no-name-in-module
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import Label
from QNodeEditor.themes import ThemeType, DarkTheme


class LabeledEntry(Entry):
    """Entry housing a label displaying the name of the entry"""

    def __init__(self, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create label with entry name and add it to the layout
        :param theme: theme for the label
        """
        super().__init__(*args, **kwargs)

        # Create a label with the entry name
        self.label = Label(self.name)
        self.theme: ThemeType = theme

        # Create a container with a layout
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)

        # Add label and stretch before or after depending on entry type
        if self.entry_type == self.TYPE_OUTPUT:
            layout.addStretch()
        layout.addWidget(self.label)
        if self.entry_type == self.TYPE_INPUT:
            layout.addStretch()

        # Set container as entry widget and update name
        self.widget = container

        # Connect signals
        self.theme_changed.connect(self.on_theme_change)
        self.name_changed.connect(self.on_name_change)
        self.resized.connect(self.on_resize)

    def on_theme_change(self) -> None:
        """
        Set the theme of the label
        :return: None
        """
        self.label.theme = self.theme

    def on_name_change(self, name: str) -> None:
        """
        Update the label with the new (truncated) name
        :param name: new name of the entry
        :return: None
        """
        # Truncate the name if it is too long
        font_metrics = QFontMetrics(self.label.font())
        margins = self.widget.contentsMargins()
        available_width = self.widget.maximumWidth() - margins.left() - margins.right()
        elided_name = font_metrics.elidedText(name, Qt.ElideRight, available_width)

        # Set label with the (truncated) name
        self.label.setText(elided_name)

    def on_resize(self, *_) -> None:
        """
        Update the label to determine truncation
        :return: None
        """
        self.on_name_change(self.name)
