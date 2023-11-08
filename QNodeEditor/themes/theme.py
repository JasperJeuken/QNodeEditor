"""
Base class for node editor themes

New themes can be created by deriving from this class and giving each property a value (see
:py:class:`~QNodeEditor.themes`).
"""
# pylint: disable = no-name-in-module, R0801
import os
from typing import Type, Optional
from pkgutil import get_data
from pkg_resources import resource_filename

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QColor, QFontDatabase, QFont


class Theme:
    """
    Theme base class storing colors and other graphical properties for the node editor
    """

    # Editor properties
    editor_color_background: QColor
    """QColor: Color of editor background"""
    editor_color_region_select: QColor
    """QColor: Color of region select in node view"""
    editor_color_grid: QColor
    """QColor: Color of editor grid"""
    editor_color_cut: QColor
    """QColor: Color of cutting line"""
    editor_cut_dash_pattern: list[int]
    """list[int]: Dash pattern for cutting length (length must be even)"""
    editor_cut_width: float
    """float: Width of cutting line"""
    font_name: str
    """str: Relative path to .ttf file in ./fonts/ directory"""
    font_size: int
    """int: Default font size"""
    editor_grid_point_size: float
    """float: Size of editor background grid points"""
    editor_grid_spacing: int
    """int: Spacing of editor background grid points"""

    # Node properties
    node_color_body: QColor
    """QColor: Color of node body"""
    node_color_header: QColor
    """QColor: Color of node header (behind title)"""
    node_color_outline_default: QColor
    """QColor: Color of node outline in default state"""
    node_color_outline_hovered: QColor
    """QColor: Color of node outline in hovered state"""
    node_color_outline_selected: QColor
    """QColor: Color of node outline in selected state"""
    node_color_shadow: QColor
    """QColor: Color of node shadow"""
    node_color_title: QColor
    """QColor: Color of node title text"""
    node_border_radius: float
    """float: Node body border radius"""
    node_outline_width: float
    """float: Node outline width"""
    node_shadow_radius: float
    """float: Node shadow blur radius"""
    node_shadow_offset: tuple[float]
    """tuple[float]: Node shadow offset (dx, dy)"""
    node_padding: tuple[int]
    """tuple[int]: Node body padding (horizontal, vertical)"""
    node_entry_spacing: float
    """float: Vertical spacing between node entries"""

    # Edge properties
    edge_type: str
    """str: Type of edge ('direct' or 'bezier')"""
    edge_color_default: QColor
    """QColor: Color of edges in default state"""
    edge_color_hover: QColor
    """QColor: Color of edges in hovered state"""
    edge_color_selected: QColor
    """QColor: Color of edges in selected state"""
    edge_color_drag: QColor
    """QColor: Color of edges that are being dragged"""
    edge_width_default: float
    """float: Width of edges in default state"""
    edge_width_hover: float
    """float: Width of edges in hovered state"""
    edge_width_selected: float
    """float: Width of edges in selected state"""
    edge_width_drag: float
    """float: Width of edges that are being dragged"""
    edge_style_default: Qt.PenStyle
    """Qt.PenStyle: Style of edges in default state"""
    edge_style_hover: Qt.PenStyle
    """Qt.PenStyle: Style of edges in hovered state"""
    edge_style_selected: Qt.PenStyle
    """Qt.PenStyle: Style of edges in selected state"""
    edge_style_drag: Qt.PenStyle
    """Qt.PenStyle: Style of edges that are being dragged"""

    # Widget properties
    widget_combo_box_arrow_name: str
    """str: Filename of SVG to use for combo box arrow in ./img/ directory"""
    widget_color_base: QColor
    """QColor: Color of widget in default state"""
    widget_color_hovered: QColor
    """QColor: Primary color of widget in hovered state"""
    widget_color_hovered_accent: QColor
    """QColor: Secondary color of widget in hovered state"""
    widget_color_pressed: QColor
    """QColor: Primary color of widget in pressed state"""
    widget_color_pressed_accent: QColor
    """QColor: Secondary color of widget in pressed state"""
    widget_color_active: QColor
    """QColor: Color of active part of widget (such as progress bar)"""
    widget_color_text: QColor
    """QColor: Color of widget text in default state"""
    widget_color_text_hover: QColor
    """QColor: Color of widget text in hovered state"""
    widget_color_text_disabled: QColor
    """QColor: Color of widget text in disabled state"""
    widget_border_radius: float
    """float: Widget border radius"""
    widget_outline_width: float
    """float: Widget outline width"""
    widget_height: int
    """int: Widget height"""

    # Socket properties
    socket_color_fill: QColor
    """QColor: Color of socket"""
    socket_color_outline: QColor
    """QColor: Color of socket outline"""
    socket_radius: int
    """int: Socket radius"""
    socket_outline_width: float
    """float: Socket outline width"""

    @classmethod
    def font(cls, point_size: Optional[int] = None) -> QFont:
        """
        Load the specified font from the ./fonts/ directory.

        Parameters
        ----------
        point_size : int, optional
            Font point size. If not specified, the default font size is used.

        Returns
        -------
        QFont
            Loaded font
        """
        # Add application font from resource file
        data = QByteArray(get_data(__name__, f'fonts/{cls.font_name}'))
        font_id = QFontDatabase.addApplicationFontFromData(data)

        # Create a QFont from the font ID
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family)

        # Set point size if specified, or use default size
        if point_size is not None:
            font.setPointSize(point_size)
        else:
            font.setPointSize(cls.font_size)
        return font

    @classmethod
    def load_svg(cls, filename: str) -> str:
        """
        Get the absolute path to an SVG file.

        Needed since filepaths for packages are not always intuitive.

        Parameters
        ----------
        filename : str
            Name of SVG file in ./img/ directory to locate

        Returns
        -------
        str
            Absolute path to SVG file
        """
        path = resource_filename(__name__, os.path.join('img', filename))
        return path.replace('\\', '/')

    @classmethod
    def load_combo_box_arrow(cls) -> str:
        """
        Get the absolute path to the SVG file used for the combo box arrow.

        Returns
        -------
        str
            Absolute path to SVG file
        """
        return cls.load_svg(cls.widget_combo_box_arrow_name)


ThemeType: Type = Type[Theme]
