"""
Module containing custom combo box for selection inputs
"""
# pylint: disable = no-name-in-module, C0103

try:
    from PySide6.QtWidgets import (QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QApplication,
                                   QFrame, QSizePolicy)
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtCore import Qt, QModelIndex, QSize, QRect, QEvent, QObject
    from PySide6.QtGui import QPainter, QPen, QFontMetrics
except ImportError:
    from PyQt5.QtWidgets import (QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QApplication,
                                 QFrame, QSizePolicy)
    from PyQt5.QtCore import Qt, QModelIndex, QSize, QRect, QEvent, QObject, pyqtSignal
    from PyQt5.QtGui import QPainter, QPen, QFontMetrics

from QNodeEditor.themes import ThemeType, DarkTheme


class ComboBox(QComboBox):
    """
    Widget with a combo box that allows selection of predefined options.

    The combo box has a custom layout showing its name as an unselectable option in the drop-down
    menu.
    """

    popup_changed: pyqtSignal = pyqtSignal(bool)
    """pyqtSignal -> bool: Signal that emits when the drop-down opens (True) or closes (False)"""

    def __init__(self, name: str, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create a new combo box.

        Parameters
        ----------
        name : str
            Name of the combo box
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the combo box (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
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
        Get or set the combo box theme.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
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
        Close the drop-down menu if the mouse leaves the popup.

        Parameters
        ----------
        watched : QObject
            Object whose events are being processed (in this case: self)
        event : QEvent
            Event to handle

        Returns
        -------
        bool
            Whether event should not be handled further

        :meta private:
        """
        if event.type() in (QEvent.Leave, QEvent.GraphicsSceneHoverLeave):
            self.hidePopup()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def showPopup(self) -> None:
        """
        Emit change signal when opening popup.

        Returns
        -------
            None

        :meta private:
        """
        super().showPopup()
        self.popup_changed.emit(True)

    def hidePopup(self) -> None:
        """
        Emit change signal when closing popup.

        Returns
        -------
            None

        :meta private:
        """
        super().hidePopup()
        self.popup_changed.emit(False)


class PopupItemDelegate(QStyledItemDelegate):
    """
    Custom item delegate used in combo box drop-down menu.

    This class should not be used. It is automatically instantiated in a :py:class:`ComboBox`.
    """

    def __init__(self, box: ComboBox, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create new item delegate.

        Parameters
        ----------
        box : :py:class:`ComboBox`
            Combo box this item delegate is for
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the item delegate (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(*args, **kwargs)
        self.box: ComboBox = box
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the item delegate theme.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Enforce strict item height for the item delegate.

        Parameters
        ----------
        option : QStyleOptionViewItem
            Style option for the item
        index : QModelIndex
            Model index of item for which the size hint is requested

        Returns
        -------
        QSize
            Size of the item delegate

        :meta private:
        """
        default_size = super().sizeHint(option, index)
        default_size.setHeight(self.theme.widget_height)
        return default_size

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the item at the specified index.

        Additionally, paint the combo box title below the final item.

        Parameters
        ----------
        painter : QPainter
            Painter object to draw with
        option : QStyleOptionViewItem
            Style option for the item
        index : QModelIndex
            Model index of item to paint

        Returns
        -------
            None

        :meta private:
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
