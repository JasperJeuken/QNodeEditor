"""
Module containing extensions of QGraphicsPathItem representing various edge types.
"""
# pylint: disable = no-name-in-module, C0103
from abc import abstractmethod
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QPoint
from PyQt5.QtGui import QPainter, QPen, QPainterPath

from QNodeEditor.entry import Entry
from QNodeEditor.themes import ThemeType, DarkTheme
from QNodeEditor.metas import GraphicsPathItemMeta
if TYPE_CHECKING:
    from QNodeEditor.edge import Edge


class EdgeGraphics(QGraphicsPathItem, metaclass=GraphicsPathItemMeta):
    """
    Extension of QGraphicsPathItem for drawing an edge.

    This class is abstract. It serves as a base class for various edge types.
    """

    def __init__(self, edge: 'Edge', theme: ThemeType = DarkTheme):
        """
        Create new edge graphics.

        Parameters
        ----------
        edge : :py:class:`~QNodeEditor.edge.Edge`
            Edge these graphics are for
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the edge graphics (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIgnoresParentOpacity)
        self.edge: 'Edge' = edge

        # Create drawing utilities
        self._pen: QPen = QPen()
        self._hovered: bool = False
        self._pos_start: QPointF = QPointF(0, 0)
        self._pos_end: QPointF = QPointF(0, 0)
        self.theme: ThemeType = theme

        # Set item flags
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)

    @property
    def pos_start(self) -> QPointF:
        """
        Get or set the scene starting position of the edge.
        """
        return self._pos_start

    @pos_start.setter
    def pos_start(self, new_start: QPointF or QPoint) -> None:
        # Ensure new start position is QPointF
        if isinstance(new_start, QPoint):
            new_start = QPointF(new_start)
        self._pos_start = new_start
        self.update()

    @property
    def pos_end(self) -> QPointF:
        """
        Get or set the scene ending position of the edge.
        """
        return self._pos_end

    @pos_end.setter
    def pos_end(self, new_end: QPointF or QPoint) -> None:
        # Ensure new end position is QPointF
        if isinstance(new_end, QPoint):
            new_end = QPointF(new_end)
        self._pos_end = new_end
        self.update()

    def hoverEnterEvent(self, _) -> None:
        """
        Update the edge graphics if the mouse is hovered over it.

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, _) -> None:
        """
        Update the edge graphics if the mouse stops hovering over it.

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = False
        self.update()

    def intersects_line(self, point1: QPointF, point2: QPointF) -> bool:
        """
        Checks whether a line segment intersects with this edge.

        Parameters
        ----------
        point1 : QPointF
            Line segment starting point
        point2 : QPointF
            Line segment end point

        Returns
        -------
        bool
            Whether the line segment intersects the edge
        """
        path = QPainterPath(point1)
        path.lineTo(point2)
        return path.intersects(self.create_path())

    def boundingRect(self) -> QRectF:
        """
        Get the bounding rectangle of the edge.

        Returns
        -------
        QRectF
            Edge bounding rectangle

        :meta private:
        """
        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        """
        Get the shape of the edge.

        Returns
        -------
        QRectF
            Edge shape

        :meta private:
        """
        return self.create_path()

    @abstractmethod
    def create_path(self) -> QPainterPath:
        """
        Abstract method that calculates the path of the edge.

        Returns
        -------
        QPainterPath
            Path connecting start and end point
        """

    def paint(self, painter: QPainter, *_) -> None:
        """
        Draw the edge

        Parameters
        ----------
        painter : QPainter
            Painter object to draw with

        Returns
        -------
            None

        :meta private:
        """
        # Calculate edge path
        self.setPath(self.create_path())

        # Set painter style based on edge state
        painter.setBrush(Qt.NoBrush)
        if self.edge.start is None or self.edge.end is None:
            self._pen.setColor(self.theme.edge_color_drag)
            self._pen.setWidthF(self.theme.edge_width_drag)
            self._pen.setStyle(self.theme.edge_style_drag)
        elif self.isSelected():
            self._pen.setColor(self.theme.edge_color_selected)
            self._pen.setWidthF(self.theme.edge_width_selected)
            self._pen.setStyle(self.theme.edge_style_selected)
        elif self._hovered:
            self._pen.setColor(self.theme.edge_color_hover)
            self._pen.setWidthF(self.theme.edge_width_hover)
            self._pen.setStyle(self.theme.edge_style_hover)
        else:
            self._pen.setColor(self.theme.edge_color_default)
            self._pen.setWidthF(self.theme.edge_width_default)
            self._pen.setStyle(self.theme.edge_style_default)
        painter.setPen(self._pen)

        # Draw edge path
        painter.drawPath(self.path())


class DirectEdgeGraphics(EdgeGraphics):
    """
    Edge graphics with  a straight line between the edge start and end point
    """

    def create_path(self) -> QPainterPath:
        """
        Create a straight line between the edge start and end point

        Returns
        -------
        QPainterPath
            Straight line connecting start and end point
        """
        path = QPainterPath(self.pos_start)
        path.lineTo(self.pos_end)
        return path


class BezierEdgeGraphics(EdgeGraphics):
    """
    Edge graphics with a Bézier curve between edge start and end
    """

    def create_path(self) -> QPainterPath:
        """
        Create a Bézier curve between the edge start and end point

        Returns
        -------
        QPainterPath
            Bézier curve connecting start and end point
        """
        # Calculate control point locations
        distance = (self.pos_end.x() - self.pos_start.x()) / 2
        control_x_start = distance
        control_x_end = -distance

        # Correct control points for edges going left
        if self.edge.start is not None:
            start_x, end_x = self.pos_start.x(), self.pos_end.x()
            entry_type = self.edge.start.entry.entry_type
            if ((start_x > end_x and entry_type == Entry.TYPE_OUTPUT) or
                    (start_x < end_x and entry_type == Entry.TYPE_INPUT)):
                control_x_start *= -1
                control_x_end *= -1

        # Create path with cubic
        path = QPainterPath(self.pos_start)
        path.cubicTo(QPointF(self.pos_start.x() + control_x_start, self.pos_start.y()),
                     QPointF(self.pos_end.x() + control_x_end, self.pos_end.y()),
                     self.pos_end)
        return path
