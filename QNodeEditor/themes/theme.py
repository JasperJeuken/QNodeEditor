"""Base class for node editor themes"""
# pylint: disable = no-name-in-module, R0801
import os
from typing import Type, Optional
from pkgutil import get_data
from pkg_resources import resource_filename

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QColor, QFontDatabase, QFont


class Theme:
    """Class storing colors, graphical properties, etc..."""

    # Editor properties
    editor_color_region_select: QColor  # Color of region select in node view
    editor_color_background: QColor     # Color of editor background
    editor_color_grid: QColor           # Color of editor grid
    editor_color_cut: QColor            # Color of cutting line
    editor_cut_dash_pattern: list[int]  # Dash pattern for cutting line (length must be even)
    editor_cut_width: float             # Width of cutting line
    font_name: str                      # Path to .tff font file  in ./fonts/
    font_size: int                      # Default point size
    editor_grid_point_size: float       # Size of grid points
    editor_grid_spacing: int            # Spacing of grid points

    # Node properties
    node_color_body: QColor              # Color of node body
    node_color_header: QColor            # Color of node header (behind title)
    node_color_outline_default: QColor   # Color of node outline in default state
    node_color_outline_hovered: QColor   # Color of node outline in hovered state
    node_color_outline_selected: QColor  # Color of node outline in selected state
    node_color_shadow: QColor            # Color of the node shadow
    node_color_title: QColor             # Color of node title text
    node_border_radius: float            # Node body border radius
    node_outline_width: float            # Node outline width
    node_shadow_radius: float            # Node shadow blur radius
    node_shadow_offset: tuple[float]     # Node shadow offset (dx, dy)
    node_padding: tuple[int]             # Node body padding (horizontal, vertical)
    node_entry_spacing: float            # Spacing between node entries

    # Edge properties
    edge_type: str                    # Type of edge ('direct', 'bezier')
    edge_color_default: QColor        # Color of edge in default state
    edge_color_hover: QColor          # Color of edge in hovered state
    edge_color_selected: QColor       # Color of edge in selected state
    edge_color_drag: QColor           # Color of edge in dragged state
    edge_width_default: float         # Width of edge in default state
    edge_width_hover: float           # Width of edge in hovered state
    edge_width_selected: float        # Width of edge in selected state
    edge_width_drag: float            # Width of edge in dragged state
    edge_style_default: Qt.PenStyle   # Style of edge in default state
    edge_style_hover: Qt.PenStyle     # Style of edge in hovered state
    edge_style_selected: Qt.PenStyle  # Style of edge in selected state
    edge_style_drag: Qt.PenStyle      # Style of edge in dragged state

    # Widget properties
    widget_combo_box_arrow_name: str     # File name of SVG to use for combo box arrow in ./img/
    widget_color_base: QColor            # Color of widget in default state
    widget_color_hovered: QColor         # Primary color of widget in hovered state
    widget_color_hovered_accent: QColor  # Secondary color of widget in hovered state
    widget_color_pressed: QColor         # Primary color of widget in pressed state
    widget_color_pressed_accent: QColor  # Secondary color of widget in pressed state
    widget_color_active: QColor          # Color of active part of widget (such as progress bar)
    widget_color_text: QColor            # Color of widget text in default state
    widget_color_text_hover: QColor      # Color of widget text in hovered state
    widget_color_text_disabled: QColor   # Color of widget text in disabled state
    widget_border_radius: float          # Widget border radius
    widget_outline_width: float          # Widget outline width
    widget_height: int                   # Widget height

    # Socket properties
    socket_color_fill: QColor     # Socket fill color
    socket_color_outline: QColor  # Socket outline color
    socket_radius: int            # Socket radius
    socket_outline_width: float   # Socket outline width

    @classmethod
    def as_hex(cls, color: QColor) -> str:
        """
        Get the RGB hexadecimal representation of a Qt color
        :param color: color to convert to hexadecimal
        :return: str: hexadecimal RGB color string ('#RRGGBB')
        """
        return color.name(QColor.HexRgb)

    @classmethod
    def as_rgb(cls, color: QColor) -> tuple[int, int, int]:
        """
        Get the RGB values of a Qt color
        :param color: color to convert to RGB
        :return: tuple[int, int, int]: (r, g, b) values with range 0-255
        """
        return color.red(), color.green(), color.blue()

    @classmethod
    def font(cls, point_size: Optional[int] = None) -> QFont:
        """
        Load the specified font from /fonts
        :param point_size: point size of return font (or default font size if not specified)
        :return: QFont: loaded font
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
        Load an SVG resource as a base64 string
        :return: str: base64 string representation of SVG file
        """
        path = resource_filename(__name__, os.path.join('img', filename))
        return path.replace('\\', '/')

    @classmethod
    def load_combo_box_arrow(cls) -> str:
        """
        Load the SVG to use for the combo box arrow
        :return: str: base64 data string containing combo box arrow SVG
        """
        return cls.load_svg(cls.widget_combo_box_arrow_name)


ThemeType: Type = Type[Theme]
