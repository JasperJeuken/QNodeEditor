"""
Module containing extension of QGraphicsProxyWidget representing node entries..
"""
# pylint: disable = no-name-in-module
from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QGraphicsProxyWidget, QGraphicsSceneHoverEvent
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QEnterEvent

from QNodeEditor.widgets.value_box import ValueBox
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
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event: Optional[QGraphicsSceneHoverEvent]) -> None:
        """
        Pass the graphics item hover enter event to the widget.

        Parameters
        ----------
        event : QGraphicsSceneHoverEvent
            Graphics scene hover event

        Returns
        -------
            None

        :meta private:
        """
        widget = self.widget()
        local_pos = widget.mapFromGlobal(event.pos().toPoint())
        screen_pos = event.screenPos()
        window_pos = widget.mapToParent(event.pos().toPoint())
        widget.enterEvent(QEnterEvent(local_pos, window_pos, screen_pos))
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Optional[QGraphicsSceneHoverEvent]) -> None:
        """
        Pass the graphics item hover leave event to the widget.

        Parameters
        ----------
        event : QGraphicsSceneHoverEvent
            Graphics scene hover event

        Returns
        -------
            None

        :meta private:
        """
        widget = self.widget()
        local_pos = widget.mapFromGlobal(event.pos().toPoint())
        screen_pos = event.screenPos()
        window_pos = widget.mapToParent(event.pos().toPoint())
        widget.leaveEvent(QEnterEvent(local_pos, window_pos, screen_pos))
        return super().hoverEnterEvent(event)