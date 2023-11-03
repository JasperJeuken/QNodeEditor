"""Custom combo box for selection inputs"""
# pylint: disable = no-name-in-module, C0103
from PyQt5.QtWidgets import (QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QApplication,
                             QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QModelIndex, QSize, QRect, QEvent, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFontMetrics

from QNodeEditor.themes import ThemeType, DarkTheme


class ComboBox(QComboBox):
    """Widget with a combo box that allows selection of predefined options"""

    popup_changed: pyqtSignal = pyqtSignal(bool)

    def __init__(self, name: str, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Initialise combo box by setting theme
        :param theme: theme to use for this widget
        """
        super().__init__(*args, **kwargs)
        self.name: str = name

        # Set a custom item delegate to allow styling of items
        self.delegate: PopupItemDelegate = PopupItemDelegate(self, theme=theme)
        self.view().setItemDelegate(self.delegate)

        # Change combo box style
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.findChild(QFrame).setWindowFlags(Qt.Popup | Qt.NoDropShadowWindowHint)
        QApplication.setEffectEnabled(Qt.UI_AnimateCombo, False)
        self.theme: ThemeType = theme

        # Listen to popup events
        self.view().setMouseTracking(True)
        self.view().installEventFilter(self)
        self.view().window().installEventFilter(self)

    @property
    def theme(self) -> ThemeType:
        """
        Get the current combo box theme
        :return: ThemeType:
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the combo box
        :param new_theme: new theme
        :return: None
        """
        self._theme = new_theme

        # Create and set stylesheet
        self.setFixedHeight(self.theme.widget_height)
        border_color = self.theme.widget_color_base.name()
        border = f'{round(self.theme.widget_outline_width)}px solid {border_color}'
        style_sheet = f"""
            QComboBox {{
                margin-left: {self.theme.node_padding[0]};
                margin-right: {self.theme.node_padding[0]};
                border: {border};
                border-radius: {round(self.theme.widget_border_radius)}px;
                color: {self.theme.widget_color_text.name()};
                padding-left: 19px;
            }}
            
            QComboBox:hover {{
                color: {self.theme.widget_color_text_hover.name()};
            }}
            
            QComboBox::drop-down {{
                border: none;
                border-top-right-radius: {round(self.theme.widget_border_radius)};
                border-bottom-right-radius: {round(self.theme.widget_border_radius)};
            }}
            
            QComboBox::down-arrow {{
                image: url({self.theme.load_combo_box_arrow()});
                width: 12px;
                height: {round(self.theme.widget_height)}px;
            }}
            
            QComboBox:!editable, QComboBox::drop-down:editable {{
                background: {self.theme.widget_color_base.name()};
            }}
            
            QComboBox:!editable:hover, QComboBox::drop-down:editable:hover {{
                background: {self.theme.widget_color_hovered.name()};
            }}
            
            QComboBox:!editable:on, QComboBox::drop-down:editable:on {{
                background: {self.theme.widget_color_pressed_accent.name()};
            }}
            
            QComboBox QListView {{
                outline: none;
                border: {border};
                background-color: {self.theme.widget_color_active.name()};
            }}
            
            QComboBox QListView::item {{
                border: none;
                padding-left: 15px;
                color: {self.theme.widget_color_text.name()};
                background-color: {self.theme.widget_color_active.name()};
            }}
            
            QComboBox QListView::item:hover {{
                color: {self.theme.widget_color_text_hover.name()};
                background-color: {self.theme.widget_color_pressed_accent.name()};
            }}
        """
        self.setStyleSheet(style_sheet)
        self.setFont(self.theme.font())

        # Propagate theme to item delegate and list view
        self.delegate.theme = new_theme

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        Detect mouse leaving popup
        :param watched: watched object (popup)
        :param event: event
        :return: bool: whether event should not be handled further
        """
        if event.type() in (QEvent.Leave, QEvent.GraphicsSceneHoverLeave):
            self.hidePopup()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def showPopup(self) -> None:
        """
        Intercept popup open to emit popup change signal
        :return: None
        """
        super().showPopup()
        self.popup_changed.emit(True)

    def hidePopup(self) -> None:
        """
        Intercept popup close to emit popup change signal
        :return: None
        """
        super().hidePopup()
        self.popup_changed.emit(False)


class PopupItemDelegate(QStyledItemDelegate):
    """Custom item for use in combo box drop-down popup"""

    def __init__(self, box: ComboBox, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create delegate and set theme
        :param box: box this item delegate is for
        :param theme: item delegate theme
        """
        super().__init__(*args, **kwargs)
        self.box: ComboBox = box
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get the current item theme
        :return: ThemeType: current item theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the item
        :param new_theme: new item theme
        :return: None
        """
        self._theme = new_theme

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Set custom item size
        :param option: style option
        :param index: model index
        :return: None
        """
        default_size = super().sizeHint(option, index)
        default_size.setHeight(self.theme.widget_height)
        return default_size

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the item at the specified index
        :param painter: painter to draw with
        :param option: style options
        :param index: index of item
        :return: None
        """
        super().paint(painter, option, index)

        # Paint the title item after the last item
        if index.row() == self.box.count() - 1:

            # Increase size of frame by one slot to account for title item
            frame: QFrame = self.box.view().window()
            new_height = ((self.box.count() + 1) * self.theme.widget_height +
                          round(self.theme.widget_outline_width) * 2)
            frame.setFixedHeight(new_height)

            # Draw separator between items and title
            pen = QPen(self.theme.widget_color_base)
            pen.setWidth(1)
            painter.setPen(pen)
            y = option.rect.y() + self.theme.widget_height
            painter.drawLine(0, y, option.widget.width(), y)

            # Truncate combo box title if too long
            title_rect = QRect(15, option.rect.y() + self.theme.widget_height,
                               option.rect.width() - 15, option.rect.height())
            font_metrics = QFontMetrics(option.font)
            elided_title = font_metrics.elidedText(self.box.name, Qt.ElideRight, title_rect.width())

            # Draw title text
            pen = QPen(self.theme.widget_color_text_disabled)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawText(title_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_title)
