"""
Module containing class for an entry with a simple name label
"""
# pylint: disable = no-name-in-module

try:
    from PySide6.QtWidgets import QHBoxLayout, QWidget
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFontMetrics
except ImportError:
    from PyQt5.QtWidgets import QHBoxLayout, QWidget
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFontMetrics

from QNodeEditor.entry import Entry
from QNodeEditor.widgets import Label
from QNodeEditor.themes import ThemeType, DarkTheme


class LabeledEntry(Entry):
    """
    Entry housing a label displaying the name of the entry.

    The entry is left-aligned for static and input entries, but right-aligned for output entries.

    Examples
    --------
    Example usage:

    .. code-block:: python

        entry = LabeledEntry('Some entry')

        node = MyNode()
        node.add_entry(entry)

    The :py:class:`~QNodeEditor.node.Node` class also contains helper methods to create labeled
    entries:

    .. code-block:: python

        node = MyNode()

        node.add_label_entry('Some entry', Entry.TYPE_INPUT)
        node.add_label_input('Some input')
        node.add_label_output('Some output')

    Attributes
    ----------
    label : :py:class:`~QNodeEditor.widgets.label.Label`
        Label widget with custom theming
    """

    def __init__(self, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create a new labeled entry.

        Parameters
        ----------
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the entry (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
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
        Update the label theme when the entry theme changes.

        Returns
        -------
            None
        """
        self.label.theme = self.theme

    def on_name_change(self, name: str) -> None:
        """
        Update the label text when the entry name changes.

        The name is truncated if necessary to fit into the available with.

        Parameters
        ----------
        name : str
            New entry name

        Returns
        -------
            None
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
        Update the label text when the entry width changes (affects truncation).

        Returns
        -------
            None
        """
        self.on_name_change(self.name)
