"""
Module containing custom value box for number inputs with slide controls and line edit input
"""
# pylint: disable = no-name-in-module, C0103
from typing import Optional, Type
from functools import partial

try:
    from PySide6.QtWidgets import (QLineEdit, QWidget, QPushButton, QHBoxLayout, QSizePolicy, QLabel,
                                   QApplication, QSpacerItem, QStackedLayout)
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtCore import QPoint, Qt, QObject, QEvent
    from PySide6.QtGui import (QMouseEvent, QIntValidator, QDoubleValidator, QFocusEvent, QKeyEvent,
                               QPalette, QColor, QEnterEvent)
except ImportError:
    from PyQt5.QtWidgets import (QLineEdit, QWidget, QPushButton, QHBoxLayout, QSizePolicy, QLabel,
                                 QApplication, QSpacerItem, QStackedLayout)
    from PyQt5.QtCore import QPoint, pyqtSignal, Qt, QObject, QEvent
    from PyQt5.QtGui import (QMouseEvent, QIntValidator, QDoubleValidator, QFocusEvent, QKeyEvent,
                             QPalette, QColor, QEnterEvent)

from QNodeEditor.themes import ThemeType, DarkTheme


class PopupLineEdit(QLineEdit):
    """
    Line edit that closes when it loses focus.

    This class should not be used. It is automatically instantiated in a :py:class:`ValueBox`.
    """

    closed: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the line edit has closed"""

    def focusOutEvent(self, event: Optional[QFocusEvent]) -> None:
        """
        Close the line edit when it loses focus.

        Parameters
        ----------
        event : QFocusEvent or None
            Event with focus out information

        Returns
        -------
            None

        :meta private:
        """
        self.closed.emit()
        self.close()
        event.accept()

    def keyPressEvent(self, event: Optional[QKeyEvent]) -> None:
        """
        Close the line edit if ``Enter`` or ``Escape`` is pressed.

        Parameters
        ----------
        event QKeyEvent or None
            Event with key press information

        Returns
        -------
            None

        :meta private:
        """
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Return:
            self.closed.emit()
            self.close()
            event.accept()
        super().keyPressEvent(event)


class ValueBox(QWidget):
    """
    Widget with a numerical value that allows dragging or line edit updating.

    The value box by default is divided into three sections. The middle section shows the name and
    value of the box, the outer sections are increment/decrement buttons.

    If the user clicks and drags from the center section, the value will increase/decrease if the
    user moves the mouse to the right/left respectively. Holding ``Shift`` will change the value in
    smaller steps, while holding ``Ctrl`` results in larger steps.

    If the user clicks on the value box, a line edit is shown for entering a custom value with the
    keyboard. The line edit closes when it loses focus or ``Enter``/``Return`` is pressed.

    The value box can have a minimum and/or maximum value. If both are set, the increment/decrement
    buttons are hidden and the value box acts as a progress bar, showing at what percentage of the
    range between minimum and maximum the current value is.
    """

    # Create value box signals
    value_changed: pyqtSignal = pyqtSignal(int or float)
    """pyqtSignal -> int or float: Signal that emits the box value if it changed"""
    editing: pyqtSignal = pyqtSignal(bool)
    """pyqtSignal -> bool: Signal that emits when the user starts/stops editing the line edit"""

    # Create value box value types
    TYPE_INT: int = 0
    """int: Attribute indicating this value box holds an integer"""
    TYPE_FLOAT: int = 1
    """int: Attribute indicating this value box holds a float"""

    def __init__(self, name: str = '', value_type: int = TYPE_INT,
                 parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create a new value box.

        Parameters
        ----------
        name : str, optional
            Name of the value box
        value_type : int, optional
            Type of value (:py:attr:`TYPE_INT` or :py:attr:`TYPE_FLOAT`)
        parent : QWidget, optional
            Parent widget (if any)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the value box (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet('background-color: transparent')
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
        Add increase, decrease, and center buttons to the widget.

        Also adds second page with only a label (used when an input socket is connected to an edge).

        Returns
        -------
            None
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

        # Set style for second page label
        self.label.setStyleSheet('QLabel { background-color: transparent }')
        self.label.setAttribute(Qt.WA_TranslucentBackground, True)

        # Connect buttons to functions
        self.buttons['decrease'].clicked.connect(self.decrement)
        self.buttons['increase'].clicked.connect(self.increment)
        self.buttons['center'].clicked.connect(self._show_field)

    def _update_button_style(self) -> None:
        """
        Update the value box style based on the current value and theme.

        Returns
        -------
            None
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
        Get the background colors for the decrease, center, and increase buttons based on the
        value box state.

        Returns
        -------
        tuple[str, str, str]
            Colors of the (decrease, center, increase) buttons
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
        Assign the primary and secondary colors to the decrease, center, and increase buttons based
        on the value box state.

        Parameters
        ----------
        color_main : str
            Color hex code for the primary button
        color_side : str
            Color hex code for the secondary button
        button : QPushButton or None
            Button that should take the primary color

        Returns
        -------
        tuple[str, str, str]
            Colors of the (decrease, center, increase) buttons
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
        Create a linear gradient that represents the percentage in the range between minimum and
        maximum of the current value.

        Returns
        -------
        str
            CSS text for a qlineargradient with the desired gradient
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
        Add the underlying text field for the widget that holds the current value.

        Returns
        -------
            None
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
        Change the box style when the mouse hovers over it.

        Parameters
        ----------
        event : QEnterEvent
            Mouse enter event

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = self._get_hovered(event.globalPos())
        self._update_button_style()

    def leaveEvent(self, _) -> None:
        """
        Change the box style when the mouse stops hovering over it.

        Returns
        -------
            None

        :meta private:
        """
        self._hovered = None
        self._update_button_style()

    def eventFilter(self, obj: Optional[QObject], event: Optional[QEvent]) -> bool:
        """
        Handle mouse button presses and movements.

        Parameters
        ----------
        obj : QObject or None
            Object the event was generated in (in this case: self)
        event : QEvent or None
            Event to be handled

        Returns
        -------
        bool
            Whether event was handled

        :meta private:
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
        Handle mouse button press.

        Parameters
        ----------
        obj : QObject or None
            Object associated with button press
        event : QMouseEvent or None
            Mouse press event

        Returns
        -------
        bool
            Whether the event was handled
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
        Handle mouse button release.

        Parameters
        ----------
        obj : QObject or None
            Object associated with button release
        event : QMouseEvent or None
            Mouse release event

        Returns
        -------
        bool
            Whether the event was handled
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
        Handle mouse movement.

        Parameters
        ----------
        obj : QObject or None
            Object associated with movement
        event : QMouseEvent or None
            Mouse movement event

        Returns
        -------
        bool
            Whether the event was handled
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
        Get the step size of the value changed based on the ``Shift`` or ``Ctrl`` modifier.

        Returns
        -------
        int or float
            Value step size (type depends on value box type)
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
        Calculate the percentage in the range between minimum and maximum of the current value.

        Returns
        -------
        float
            Fraction of range [0,1]
        """
        return (self.value - self.minimum) / (self.maximum - self.minimum)

    def _get_hovered(self, mouse_position: QPoint) -> QPushButton or None:
        """
        Get the button that is being hovered over (if any).

        Parameters
        ----------
        mouse_position : QPoint
            Global mouse position

        Returns
        -------
        QPushButton or None
            Hovered button (or None if no button is hovered)
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
        Increment the value by one step (modified by ``Shift``/``Ctrl``)

        Returns
        -------
            None
        """
        step = self._get_modified_step()
        self.value = self.value + step

    def decrement(self) -> None:
        """
        Decrement the value by one step (modified by ``Shift``/``Ctrl``)

        Returns
        -------
            None
        """
        step = self._get_modified_step()
        self.value = self.value - step

    @property
    def name(self) -> str:
        """
        Get or set the value box name.
        """
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        label = self._get_name_label()
        label.setText(new_name)
        self.label.setText(new_name)

    @property
    def minimum(self) -> int or float:
        """
        Get or set the minimum value of the box.

        If the current value is lower than the new minimum, the value will be set to the new
        minimum.
        """
        return self._minimum

    @minimum.setter
    def minimum(self, new_minimum: int or float or None) -> None:
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
        Get or set the maximum value of the box.

        If the current value is lower than the new maximum, the value will be set to the new
        maximum.
        """
        return self._maximum

    @maximum.setter
    def maximum(self, new_maximum: int or float or None) -> None:
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
        Get or set the type of value in the box (``int`` or ``float``)
        """
        return self._value_type

    @value_type.setter
    def value_type(self, new_value_type: int or Type) -> None:
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
        Modify a value such that it is of the same type as the value box.

        Parameters
        ----------
        value : int or float or None
            Value to type check

        Returns
        -------
        int or float or None
            ``value`` with same type as value box (or None if None was provided as ``value``)
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
        Set the minimum and maximum value of the value box.

        Parameters
        ----------
        minimum : int or float
            New minimum value
        maximum : int or float
            New maximum value

        Returns
        -------
            None
        """
        self.minimum = minimum
        self.maximum = maximum

    @property
    def step(self) -> int or float:
        """
        Get or set the value step size
        """
        return self._step

    @step.setter
    def step(self, new_step: int or float) -> None:
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
        Get or set the current value.

        Provided values will be forced within minimum-maximum range.
        """
        if self.value_type == self.TYPE_INT:
            return int(self.field.text())
        if self.value_type == self.TYPE_FLOAT:
            return float(self.field.text())
        raise TypeError(f'Unknown value type {self.value_type}')

    @value.setter
    def value(self, new_value: int or float) -> None:
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
        Set the fixed height of the value box.

        Parameters
        ----------
        height : int
            Fixed height for the value box

        Returns
        -------
            None
        """
        for button in self.buttons.values():
            button.setFixedHeight(height)
        self.setFixedHeight(height)

    def _set_button_visibility(self, visible: bool) -> None:
        """
        Show/hide the increment/decrement buttons.

        Used to hide buttons when both minimum and maximum are set.

        Parameters
        ----------
        visible : bool
            Whether buttons should be visible

        Returns
        -------
            None
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
        Update the shape of the cursor based on the value box state.

        Parameters
        ----------
        dragging : bool
            Whether the user is dragging the value

        Returns
        -------
            None
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
        Get the width of the value box (excluding content margins)

        Returns
        -------
        int
            Value box width
        """
        margins = self.contentsMargins()
        return self.width() - margins.left() - margins.right()

    def _get_height(self) -> int:
        """
        Get the height of the value box (excluding content margins)

        Returns
        -------
        int
            Value box height
        """
        margins = self.contentsMargins()
        return self.height() - margins.top() - margins.bottom()

    def _show_field(self) -> None:
        """
        Show the popup line edit for entering custom values with the keyboard.

        Returns
        -------
            None
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
                padding-left: {self.theme.node_padding[0]};
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

    def _field_changed(self, new_text: str) -> None:
        """
        Update the value label if the text field changed.

        Parameters
        ----------
        new_text : str
            String containing new value for the box

        Returns
        -------
            None
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
        Get the label that is displaying the value in the center button.

        Returns
        -------
        QLabel
            Value label

        Raises
        ------
        ValueError
            If the label could not be found
        """
        for i in reversed(range(self.buttons['center'].layout().count())):
            widget = self.buttons['center'].layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                return widget
        raise ValueError('Could not find value QLabel')

    def _get_name_label(self) -> QLabel:
        """
        Get the label that is displaying the name in the center button

        Returns
        -------
        QLabel
            Name label

        Raises
        ------
        ValueError
            If the label could not be found
        """
        for i in range(self.buttons['center'].layout().count()):
            widget = self.buttons['center'].layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                return widget
        raise ValueError('Could not find name QLabel')

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the value box theme.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self.set_height(new_theme.widget_height)
        self._update_button_style()

    def set_label_only(self, label_only: bool) -> None:
        """
        Hide/show the value box and hide/show only the name label instead.

        Parameters
        ----------
        label_only : bool
            Whether to only show the name label

        Returns
        -------
            None
        """
        layout: QStackedLayout = self.layout()
        if label_only:
            layout.setCurrentIndex(1)
        else:
            layout.setCurrentIndex(0)
