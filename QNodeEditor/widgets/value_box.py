"""Custom value box for number inputs with slide controls and line edit input"""
# pylint: disable = no-name-in-module, C0103
from typing import Optional, Type
from functools import partial

from PyQt5.QtWidgets import (QLineEdit, QWidget, QPushButton, QHBoxLayout, QSizePolicy, QLabel,
                             QApplication, QSpacerItem, QStackedLayout)
from PyQt5.QtCore import QPoint, pyqtSignal, Qt, QObject, QEvent
from PyQt5.QtGui import (QMouseEvent, QIntValidator, QDoubleValidator, QFocusEvent, QKeyEvent,
                         QPalette, QColor, QEnterEvent)

from QNodeEditor.themes import ThemeType, DarkTheme


class PopupLineEdit(QLineEdit):
    """
    Line edit that closes when it loses focus
    """

    closed: pyqtSignal = pyqtSignal()

    def focusOutEvent(self, event: Optional[QFocusEvent]) -> None:
        """
        Close the widget if it loses focus
        :param event: focus event
        :return: None
        """
        self.closed.emit()
        self.close()
        event.accept()

    def keyPressEvent(self, event: Optional[QKeyEvent]) -> None:
        """
        Close the widget if "Enter" or "Escape" is pressed
        :param event: key event
        :return: None
        """
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Return:
            self.closed.emit()
            self.close()
            event.accept()
        super().keyPressEvent(event)


