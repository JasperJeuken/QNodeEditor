"""Class containing dark theme for node editor"""
# pylint: disable = no-name-in-module, R0801
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from QNodeEditor.themes.theme import Theme


class DarkTheme(Theme):
    """Dark theme for node editor"""

    # Editor properties
    editor_color_region_select: QColor = QColor('#222222')
    editor_color_background: QColor = QColor('#262626')
    editor_color_grid: QColor = QColor('#333333')
    editor_color_cut: QColor = QColor('#999999')
    editor_cut_dash_pattern: list[int] = [2, 2]
    editor_cut_width: float = 2.0
    font_name: str = 'DejaVuSans/DejaVuSansCondensed.ttf'
    font_size: int = 10
    editor_grid_point_size: float = 2.0
    editor_grid_spacing: int = 30

    # Node properties
    node_color_body: QColor = QColor('#393939')
    node_color_header: QColor = QColor('#356A3B')
    node_color_outline_default: QColor = QColor('transparent')
    node_color_outline_hovered: QColor = QColor('#191919')
    node_color_outline_selected: QColor = QColor('#9D9D9D')
    node_color_shadow: QColor = QColor('#000000')
    node_color_title: QColor = QColor('#FFFFFF')
    node_border_radius: float = 5.0
    node_outline_width: float = 1.0
    node_shadow_radius: float = 15.0
    node_shadow_offset: tuple[float] = (0, 3)
    node_padding: tuple[int] = (15, 10)
    node_entry_spacing: float = 5.0

    # Edge properties
    edge_type: str = 'bezier'
    edge_color_default: QColor = QColor('#141414')
    edge_color_hover: QColor = QColor('#101010')
    edge_color_selected: QColor = QColor('#9D9D9D')
    edge_color_drag: QColor = QColor('#171717')
    edge_width_default: float = 3.0
    edge_width_hover: float = 4.0
    edge_width_selected: float = 3.0
    edge_width_drag: float = 3.0
    edge_style_default: Qt.PenStyle = Qt.SolidLine
    edge_style_hover: Qt.PenStyle = Qt.SolidLine
    edge_style_selected: Qt.PenStyle = Qt.SolidLine
    edge_style_drag: Qt.PenStyle = Qt.DashLine

    # Widget properties
    widget_combo_box_arrow_name: str = 'arrow_light.svg'
    widget_color_base: QColor = QColor('#4D4D4D')
    widget_color_hovered: QColor = QColor('#6E6E6E')
    widget_color_hovered_accent: QColor = QColor('#5C5C5C')
    widget_color_pressed: QColor = QColor('#5399DF')
    widget_color_pressed_accent: QColor = QColor('#3380CC')
    widget_color_active: QColor = QColor('#333333')
    widget_color_text: QColor = QColor('#DCDCDC')
    widget_color_text_hover: QColor = QColor('#FFFFFF')
    widget_color_text_disabled: QColor = QColor('#888888')
    widget_border_radius: float = 2.0
    widget_outline_width: float = 1.0
    widget_height: int = 22

    # Socket properties
    socket_color_fill: QColor = QColor('#A1A1A1')
    socket_color_outline: QColor = QColor('#616161')
    socket_radius: int = 5
    socket_outline_width: float = 1.0


if __name__ == '__main__':
    DarkTheme.load_combo_box_arrow()
