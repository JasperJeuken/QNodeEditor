"""Extension of QGraphicsItem representing a socket"""
# pylint: disable = no-name-in-module, C0103
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor.socket import Socket


class SocketGraphics(QGraphicsItem):
    """Extension of QGraphicsItem for drawing a socket"""

    def __init__(self, socket: 'Socket', theme: ThemeType = DarkTheme):
        """
        Initialise by setting properties and creating drawing utilities
        :param socket: socket the graphics are for
        """
        super().__init__(socket.entry.graphics)
        self.socket: Socket = socket
        self.setFlags(QGraphicsItem.ItemIgnoresParentOpacity)

        # Create pen and brush
        self._pen: QPen = QPen()
        self._brush: QBrush = QBrush(QColor(0, 0, 0))
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get the socket theme
        :return: current socket theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new socket theme
        :param new_theme: new socket theme
        :return: None
        """
        self._theme = new_theme

        # Set socket colors and outline
        self._pen.setColor(self.theme.socket_color_outline)
        self._brush.setColor(self.theme.socket_color_fill)
        self._pen.setWidthF(self.theme.socket_outline_width)

    def update_position(self) -> None:
        """
        Update the position of the socket relative to the node entry
        :return: None
        """
        # Determine x-location
        if (self.socket.entry.node is None or
                self.socket.entry.entry_type == self.socket.entry.TYPE_INPUT):
            x = 0.0
        else:
            x = self.socket.entry.node.graphics.width

        # Determine y-location
        y = self.socket.entry.widget.height() / 2
        self.setPos(x, y)

    def get_scene_position(self) -> QPointF:
        """
        Get the position of this socket in scene coordinates
        :return: QPointF: socket position in scene
        """
        return self.pos() + self.socket.entry.graphics.pos() + self.socket.entry.node.graphics.pos()

    def boundingRect(self) -> QRectF:
        """
        Get the bounding box of the socket
        :return: QRectF: bounding box
        """
        return QRectF(
            -1 * (self.theme.socket_radius + self.theme.socket_outline_width),
            -1 * (self.theme.socket_radius + self.theme.socket_outline_width),
            2 * (self.theme.socket_radius + self.theme.socket_outline_width),
            2 * (self.theme.socket_radius + self.theme.socket_outline_width)
        )

    def paint(self, painter: QPainter, *_) -> None:
        """
        Draw the socket
        :param painter: painter object to draw with
        :return: None
        """
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self.theme.socket_radius, -self.theme.socket_radius,
                            2 * self.theme.socket_radius, 2 * self.theme.socket_radius)
