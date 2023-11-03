"""Empty QWidget"""
# pylint: disable = no-name-in-module
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt


class EmptyWidget(QWidget):
    """Empty, transparent widget with default height"""

    def __init__(self, *args, **kwargs):
        """
        Create empty node with transparent background and fixed height
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(25)
