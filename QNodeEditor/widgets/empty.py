"""
Module containing empty QWidget
"""
# pylint: disable = no-name-in-module
try:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtCore import Qt


class EmptyWidget(QWidget):
    """
    Empty, transparent widget with default height (used for spacing).
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new empty widget.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(25)
