"""Extension of QGraphicsItem for graphics of an edge cutting line"""
# pylint: disable = no-name-in-module, C0103
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QPointF, Qt, QRectF, QPoint
from PyQt5.QtGui import QPen, QPainter, QPainterPath, QPolygonF

from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene


class Cutter(QGraphicsItem):
    """Extension of QGraphicsItem for cutting edges with a line"""

    def __init__(self, scene: 'NodeScene', parent: QGraphicsItem = None,
                 theme: ThemeType = DarkTheme):
        """
        Create tracking variables and drawing utilities
        :param scene: node scene this cutting line is active in
        :param parent: parent item
        :param theme: cutting line theme
        """
        super().__init__(parent)
        self.scene: 'NodeScene' = scene

        # Create tracking variables
        self._points: list[QPointF] = []

        # Create drawing utilities
        self._pen: QPen = QPen()
        self.theme: ThemeType = theme

    def reset(self, position: QPoint or QPointF or None = None) -> None:
        """
        Reset the cutting line
        :param position: first scene position to add to reset cutting line (or None)
        :return: None
        """
        self._points.clear()
        if position is not None:
            self.add_point(position)
        self.update()

    def add_point(self, position: QPoint or QPointF) -> None:
        """
        Add a new point to the cutting line
        :param position: scene position to add to cutting line
        :return: None
        """
        self._points.append(QPointF(position))
        self.update()

    def cut(self) -> None:
        """
        Cut the edges that this cutting line crosses
        :return: None
        """
        # Cannot cut anything if there is not at least two points
        if len(self._points) < 2:
            return

        # Loop through combinations of succeeding points
        for i in range(len(self._points) - 1):
            point1, point2 = self._points[i], self._points[i + 1]

            # Cut any edge in the scene that intersects this line segment
            for edge in reversed(self.scene.edges):
                if edge.graphics.intersects_line(point1, point2):
                    edge.remove()

    @property
    def theme(self) -> ThemeType:
        """
        Get the current cutting line theme
        :return: ThemeType: cutting line theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the cutting line
        :param new_theme: new cutting line theme
        :return: None
        """
        self._theme = new_theme
        self._pen = QPen(new_theme.editor_color_cut)
        self._pen.setWidthF(new_theme.editor_cut_width)
        self._pen.setDashPattern(new_theme.editor_cut_dash_pattern)

    def boundingRect(self) -> QRectF:
        """
        Get the bounding rectangle of the cutting line
        :return: QRectF: bounding rectangle
        """
        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        """
        Get a path representing the current cutting line
        :return: QPainterPath: cutting line path
        """
        # If there are at least two points, create a path
        if len(self._points) > 1:
            path = QPainterPath(self._points[0])
            for point in self._points[1:]:
                path.lineTo(point)

        # Otherwise, create a default path
        else:
            path = QPainterPath(QPointF(0, 0))
            path.lineTo(QPointF(1, 1))
        return path

    def paint(self, painter: QPainter, *_) -> None:
        """
        Draw the cutting line
        :param painter: painter object to draw with
        :return: None
        """
        # Set drawing properties
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._pen)

        # Draw cutting line as polygon
        polygon = QPolygonF(self._points)
        painter.drawPolyline(polygon)
