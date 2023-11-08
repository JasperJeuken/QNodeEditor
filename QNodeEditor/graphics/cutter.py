"""
Module containing extension of QGraphicsItem for graphics of an edge cutting line..
"""
# pylint: disable = no-name-in-module, C0103
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QPointF, Qt, QRectF, QPoint
from PyQt5.QtGui import QPen, QPainter, QPainterPath, QPolygonF

from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene


class Cutter(QGraphicsItem):
    """
    Extension of QGraphicsItem for a line defined by points to cut edges with.
    """

    def __init__(self, scene: 'NodeScene', parent: QGraphicsItem = None,
                 theme: ThemeType = DarkTheme):
        """
        Create a new cutting line.

        Parameters
        ----------
        scene : :py:class:`~QNodeEditor.scene.NodeScene`
            Scene the cutter should act in
        parent : QGraphicsItem, optional
            Parent item (if any)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the cutting line (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
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
        Reset the cutting line by removing all points

        Parameters
        ----------
        position : QPoint or QPointF, optional
            Point to add after removing all points

        Returns
        -------
            None
        """
        self._points.clear()
        if position is not None:
            self.add_point(position)
        self.update()

    def add_point(self, position: QPoint or QPointF) -> None:
        """
        Add a point to the cutting line

        Parameters
        ----------
        position : QPoint or QPointF
            Scene position to add to cutting line

        Returns
        -------
            None
        """
        self._points.append(QPointF(position))
        self.update()

    def cut(self) -> None:
        """
        Cut the edges that this cutting line intersects with.

        Returns
        -------
            None
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
        Get or set the cutting line theme.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self._pen = QPen(new_theme.editor_color_cut)
        self._pen.setWidthF(new_theme.editor_cut_width)
        self._pen.setDashPattern(new_theme.editor_cut_dash_pattern)

    def boundingRect(self) -> QRectF:
        """
        Get the bounding rectangle of the cutting line.

        Returns
        -------
        QRectF
            Cutting line bounding rectangle

        :meta private:
        """
        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        """
        Get the shape of the cutting line.

        Returns
        -------
        QPainterPath
            Cutting line shape

        :meta private:
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
        Draw the cutting line.

        Parameters
        ----------
        painter : QPainter
            Painter object to draw with

        Returns
        -------
            None

        :meta private:
        """
        # Set drawing properties
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._pen)

        # Draw cutting line as polygon
        polygon = QPolygonF(self._points)
        painter.drawPolyline(polygon)
