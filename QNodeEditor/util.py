"""Utility functions for node editor"""
# pylint: disable = no-name-in-module
from typing import Any

from PyQt5.QtWidgets import (QWidget, QCheckBox, QCalendarWidget, QColorDialog, QDateEdit,
                             QDateTimeEdit, QTimeEdit, QDial, QDoubleSpinBox, QSpinBox, QComboBox,
                             QFontComboBox, QKeySequenceEdit, QLineEdit, QListWidget,
                             QPlainTextEdit, QRadioButton, QSlider, QTextEdit, QLayout)

from QNodeEditor.widgets import ComboBox, ValueBox, TextBox


def get_widget_value(widget: QWidget) -> Any:
    """
    Get the value of a QWidget
    :param widget: widget to get value of
    :return: Any: widget value (or None for unsupported QWidgets)
    """
    # Custom QNodeEditor widgets
    if isinstance(widget, ValueBox):
        return widget.value
    if isinstance(widget, ComboBox):
        if widget.currentData() is not None:
            return widget.currentData()
        return widget.currentText()
    if isinstance(widget, TextBox):
        return widget.value

    # Default PyQt5 widgets
    if isinstance(widget, QComboBox):
        if widget.currentData() is not None:
            return widget.currentData()
        return widget.currentText()
    if isinstance(widget, QCheckBox):
        return widget.checkState()
    if isinstance(widget, QCalendarWidget):
        return widget.selectedDate()
    if isinstance(widget, QColorDialog):
        return widget.currentColor()
    if isinstance(widget, QDateEdit):
        return widget.date()
    if isinstance(widget, QDateTimeEdit):
        return widget.dateTime()
    if isinstance(widget, QTimeEdit):
        return widget.time()
    if isinstance(widget, QDial):
        return widget.value()
    if isinstance(widget, QDoubleSpinBox):
        return widget.value()
    if isinstance(widget, QSpinBox):
        return widget.value()
    if isinstance(widget, QFontComboBox):
        return widget.currentFont()
    if isinstance(widget, QKeySequenceEdit):
        return widget.keySequence()
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QListWidget):
        return widget.currentItem()
    if isinstance(widget, QPlainTextEdit):
        return widget.toPlainText()
    if isinstance(widget, QRadioButton):
        return widget.isChecked()
    if isinstance(widget, QSlider):
        return widget.value()
    if isinstance(widget, QTextEdit):
        return widget.toPlainText()

    # Check if widget has 'value' attribute
    if hasattr(widget, 'value'):
        return widget.value

    return None


def set_widget_value(widget: QWidget, value: Any) -> None:
    """
    Set the value of a QWidget
    :param widget: widget to set value of
    :param value: new widget value
    :return: None
    :raise: TypeError: for unknown widgets or unsupported value types
    """
    # Custom QNodeEditor widgets
    if isinstance(widget, ValueBox):
        widget.value = value
        return
    if isinstance(widget, ComboBox):
        if isinstance(value, int):
            widget.setCurrentIndex(value)
            return
        if isinstance(value, str):
            widget.setCurrentText(value)
            return
        raise TypeError(f"Could not set value '{value}' for widget '{widget}'")
    if isinstance(widget, TextBox):
        widget.value = value
        return

    # Default PyQt5 widgets
    if isinstance(widget, QComboBox):
        if isinstance(value, int):
            widget.setCurrentIndex(value)
            return
        if isinstance(value, str):
            widget.setCurrentText(value)
            return
        raise TypeError(f"Could not set value '{value}' for widget '{widget}'")
    if isinstance(widget, QCheckBox):
        widget.setCheckState(value)
        return
    if isinstance(widget, QCalendarWidget):
        widget.setSelectedDate(value)
        return
    if isinstance(widget, QColorDialog):
        widget.setCurrentColor(value)
        return
    if isinstance(widget, QDateEdit):
        widget.setDate(value)
        return
    if isinstance(widget, QDateTimeEdit):
        widget.setDateTime(value)
        return
    if isinstance(widget, QTimeEdit):
        widget.setTime(value)
        return
    if isinstance(widget, QDial):
        widget.setValue(value)
        return
    if isinstance(widget, QDoubleSpinBox):
        widget.setValue(value)
        return
    if isinstance(widget, QSpinBox):
        widget.setValue(value)
        return
    if isinstance(widget, QFontComboBox):
        widget.setCurrentFont(value)
        return
    if isinstance(widget, QKeySequenceEdit):
        widget.setKeySequence(value)
        return
    if isinstance(widget, QLineEdit):
        widget.setText(value)
        return
    if isinstance(widget, QListWidget):
        widget.setCurrentItem(value)
        return
    if isinstance(widget, QPlainTextEdit):
        widget.setPlainText(value)
        return
    if isinstance(widget, QRadioButton):
        widget.setChecked(value)
        return
    if isinstance(widget, QSlider):
        widget.setValue(value)
        return
    if isinstance(widget, QTextEdit):
        widget.setText(value)
        return

    # Check if widget has 'value' attribute
    if hasattr(widget, 'value'):
        widget.value = value
        return
    raise TypeError(f"Could not set value '{value}' for widget '{widget}'")


def clear_layout(layout: QLayout) -> None:
    """
    Remove (in-place) all elements from a QLayout
    :param layout: layout to empty
    :return: None
    """
    # Helper function that recursively goes through all layout elements and removes them
    def _delete_items(_layout):
        if _layout is not None:
            while _layout.count():
                item = _layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    _delete_items(item.layout())
    _delete_items(layout)


class NoValue:
    """Empty class used as a null value"""
