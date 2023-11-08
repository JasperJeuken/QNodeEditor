"""
Module containing extension of QGraphicsProxyWidget representing node entries..
"""
# pylint: disable = no-name-in-module
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsProxyWidget

if TYPE_CHECKING:
    from QNodeEditor.entry import Entry


class EntryGraphics(QGraphicsProxyWidget):
    """
    Extension of QGraphicsItem for drawing a node entry.
    """

    def __init__(self, entry: 'Entry', *args, **kwargs):
        """
        Create new entry graphics.

        Parameters
        ----------
        entry: :py:class:`~QNodeEditor.entry.Entry`
            Entry the graphics are for
        """
        super().__init__(*args, **kwargs)
        self.entry: 'Entry' = entry
