"""Extension of QGraphicsScene for node editor"""
# pylint: disable = no-name-in-module, C0103
from math import floor, ceil
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsScene, QWidget
from PyQt5.QtCore import QRectF, QPoint
from PyQt5.QtGui import QPainter, QPen

from QNodeEditor.themes import ThemeType, DarkTheme
if TYPE_CHECKING:
    from QNodeEditor import NodeScene


class NodeSceneGraphics(QGraphicsScene):
    """Extension of QGraphicsScene for drawing node scene"""

    def __init__(self, scene: 'NodeScene', parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Initialise the scene and set internal variables
        :param scene: scene object containing all node elements
        :param parent: parent of the scene (passed to QGraphicsScene)
        :param theme: theme for the node scene
        """
        super().__init__(parent)
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene: NodeScene = scene
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get the current theme of the node scene
        :return: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the node scene
        :param new_theme: new theme
        :return: None
        """
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
        Set the size of the scene
        :param width: scene width
        :param height: scene height
        :return: None
        """
        self.setSceneRect(QRectF(-width // 2, -height // 2, width, height))

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw the scene background (grid)
        :param painter: painter object to draw with
        :param rect: rectangle to draw in
        :return: None
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
