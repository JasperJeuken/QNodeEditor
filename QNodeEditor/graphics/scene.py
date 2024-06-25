"""
Module containing extension of QGraphicsScene for node editor scenes.
"""
# pylint: disable = no-name-in-module, C0103
from math import floor, ceil
from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import QGraphicsScene, QWidget
    from PySide6.QtCore import QRectF, QPoint
    from PySide6.QtGui import QPainter, QPen
except ImportError:
    from PyQt5.QtWidgets import QGraphicsScene, QWidget
    from PyQt5.QtCore import QRectF, QPoint
    from PyQt5.QtGui import QPainter, QPen

from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor import NodeScene


class NodeSceneGraphics(QGraphicsScene):
    """
    Extension of QGraphicsScene for drawing node scene.
    """

    def __init__(self, scene: 'NodeScene', parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create new node scene graphics.

        Parameters
        ----------
        scene : :py:class:`~QNodeEditor.scene.NodeScene`
            Node scene these graphics are for
        parent : QWidget, optional
            Parent widget (if any)
        theme :  Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the node scene (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(parent)
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene: NodeScene = scene
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the theme of the node scene.

        Setting the theme will affect all child elements.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme

        # Update drawing utilities
        self.setBackgroundBrush(new_theme.editor_color_background)
        self._pen = QPen(new_theme.editor_color_grid)
        self._pen.setWidthF(self.theme.editor_grid_point_size)

        # Propagate changed theme to all nodes
        for node in self.scene.nodes:
            node.graphics.theme = new_theme

        # Propagate changed theme to all edges
        for edge in self.scene.edges:
            edge.theme = new_theme

    def set_size(self, width: int or float, height: int or float) -> None:
        """
        Set the size of the scene.

        Parameters
        ----------
        width : int or float
            Scene width
        height : int or float
            Scene height

        Returns
        -------
            None
        """
        self.setSceneRect(QRectF(-width // 2, -height // 2, width, height))

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw the scene background.

        Parameters
        ----------
        painter : QPainter
            Painter object to draw with
        rect : QRectF
            Rectangle in which to draw the background

        Returns
        -------
            None

        :meta private:
        """
        super().drawBackground(painter, rect)

        # Calculate values for ease of use
        left, right = floor(rect.left()), ceil(rect.right())
        top, bottom = floor(rect.top()), ceil(rect.bottom())

        # Create grid points
        grid_points: list[QPoint] = []
        for x in range(left - (left % self.theme.editor_grid_spacing),
                       right, self.theme.editor_grid_spacing):
            for y in range(top - (top % self.theme.editor_grid_spacing),
                           bottom, self.theme.editor_grid_spacing):
                grid_points.append(QPoint(x, y))

        # Draw grid points
        if len(grid_points) > 0:
            painter.setPen(self._pen)
            painter.drawPoints(grid_points)
