"""
Module containing extension of QGraphicsItem representing a node.
"""
# pylint: disable = no-name-in-module, C0103
from typing import TYPE_CHECKING, Any

try:
    from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect, QGraphicsTextItem
    from PySide6.QtCore import QRectF, Qt, QPointF
    from PySide6.QtGui import QPainter, QPainterPath, QColor, QBrush, QPen, QFontMetrics
except ImportError:
    from PyQt5.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect, QGraphicsTextItem
    from PyQt5.QtCore import QRectF, Qt, QPointF
    from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush, QPen, QFontMetrics

from QNodeEditor.themes import ThemeType, DarkTheme
from QNodeEditor.graphics.entry import EntryGraphics
from QNodeEditor.graphics.scene import NodeSceneGraphics
if TYPE_CHECKING:
    from QNodeEditor.node import Node
    from QNodeEditor.entry import Entry


class NodeGraphics(QGraphicsItem):
    """
    Extension of QGraphicsItem for drawing a node.
    """

    def __init__(self, node: 'Node', theme: ThemeType = DarkTheme):
        """
        Create new node graphics.

        Parameters
        ----------
        node : :py:class:`~QNodeEditor.node.Node`
            Node these graphics are for
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the node graphics (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__()
        self.node: Node = node

        # Set tracking variables
        self._hovered: bool = False

        # Set node graphical properties
        self.header_height: float = 24.0
        self.width: float = 200
        self.colors: dict[str, QColor] = {
            'body': QColor(57, 57, 57),
            'header': QColor(53, 106, 59),
            'outline_default': QColor(51, 51, 51),
            'outline_hover': QColor(),
            'outline_selected': QColor()
        }

        # Set node interaction properties
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIgnoresParentOpacity |
                      QGraphicsItem.ItemSendsScenePositionChanges | QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        # Add drop shadow
        self.shadow_effect: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect()
        self.theme: ThemeType = theme
        self.shadow_effect.setBlurRadius(self.theme.node_shadow_radius)
        self.shadow_effect.setOffset(*self.theme.node_shadow_offset)
        self.setGraphicsEffect(self.shadow_effect)

        # Add node title
        self._title_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self._title_item.setFont(self.theme.font())
        self._title_item.setDefaultTextColor(self.theme.node_color_title)
        self.set_title(self.node.title)

    @property
    def width(self) -> float:
        """
        Get or set the width of the node.
        """
        return self._width

    @width.setter
    def width(self, new_width: float) -> None:
        self.prepareGeometryChange()
        self._width = new_width

    @property
    def height(self) -> float:
        """
        Get the height of the node.
        """
        height = self.header_height + 2 * self.theme.node_padding[1]
        if len(self.node.entries) > 0:
            for entry in self.node.entries:
                height += entry.graphics.rect().height()
            height += (len(self.node.entries) - 1) * self.theme.node_entry_spacing
        return height

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the theme of the node.

        Setting the theme will apply the theme to all children elements.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self.shadow_effect.setBlurRadius(self.theme.node_shadow_radius)
        self.shadow_effect.setOffset(*self.theme.node_shadow_offset)
        self.shadow_effect.setColor(self.theme.node_color_shadow)
        self.update()

        # Propagate changed theme to all entries
        for entry in self.node.entries:
            entry.theme = new_theme

    def set_title(self, title: str) -> None:
        """
        Change the title of the node.

        The title is automatically truncated if it would exceed the width of the node.

        Parameters
        ----------
        title : str
            New title for the node

        Returns
        -------
            None
        """
        # Set title (truncate if longer than 80% of width)
        font_metrics = QFontMetrics(self._title_item.font())
        elided_text = font_metrics.elidedText(title, Qt.TextElideMode.ElideMiddle,
                                              int(0.9 * self.width))
        self._title_item.setPlainText(elided_text)

        # Center title item in node header
        text_width = self._title_item.boundingRect().width()
        offset = self.width // 2 - text_width // 2
        self._title_item.setPos(offset, 0)

    def get_entry_geometry(self, entry: 'Entry') -> tuple[QPointF, float]:
        """
        Determine the top-left position of an entry relative to the node top-left corner.

        Parameters
        ----------
        entry : :py:class:`~QNodeEditor.entry.Entry`
            Entry to calculate geometry for

        Returns
        -------
        tuple[QPointF, float]
            Top-left position and available width for the given entry.
        """
        # Get the index of the entry in the node entries
        idx = self.node.entries.index(entry)

        # Calculate the y-location
        y = self.header_height + self.theme.node_padding[1] + idx * self.theme.node_entry_spacing
        for i in range(idx):
            y += self.node.entries[i].graphics.rect().height()
        return QPointF(0, y), self.width

    def hoverEnterEvent(self, _) -> None:
        """
        Update the node graphics if the mouse is hovered over it.

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, _) -> None:
        """
        Update the node graphics if the mouse stops hovering over it.

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = False
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange,
                   value: int | QGraphicsItem | EntryGraphics | NodeSceneGraphics) \
            -> int | QGraphicsItem | EntryGraphics | NodeSceneGraphics:
        """
        Update the node and connected edges if it was moved.

        Parameters
        ----------
        change : QGraphicsItemChange
            Change that occurred
        value : QVariant
            New value after change

        Returns
        -------
        QVariant
            Modified value after handling

        :meta private:
        """
        # If the node is moving/was moved, update the edges with the new socket positions
        if change in (QGraphicsItem.ItemPositionChange, QGraphicsItem.ItemTransformChange,
                      QGraphicsItem.ItemPositionHasChanged):
            for socket in self.node.sockets():
                socket.update_edges()

        # Use the default item change event handler
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        """
        Get the bounding rectangle of the node.

        Returns
        -------
        QRectF
            Node bounding rectangle

        :meta private:
        """
        return QRectF(0, 0, self.width, self.height).normalized()

    def paint(self, painter: QPainter, *_) -> None:
        """
        Draw the node.

        Parameters
        ----------
        painter : QPainter
            Painter object to draw with

        Returns
        -------
            None

        :meta private:
        """
        # Create node body (rounded rect below title bar with filled top corners)
        path_body = QPainterPath()
        path_body.setFillRule(Qt.WindingFill)
        path_body.addRoundedRect(QRectF(0, self.header_height, self.width,
                                        self.height - self.header_height),
                                 self.theme.node_border_radius, self.theme.node_border_radius)
        path_body.addRect(QRectF(0, self.header_height,
                                 self.theme.node_border_radius, self.theme.node_border_radius))
        path_body.addRect(QRectF(self.width - self.theme.node_border_radius, self.header_height,
                                 self.theme.node_border_radius, self.theme.node_border_radius))

        # Create node header (rounded rect above body with filled bottom corners)
        path_header = QPainterPath()
        path_header.setFillRule(Qt.WindingFill)
        path_header.addRoundedRect(QRectF(0, 0, self.width, self.header_height),
                                   self.theme.node_border_radius, self.theme.node_border_radius)
        path_header.addRect(QRectF(0, self.header_height - self.theme.node_border_radius,
                                   self.theme.node_border_radius, self.theme.node_border_radius))
        path_header.addRect(QRectF(self.width - self.theme.node_border_radius,
                                   self.header_height - self.theme.node_border_radius,
                                   self.theme.node_border_radius, self.theme.node_border_radius))

        # Create node outline (rounded rectangle around header and body)
        path_outline = QPainterPath()
        path_outline.addRoundedRect(QRectF(0, 0, self.width, self.height),
                                    self.theme.node_border_radius, self.theme.node_border_radius)

        # Create outline pen based on theme
        if self.isSelected():
            pen = QPen(self.theme.node_color_outline_selected)
        elif self._hovered:
            pen = QPen(self.theme.node_color_outline_hovered)
        else:
            pen = QPen(self.theme.node_color_outline_default)
        pen.setWidthF(self.theme.node_outline_width)

        # Draw node body
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.theme.node_color_body))
        painter.drawPath(path_body)

        # Draw node header
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.theme.node_color_header))
        painter.drawPath(path_header)

        # Draw outline
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_outline.simplified())