class ValueBox(QWidget):
    """Widget with a numerical value that allows dragging or line edit update"""

    value_changed: pyqtSignal = pyqtSignal(int or float)
    editing: pyqtSignal = pyqtSignal(bool)

    TYPE_INT: int = 0
    TYPE_FLOAT: int = 1

    def __init__(self, name: str = '', value_type: int = TYPE_INT,
                 parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Initialise box
        :param name: value name
        :param value_type: type of the value box (0: integer, 1: float)
        :param parent: parent widget
        :param theme: theme to use for this widget
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setContentsMargins(0, 0, 0, 0)
        self.value_type: int = value_type

        # Set widget font
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        # Set tracking variables for dragging
        self._dragging: bool = False          # whether the user is dragging the value
        self._dragged: bool = False           # whether the value changed since starting drag
        self._press_point: QPoint = QPoint()  # mouse position when drag started

        # Set tracking variables for button style
        self._hovered: QPushButton or None = None  # button that is hovered over (or None)
        self._pressed: QPushButton or None = None  # button that is pressed (or None)

        # Add increase/decrease buttons
        self.buttons: dict[str, QPushButton] = {
            'decrease': QPushButton('<', self),
            'increase': QPushButton('>', self),
            'center': QPushButton(self)
        }
        self.label: QLabel = QLabel(name, self)
        self._showing_buttons: bool = True
        self.theme: ThemeType = theme
        self._add_buttons()

        # Add underlying line edit
        self.field: QLineEdit = QLineEdit(self)
        self._add_field()

        # Initialize class properties and values
        self.name: str = name
        self.minimum: float or int = None
        self.maximum: float or int = None
        self.value: float or int = 0
        self.sensitivity: int = 2

    def _add_buttons(self) -> None:
        """
        Add increase, decrease and center buttons to the widget
        :return: None
        """
        # Create a stacked layout for the widget
        self.setLayout(QStackedLayout())

        # Add first page widget with value box buttons
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.buttons['decrease'])
        layout.addWidget(self.buttons['center'], 1)
        layout.addWidget(self.buttons['increase'])
        widget = QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(widget)

        # Add second page widget with label only
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        widget = QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(widget)

        # Set center button label layout
        layout = QHBoxLayout(self.buttons['center'])
        label1 = QLabel()
        label2 = QLabel()
        layout.addWidget(label1, 1)
        layout.addSpacing(5)
        layout.addWidget(label2)
        layout.setContentsMargins(5, 0, 5, 0)
        self.buttons['center'].setLayout(layout)

        # Set button sizes
        self.buttons['decrease'].setFixedWidth(15)
        self.buttons['increase'].setFixedWidth(15)
        # self.buttons['center'].setMinimumWidth(240)

        # Set button object names
        self.buttons['center'].setObjectName('centerButton')
        self.buttons['decrease'].setObjectName('decreaseButton')
        self.buttons['increase'].setObjectName('increaseButton')

        # Add styles to button
        for button in self.buttons.values():
            button.setFlat(True)
            button.setMouseTracking(True)
            button.installEventFilter(self)
            button.setFont(self.theme.font())
        self._update_button_style()

        # Set style for labels in center button
        for label in [label1, label2]:
            label.setMouseTracking(True)
            label.setFont(self.theme.font())

        # Connect buttons to functions
        self.buttons['decrease'].clicked.connect(self.decrement)
        self.buttons['increase'].clicked.connect(self.increment)
        self.buttons['center'].clicked.connect(self._show_field)

    def _update_button_style(self) -> None:
        """
        Update the button style based on current value and settings
        :return: None
        """
        # Determine button background colors in the case no range is set
        bg_decr, bg_cent, bg_incr = self._get_background_colors()

        # Determine text color
        if self._hovered is None and self._pressed is None:
            text_decr = bg_decr
            text_cent = self.theme.widget_color_text.name()
            text_incr = bg_incr
        else:
            text_decr = self.theme.widget_color_text_hover.name()
            text_cent = self.theme.widget_color_text_hover.name()
            text_incr = self.theme.widget_color_text_hover.name()

        # If increase/decrease buttons are hidden, show progress bar and change border
        if not self._showing_buttons:
            bg_cent = self._create_gradient()
            border_radius = f'{round(self.theme.widget_border_radius)}px'
            if self._pressed is not None:
                border = (f'{round(self.theme.widget_outline_width)}px solid '
                          f'{self.theme.widget_color_base.name()}')
            elif self._hovered is not None:
                border = (f'{round(self.theme.widget_outline_width)}px solid '
                          f'{self.theme.widget_color_hovered_accent.name()}')
            else:
                border = (f'{round(self.theme.widget_outline_width)}px solid '
                          f'{self.theme.widget_color_base.name()}')
        else:
            border = 'none'
            border_radius = '0px'

        # Create style sheet for buttons
        style_sheet = f"""
            #centerButton {{
                border: {border};
                border-radius: {border_radius};
                background-color: {bg_cent};
            }}
            
            #decreaseButton {{
                border-top-left-radius: {round(self.theme.widget_border_radius)}px;
                border-bottom-left-radius: {round(self.theme.widget_border_radius)}px;
                color: {text_decr};
                background-color: {bg_decr};
            }}
            
            #increaseButton {{
                border-top-right-radius: {round(self.theme.widget_border_radius)}px;
                border-bottom-right-radius: {round(self.theme.widget_border_radius)}px;
                color: {text_incr};
                background-color: {bg_incr};
            }}
        """
        for button in self.buttons.values():
            button.setStyleSheet(style_sheet)

        # Create style sheet for label
        style_sheet = f"""
            QLabel {{
                color: {self.theme.widget_color_text.name()};
            }}
        """
        self.label.setStyleSheet(style_sheet)
        self.label.setFont(self.theme.font())

        # Apply QLabel style
        button_layout = self.buttons['center'].layout()
        if button_layout is not None:
            for i in range(button_layout.count()):
                widget = self.buttons['center'].layout().itemAt(i).widget()
                if isinstance(widget, QLabel):
                    widget.setStyleSheet(f'color: {text_cent};')

    def _get_background_colors(self) -> tuple[str, str, str]:
        """
        Get the background color for the center and increase/decrease buttons for the case in which
        the minimum/maximum range is not set (no gradient)
        :return: tuple[str, str, str]: (decrease, center, increase) button colors
        """
        # Determine flat background color
        if self._pressed is not None:
            decr, cent, incr = self._set_colors(self.theme.widget_color_pressed.name(),
                                                self.theme.widget_color_pressed_accent.name(),
                                                self._pressed)
        elif self._hovered is not None:
            decr, cent, incr = self._set_colors(self.theme.widget_color_hovered.name(),
                                                self.theme.widget_color_hovered_accent.name(),
                                                self._hovered)
        else:
            decr, cent, incr = self._set_colors(self.theme.widget_color_base.name(),
                                                self.theme.widget_color_base.name(),
                                                None)
        return decr, cent, incr

    def _set_colors(self, color_main: str, color_side: str,
                    button: QPushButton or None) -> tuple[str, str, str]:
        """
        Assign the main and side colors based on the selected button
        :param color_main: color for specified button
        :param color_side: color for other buttons
        :param button: button to take main color
        :return: tuple[str, str, str]: (decrease, center, increase) button colors
        """
        decrease, center, increase = color_side, color_side, color_side
        if button == self.buttons['decrease']:
            decrease = color_main
        elif button == self.buttons['center']:
            center = color_main
        elif button == self.buttons['increase']:
            increase = color_main
        return decrease, center, increase

    def _create_gradient(self) -> str:
        """
        Create a linear gradient representing the fraction of the current value in the range
        :return: str: linear gradient for style sheet
        """
        # Calculate fraction of value in min-max range
        fraction_start = self._calculate_fraction()
        fraction_end = fraction_start + 0.001

        # Choose color based on current value box state
        if self._dragging or self._pressed is not None:
            color = self.theme.widget_color_pressed_accent.name()
        elif self._hovered is not None:
            color = self.theme.widget_color_hovered_accent.name()
        else:
            color = self.theme.widget_color_base.name()

        # Return gradient
        return (f'qlineargradient(x1:{fraction_start}, y1:0, x2:{fraction_end}, y2:0, '
                f'stop:0 {self.theme.widget_color_active.name()}, stop:1 {color})')

    def _add_field(self) -> None:
        """
        Add underlying text field to the widget
        :return: None
        """
        self.field.setVisible(False)
        self.field.setFocusProxy(self)

        # Set validator based on value type
        if self.value_type == self.TYPE_INT:
            self.field.setValidator(QIntValidator(self))
        elif self.value_type == self.TYPE_FLOAT:
            self.field.setValidator(QDoubleValidator(self))
        else:
            raise TypeError(f'Unknown value type {self.value_type}')

        # Connect value update function
        self.field.textChanged.connect(self._field_changed)
        self.field.installEventFilter(self)

    def enterEvent(self, event: QEnterEvent) -> None:
        """
        Change box style when mouse enters value box
        :param event: mouse enter event
        :return: None
        """
        self._hovered = self._get_hovered(event.globalPos())
        self._update_button_style()

    def leaveEvent(self, _) -> None:
        """
        Change box style when mouse leaves value box
        :return: None
        """
        self._hovered = None
        self._update_button_style()

    def eventFilter(self, obj: Optional[QObject], event: Optional[QEvent]) -> bool:
        """
        Intercept events fired
        :param obj: object associated with event
        :param event: event to handle
        :return: bool: whether the event was handled
        """
        if event.type() == QEvent.MouseButtonPress:
            return self._handle_mouse_press(obj, event)
        if event.type() == QEvent.MouseButtonRelease:
            return self._handle_mouse_release(obj, event)
        if event.type() == QEvent.MouseMove:
            return self._handle_mouse_move(obj, event)
        return False

    def _handle_mouse_press(self, obj: Optional[QObject], event: Optional[QMouseEvent]) -> bool:
        """
        Handle mouse press event
        :param obj: object associated with mouse press
        :param event: mouse press event
        :return: bool: whether the event was handled
        """
        if event.buttons() == Qt.LeftButton:
            self._hovered = self._get_hovered(event.globalPos())
            self._pressed = obj
            self._update_button_style()

            if obj == self.buttons['center']:
                # Start drag and store position of mouse press
                self._dragged = False
                self._dragging = True
                self._press_point = event.pos()

                # Hide the cursor while dragging
                self._update_cursor_shape(True)
                event.accept()
                return True
        return False

    def _handle_mouse_release(self, obj: Optional[QObject], event: Optional[QMouseEvent]) -> bool:
        """
        Handle mouse release event
        :param obj: object associated with mouse release
        :param event: mouse release event
        :return: bool: whether the event was handled
        """
        if event.button() == Qt.LeftButton:
            self._pressed = None
            self._hovered = self._get_hovered(event.globalPos())

            if self._dragging and obj == self.buttons['center']:
                self._dragging = False

                # If the mouse was not dragged, open text field
                if not self._dragged:
                    self._show_field()

                # Set mouse position (if range is set use fraction, press point otherwise)
                if self._showing_buttons:
                    self.cursor().setPos(self.buttons['center'].mapToGlobal(self._press_point))
                else:
                    x = round(self._calculate_fraction() * self._get_width())
                    y = round(self._get_height() / 2)
                    self.cursor().setPos(self.buttons['center'].mapToGlobal(QPoint(x, y)))

                # Update button style and enable cursor
                self._hovered = self._get_hovered(self.cursor().pos())
                self._update_button_style()
                self._update_cursor_shape()
                event.accept()
                return True

            # Update button style and enable cursor
            self._update_button_style()
            self._update_cursor_shape()
        return False

    def _handle_mouse_move(self, obj: Optional[QObject], event: Optional[QMouseEvent]) -> bool:
        """
        Handle mouse move event
        :param obj: object associated with mouse move
        :param event: mouse move event
        :return: bool: whether the event was handled
        """
        self._hovered = self._get_hovered(event.globalPos())
        self._update_button_style()

        if obj == self.buttons['center'] and self._dragging:
            # Calculate new value based on mouse movement and modifier keys
            step = self._get_modified_step()
            delta = (event.pos().x() - self._press_point.x()) / self.sensitivity * step
            new_value = self.value + delta
            if self.value_type == self.TYPE_INT:
                new_value = int(new_value)

            # Update value if it changed
            if new_value != self.value:
                self._dragged = True
                self.value = new_value

                # Set cursor back to mouse press position
                self.cursor().setPos(self.buttons['center'].mapToGlobal(self._press_point))
        event.accept()
        return True

    def _get_modified_step(self) -> int or float:
        """
        Get the step size modified by the event
        :return: int or float: value step size
        """
        # Determine step multiplier
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            multiplier = 0.1
        elif modifiers == Qt.ControlModifier:
            multiplier = 10.0
        else:
            multiplier = 1.0

        # Ensure step is of correct type
        if self.value_type == self.TYPE_INT:
            return int(max(multiplier * self.step, 1))
        if self.value_type == self.TYPE_FLOAT:
            return float(multiplier * self.step)
        raise TypeError(f'Unknown value type {self.value_type}')

    def _calculate_fraction(self) -> float:
        """
        Calculate the fraction the value in the range min-max
        :return: float: fraction of range
        """
        return (self.value - self.minimum) / (self.maximum - self.minimum)

    def _get_hovered(self, mouse_position: QPoint) -> QPushButton or None:
        """
        Get the button that is being hovered over (or None if none hovered)
        :param mouse_position: position of the mouse (global)
        :return: QPushButton or None: hovered button (or None if none hovered)
        """
        decrease, center, increase = self.buttons.values()
        if center.rect().contains(center.mapFromGlobal(mouse_position)):
            return center
        if decrease.rect().contains(decrease.mapFromGlobal(mouse_position)):
            return decrease
        if increase.rect().contains(increase.mapFromGlobal(mouse_position)):
            return increase
        return None

    def increment(self) -> None:
        """
        Increment the value by one step (modified by Shift/Ctrl)
        :return: None
        """
        step = self._get_modified_step()
        self.value = self.value + step

    def decrement(self) -> None:
        """
        Decrement the value by one step (modified by Shift/Ctrl)
        :return: None
        """
        step = self._get_modified_step()
        self.value = self.value - step

    @property
    def name(self) -> str:
        """
        Getter for box name
        :return: str: box name
        """
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """
        Setter for box name
        :param new_name: new box name
        :return: None
        """
        self._name = new_name
        label = self._get_name_label()
        label.setText(new_name)
        self.label.setText(new_name)

    @property
    def minimum(self) -> int or float:
        """
        Getter for box minimum value
        :return: box minimum value
        """
        return self._minimum

    @minimum.setter
    def minimum(self, new_minimum: int or float or None) -> None:
        """
        Setter for box minimum value
        :param new_minimum: new box minimum value
        :return: None
        """
        # Update internal variable
        self._minimum = self._type_check_value(new_minimum)

        # Update value (in case it is now out of range)
        if len(self.field.text()) > 0:
            self.value = self.value

        # Update style
        if hasattr(self, 'maximum') and self.maximum is not None and self.minimum is not None:
            self._set_button_visibility(False)
        else:
            self._set_button_visibility(True)

    @property
    def maximum(self) -> int or float:
        """
        Getter for box maximum value
        :return: box maximum value
        """
        return self._maximum

    @maximum.setter
    def maximum(self, new_maximum: int or float or None) -> None:
        """
        Setter for box maximum value
        :param new_maximum: new box maximum value
        :return: None
        """
        # Update internal variable
        self._maximum = self._type_check_value(new_maximum)

        # Update value (in case it is now out of range)
        if len(self.field.text()) > 0:
            self.value = self.value

        # Update style
        if hasattr(self, 'minimum') and self.minimum is not None and self.maximum is not None:
            self._set_button_visibility(False)
        else:
            self._set_button_visibility(True)

    @property
    def value_type(self) -> int:
        """
        Getter for box value type
        :return: int: value type (0: int, 1: float)
        """
        return self._value_type

    @value_type.setter
    def value_type(self, new_value_type: int or Type) -> None:
        """
        Setter for box value type
        :param new_value_type: new value type (0: int, 1: float, or type itself)
        :return: None
        """
        if new_value_type == int:
            new_value_type = self.TYPE_INT
        elif new_value_type == float:
            new_value_type = self.TYPE_FLOAT
        elif not isinstance(new_value_type, int) or new_value_type < 0 or new_value_type > 1:
            raise TypeError(f'Unknown value type {new_value_type}')

        # Set internal variable
        self._value_type = new_value_type

        # Set step size based on value type
        if new_value_type == self.TYPE_INT:
            self.step = 1
        elif new_value_type == self.TYPE_FLOAT:
            self.step = 0.1
        else:
            raise ValueError(f'Value type {new_value_type} is not known...')

        # Set validator based on value type
        if hasattr(self, 'field'):
            if self.value_type == self.TYPE_INT:
                self.field.setValidator(QIntValidator(self))
            elif self.value_type == self.TYPE_FLOAT:
                self.field.setValidator(QDoubleValidator(self))
            else:
                raise TypeError(f'Unknown value type {self.value_type}')

    def _type_check_value(self, value: int or float or None) -> int or float or None:
        """
        Ensures the provided value is the same as the value box type (or None)
        :param value: value to type check
        :return: int or float or None: value with type corresponding to value box type (or None)
        """
        if value is None:
            return value
        if self.value_type == self.TYPE_INT:
            return int(value)
        if self.value_type == self.TYPE_FLOAT:
            return float(value)
        raise TypeError(f'Value "{value}" not of type (int, float, None)')

    def set_range(self, minimum: int or float, maximum: int or float) -> None:
        """
        Set the minimum and maximum value
        :param minimum: minimum value
        :param maximum: maximum value
        :return: None
        """
        self.minimum = minimum
        self.maximum = maximum

    @property
    def step(self) -> int or float:
        """
        Getter for value step size
        :return: int or float: step size
        """
        return self._step

    @step.setter
    def step(self, new_step: int or float) -> None:
        """
        Setter for value step size
        :param new_step: new step size
        :return: None
        """
        # Ensure step size is of correct type
        if self.value_type == self.TYPE_INT:
            new_step = int(new_step)
        elif self.value_type == self.TYPE_FLOAT:
            new_step = float(new_step)
        else:
            raise TypeError(f'Unknown value type {self.value_type}')

        # Set step size
        self._step = new_step

    @property
    def value(self) -> int or float:
        """
        Getter for the box value
        :return: int or float: box value
        """
        if self.value_type == self.TYPE_INT:
            return int(self.field.text())
        if self.value_type == self.TYPE_FLOAT:
            return float(self.field.text())
        raise TypeError(f'Unknown value type {self.value_type}')

    @value.setter
    def value(self, new_value: int or float) -> None:
        """
        Setter for box value
        :param new_value: new box value
        :return: None
        """
        # Ensure value is in value range
        if self.minimum is not None:
            new_value = max(new_value, self.minimum)
        if self.maximum is not None:
            new_value = min(new_value, self.maximum)

        # Ensure value is of correct type
        if self.value_type == self.TYPE_INT:
            self.field.setText(str(int(new_value)))
        elif self.value_type == self.TYPE_FLOAT:
            new_value = round(float(new_value), 10)
            if len(str(new_value)) < len(f'{new_value:.3f}'):
                self.field.setText(f'{new_value:.3f}')
            else:
                self.field.setText(str(new_value))
        else:
            raise TypeError(f'Unknown value type {self.value_type}')

        # Update button style if displaying progress
        if self.minimum is not None and self.maximum is not None:
            self._update_button_style()

    def set_height(self, height: int) -> None:
        """
        Set the widget height
        :param height: widget height to use
        :return: None
        """
        for button in self.buttons.values():
            button.setFixedHeight(height)
        self.setFixedHeight(height)

    def _set_button_visibility(self, visible: bool) -> None:
        """
        Show/hide the increment/decrement buttons
        :param visible: whether to show buttons
        :return: None
        """
        self.buttons['decrease'].setVisible(visible)
        self.buttons['increase'].setVisible(visible)
        self._showing_buttons = visible

        # Add/remove spacing to/from center button
        center = self.buttons['center']
        item_first = center.layout().itemAt(0)
        item_last = center.layout().itemAt(center.layout().count() - 1)
        if visible and isinstance(item_first, QSpacerItem):
            center.layout().removeItem(item_first)
        if visible and isinstance(item_last, QSpacerItem):
            center.layout().removeItem(item_last)
        if not visible and not isinstance(item_first, QSpacerItem):
            center.layout().insertSpacing(0, 15)
        if not visible and not isinstance(item_last, QSpacerItem):
            center.layout().addSpacing(15)

        # Update button style
        self._update_button_style()
        self._update_cursor_shape()

    def _update_cursor_shape(self, dragging: bool = False) -> None:
        """
        Set the cursor shape for the center button based on the current state
        :param dragging: whether the user is currently dragging
        :return: None
        """
        QApplication.restoreOverrideCursor()
        if dragging:
            QApplication.setOverrideCursor(Qt.BlankCursor)
            self.buttons['center'].setCursor(Qt.BlankCursor)
        elif self._showing_buttons:
            self.buttons['center'].setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.buttons['center'].setCursor(Qt.CursorShape.ArrowCursor)

    def _get_width(self) -> int:
        """
        Calculate the width of the value box (excluding content margins)
        :return: int: value box width
        """
        margins = self.contentsMargins()
        return self.width() - margins.left() - margins.right()

    def _get_height(self) -> int:
        """
        Calculate the height of the value box (excluding content margins)
        :return: int: value box height
        """
        margins = self.contentsMargins()
        return self.height() - margins.top() - margins.bottom()

    def _show_field(self) -> None:
        """
        Show the text field for editing value
        :return: None
        """
        def _update_value(new_text: str):
            try:
                if self.value_type == self.TYPE_INT:
                    self.value = int(new_text)
                elif self.value_type == self.TYPE_FLOAT:
                    self.value = float(new_text)
                else:
                    raise TypeError(f'Unknown value type {self.value_type}')
            except ValueError:
                pass

        # Create temporary line edit that closes when it loses focus
        temp_field = PopupLineEdit(self)
        temp_field.setText(self.field.text())

        # Set the field size
        margins = self.contentsMargins()
        width = self._get_width()
        height = self._get_height()
        temp_field.setFixedSize(width, height)
        temp_field.move(margins.left(), margins.top())

        # Set validator to only accept number inputs
        limits = {}
        if self.minimum is not None:
            limits['bottom'] = self.minimum
        if self.maximum is not None:
            limits['top'] = self.maximum
        if self.value_type == self.TYPE_INT:
            temp_field.setValidator(QIntValidator(**limits))
        else:
            temp_field.setValidator(QDoubleValidator(**limits))

        # Set field style
        temp_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme.widget_color_pressed_accent.name()};
                border: {round(self.theme.widget_border_radius)}px solid 
                {self.theme.widget_color_pressed_accent.name()};
                color: {self.theme.widget_color_text_hover.name()};
                padding: {self.theme.node_padding[0]};
            }}
        """)
        palette = temp_field.palette()
        palette.setColor(QPalette.Highlight, QColor(self.theme.widget_color_active.name()))
        temp_field.setPalette(palette)
        font = temp_field.font()
        font.setPointSize(10)
        temp_field.setFont(font)

        # Show the line edit and give it focus
        self.editing.emit(True)
        temp_field.show()
        temp_field.setFocus()
        temp_field.selectAll()

        # Connect signal to process changes
        temp_field.closed.connect(partial(self.editing.emit, False))
        temp_field.textChanged.connect(_update_value)

    def _hide_field(self) -> None:
        """
        Hide underlying text field
        :return: None
        """
        self.field.setVisible(False)

    def _field_visible(self) -> bool:
        """
        Checks whether the underlying text field is visible
        :return: bool: whether field is visible
        """
        return self.field.isVisible()

    def _field_changed(self, new_text: str) -> None:
        """
        Update value label and emit signal on value change
        :param new_text: new value (as string)
        :return: None
        """
        # Get int or float from text based on value type
        if self.value_type == self.TYPE_INT:
            value = int(new_text)
        elif self.value_type == self.TYPE_FLOAT:
            value = float(new_text)
        else:
            raise TypeError(f'Unknown value type {self.value_type}')

        # Emit value change signal
        self.value_changed.emit(value)

        # Set value label in center button
        label = self._get_value_label()
        if self.value_type == self.TYPE_INT:
            label.setText(str(value))
        elif self.value_type == self.TYPE_FLOAT:
            label.setText(f'{value:.3f}')

    def _get_value_label(self) -> QLabel:
        """
        Get the label that displays the value
        :return: QLabel: value display label
        """
        for i in reversed(range(self.buttons['center'].layout().count())):
            widget = self.buttons['center'].layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                return widget
        raise ValueError('Could not find value QLabel')

    def _get_name_label(self) -> QLabel:
        """
        Get the label that displays the name
        :return: QLabel: name display label
        """
        for i in range(self.buttons['center'].layout().count()):
            widget = self.buttons['center'].layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                return widget
        raise ValueError('Could not find name QLabel')

    @property
    def theme(self) -> ThemeType:
        """
        Gets the current theme
        :return: ThemeType: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme
        :param new_theme: new theme
        :return: None
        """
        self._theme = new_theme
        self.set_height(new_theme.widget_height)
        self._update_button_style()

    def set_label_only(self, label_only: bool) -> None:
        """
        Hide value box buttons and only show name label
        :param label_only: whether to only show name label
        :return: None
        """
        layout: QStackedLayout = self.layout()
        if label_only:
            layout.setCurrentIndex(1)
        else:
            layout.setCurrentIndex(0)
