"""Extension of QGraphicsPathItem representing an edge"""
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
    Extension of QGraphicsPathItem for drawing an edge
    Base class for various edge types
    """

    def __init__(self, edge: 'Edge', theme: ThemeType = DarkTheme):
        """
        Create edge graphics by storing properties and drawing utilities
        :param edge: edge the graphics belong to
        :param theme: theme to use for this edge
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
        Get the start position of the edge
        :return: QPointF: edge start position
        """
        return self._pos_start

    @pos_start.setter
    def pos_start(self, new_start: QPointF or QPoint) -> None:
        """
        Set a new start position for the edge
        :param new_start: new start position
        :return: None
        """
        # Ensure new start position is QPointF
        if isinstance(new_start, QPoint):
            new_start = QPointF(new_start)
        self._pos_start = new_start
        self.update()

    @property
    def pos_end(self) -> QPointF:
        """
        Get the end position of the edge
        :return: QPointF: edge end position
        """
        return self._pos_end

    @pos_end.setter
    def pos_end(self, new_end: QPointF or QPoint) -> None:
        """
        Set a new end position for the edge
        :param new_end: new end position
        :return: None
        """
        # Ensure new end position is QPointF
        if isinstance(new_end, QPoint):
            new_end = QPointF(new_end)
        self._pos_end = new_end
        self.update()

    def hoverEnterEvent(self, _) -> None:
        """
        Detect hover enter and update edge
        :return: None
        """
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, _) -> None:
        """
        Detect hover leave and update edge
        :return: None
        """
        self._hovered = False
        self.update()

    def intersects_line(self, point1: QPointF, point2: QPointF) -> bool:
        """
        Checks whether this edge intersects with a line segment
        :param point1: line segment start point
        :param point2: line segment end point
        :return: bool: whether this edge intersects the line segment
        """
        path = QPainterPath(point1)
        path.lineTo(point2)
        return path.intersects(self.create_path())

    def boundingRect(self) -> QRectF:
        """
        Get the bounding box of the edge
        :return: QRectF: edge bounding box
        """
        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        """
        Get the shape of the edge
        :return: QPainterPath: edge shape
        """
        return self.create_path()

    @abstractmethod
    def create_path(self) -> QPainterPath:
        """
        Abstract method that should create a painter path for the edge
        :return: QPainterPath: path connecting edge start and end
        """

    def paint(self, painter: QPainter, *_) -> None:
        """
        Draw the edge
        :param painter: painter object to draw with
        :return: None
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
    """Edge graphics using a straight line between edge start and end"""

    def create_path(self) -> QPainterPath:
        """
        Create a direct line between edge start and end
        :return: QPainterPath: direct path
        """
        path = QPainterPath(self.pos_start)
        path.lineTo(self.pos_end)
        return path


class BezierEdgeGraphics(EdgeGraphics):
    """Edge graphics using a Bézier curve between edge start and end"""

    def create_path(self) -> QPainterPath:
        """
        Create a Bézier curve between edge start and end
        :return: QPainterPath: Bézier curve path
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
