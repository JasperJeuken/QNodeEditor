"""
Module containing custom line edit for text input
"""
from typing import Optional

try:
    from PySide6.QtWidgets import (QLineEdit, QWidget, QStackedLayout, QLabel, QSizePolicy, QHBoxLayout,
                                   QCompleter)
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFocusEvent, QValidator
except ImportError:
    from PyQt5.QtWidgets import (QLineEdit, QWidget, QStackedLayout, QLabel, QSizePolicy, QHBoxLayout,
                                 QCompleter)
    from PyQt5.QtCore import pyqtSignal, Qt
    from PyQt5.QtGui import QFocusEvent, QValidator

from QNodeEditor.themes import ThemeType, DarkTheme


class LineEdit(QLineEdit):
    """
    Line edit that emits a signal when focus enters/leaves the box.

    This class should not be used directly. It is automatically instantiated in
    a :py:class:`TextBox`.
    """

    focus_changed: pyqtSignal = pyqtSignal(bool)
    """pyqtSignal -> bool: Signal that emits when the focus enters/leaves the line edit"""

    def focusInEvent(self, event: QFocusEvent) -> None:
        """
        Emit that focus has entered the line edit.

        Parameters
        ----------
        event : QFocusEvent
            Focus event

        Returns
        -------
            None
        """
        self.focus_changed.emit(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """
        Emit that focus has left the line edit.

        Parameters
        ----------
        event : QFocusEvent
            Focus event

        Returns
        -------
            None
        """
        self.focus_changed.emit(False)
        super().focusOutEvent(event)


class TextBox(QWidget):
    """
    Widget with a string value that allows for text inputs.

    The text box by default is a line edit. The widget can switch to a label displaying the widget
    name instead (used when an edge is connected to an entry with this widget).
    """

    # Create text box signals
    value_changed: pyqtSignal = pyqtSignal(str)
    """pyqtSignal -> str: Signal that emits the box value if it changed"""
    editing: pyqtSignal = pyqtSignal(bool)
    """pyqtSignal -> bool: Signal that emits when the user starts/stops editing the line edit"""

    def __init__(self, name: str = '', parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create a new text box.

        Parameters
        ----------
        name : str, optional
            Name of the text box
        parent : QWidget, optional
            Parent widget (if any)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the text box (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet('background-color: transparent')
        self.setContentsMargins(0, 0, 0, 0)

        # Create tracking variables
        self._hovered: bool = False
        self._editing: bool = False

        # Create line edit
        self.line_edit: LineEdit = LineEdit(self)
        self.line_edit.focus_changed.connect(self.update_editing_signal)
        self.line_edit.setClearButtonEnabled(True)

        # Create label
        self.label: QLabel = QLabel(name, self)

        # Set properties
        self.name: str = name
        self.theme: ThemeType = theme
        self.show_clear_button: bool = False
        self.completer: Optional[QCompleter] = None
        self.input_mask: str = ''
        self.max_length: int = 32767
        self.validator: Optional[QValidator] = None
        self.value: str = ''

        # Create the widget
        self.create_layout()

    def create_layout(self) -> None:
        """
        Create the layout of the text box with a stacked layout.

        The first page of the stacked layout contains the line edit, the second page contains only
        a label. These can be switched between when an entry is connected to another node.

        Returns
        -------
            None
        """
        # Set widget layout
        self.setLayout(QStackedLayout())

        # Add first page with line edit
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line_edit)
        widget = QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(widget)

        # Add second page with label only
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        widget = QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(widget)

        # Set style for label
        self.label.setStyleSheet('QLabel { background-color: transparent }')
        self.label.setAttribute(Qt.WA_TranslucentBackground, True)

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the text box theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self.setFixedHeight(new_theme.widget_height)
        self.setFont(new_theme.font())
        self.update_style()

    def update_style(self) -> None:
        """
        Update the style of the line edit based on the current properties.

        Returns
        -------
            None
        """
        # Determine colors based on state
        if self._editing:
            bg_color = self.theme.widget_color_pressed.name()
            color = self.theme.widget_color_text_hover.name()
        elif self._hovered:
            bg_color = self.theme.widget_color_hovered.name()
            color = self.theme.widget_color_text_hover.name()
        else:
            bg_color = self.theme.widget_color_base.name()
            color = self.theme.widget_color_text.name()

        # Set line edit style
        style_sheet = f"""
            QLineEdit {{
                border-radius: {self.theme.widget_border_radius};
                background-color: {bg_color};
                color: {color};
                padding-left: {self.theme.node_padding[0]};
            }}
        """
        self.line_edit.setStyleSheet(style_sheet)
        self.line_edit.setFont(self.theme.font())
        self.line_edit.setFixedHeight(self.theme.widget_height)

        # Set label style
        style_sheet = f"""
            QLabel {{
                color: {self.theme.widget_color_text.name()};
            }}
        """
        self.label.setStyleSheet(style_sheet)
        self.label.setFont(self.theme.font())

    @property
    def name(self) -> str:
        """
        Get or set the text box name
        """
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        self.label.setText(new_name)
        self.line_edit.setPlaceholderText(new_name)

    @property
    def value(self) -> str:
        """
        Get or set the current value.
        """
        return self.line_edit.text()

    @value.setter
    def value(self, new_value: str) -> None:
        self.line_edit.setText(new_value[:self.max_length])

    @property
    def show_clear_button(self) -> bool:
        """
        Get or set whether the line edit should show a clear all button when not empty.
        """
        return self._show_clear_button

    @show_clear_button.setter
    def show_clear_button(self, new_value: bool):
        self._show_clear_button = new_value
        self.line_edit.setClearButtonEnabled(new_value)

    @property
    def completer(self) -> Optional[QCompleter]:
        """
        Get or set whether the completer that is used in the QLineEdit
        """
        return self._completer

    @completer.setter
    def completer(self, new_completer: Optional[QCompleter]):
        self._completer = new_completer
        self.line_edit.setCompleter(new_completer)

    @property
    def input_mask(self) -> str:
        """
        Get or set whether the input mask that is used in the QLineEdit
        """
        return self._input_mask

    @input_mask.setter
    def input_mask(self, new_input_mask: str):
        self._input_mask = new_input_mask
        self.line_edit.setInputMask(new_input_mask)

    @property
    def max_length(self) -> int:
        """
        Get or set whether the maximum length that is used in the QLineEdit
        """
        return self._max_length

    @max_length.setter
    def max_length(self, new_max_length: int):
        self._max_length = new_max_length
        self.line_edit.setMaxLength(new_max_length)

    @property
    def validator(self) -> Optional[QValidator]:
        """
        Get or set whether the validator that is used in the QLineEdit
        """
        return self._validator

    @validator.setter
    def validator(self, new_validator: Optional[QValidator]):
        self._validator = new_validator
        self.line_edit.setValidator(new_validator)

    def update_editing_signal(self, has_focus: bool) -> None:
        """
        Update the editing signal of the text box when focus enters/leaves the line edit.

        Parameters
        ----------
        has_focus : bool
            Whether the line edit has focus

        Returns
        -------
            None
        """
        self._editing = has_focus
        self.editing.emit(has_focus)
        self.update_style()

    def set_label_only(self, label_only: bool) -> None:
        """
        Hide/show the text box and hide/show only the label instead.

        Parameters
        ----------
        label_only : bool
            Whether to only show the name label

        Returns
        -------
            None
        """
        layout: QStackedLayout = self.layout()
        if label_only:
            layout.setCurrentIndex(1)
        else:
            layout.setCurrentIndex(0)

    def enterEvent(self, _) -> None:
        """
        Change the line edit style when the mouse hover enters it.

        Returns
        -------
            None
        """
        self._hovered = True
        self.update_style()

    def leaveEvent(self, _) -> None:
        """
        Change the line edit style when the mouse hover leaves it.

        Returns
        -------
            None
        """
        self._hovered = False
        self.update_style()
