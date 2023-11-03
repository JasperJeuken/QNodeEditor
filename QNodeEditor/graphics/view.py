"""Extension of QGraphicsView for node editor"""
# pylint: disable = no-name-in-module, C0103
from typing import Optional, Type
from math import sqrt
from functools import partial

from PyQt5.QtWidgets import QGraphicsView, QGraphicsItem, QMenu, QAction, QFrame
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QMouseEvent, QWheelEvent, QKeyEvent, QCursor

from QNodeEditor.node import Node
from QNodeEditor.edge import Edge
from QNodeEditor.entry import Entry
from QNodeEditor.socket import Socket
from QNodeEditor.graphics.edge import EdgeGraphics
from QNodeEditor.graphics.node import NodeGraphics
from QNodeEditor.graphics.entry import EntryGraphics
from QNodeEditor.graphics.scene import NodeSceneGraphics
from QNodeEditor.graphics.socket import SocketGraphics
from QNodeEditor.graphics.cutter import Cutter
from QNodeEditor.themes import ThemeType, DarkTheme, LightTheme


class NodeView(QGraphicsView):
    """Extension of QGraphicsView for viewing and interacting with a node scene"""

    STATE_DEFAULT: int = 0
    STATE_CUTTING: int = 1
    STATE_DRAGGING: int = 2
    STATE_PLACING: int = 3

    def __init__(self, scene_graphics: NodeSceneGraphics, theme: ThemeType = DarkTheme):
        """
        Initialise graphics view by settings drawing properties and tracking variables
        :param scene_graphics: graphics scene in the view
        :param theme: theme for the node view
        """
        super().__init__(scene_graphics)
        self.scene_graphics: NodeSceneGraphics = scene_graphics

        # Create cutting line
        self._cutter: Cutter = Cutter(self.scene_graphics.scene)
        self.scene_graphics.addItem(self._cutter)

        # Set node view theme and state
        self.theme: ThemeType = theme
        self._state: int = self.STATE_DEFAULT

        # Set graphics rendering properties
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHints(QPainter.Antialiasing | QPainter.HighQualityAntialiasing |
                            QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)

        # Set viewport properties
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)

        # Set zoom tracking variables
        self._zoom_min: int = 5
        self._zoom_max: int = 15
        self._zoom: int = 10
        self._zoom_speed: float = 1.25

        # Set dragging tracking variables
        self._drag_edge: Optional[Edge] = None
        self._drag_start: Optional[Socket] = None
        self._snap_radius: float = 15.0

        # Set placing tracking variables
        self._started_place: bool = False

        # Set other tracking variables
        self.prev_mouse_pos: QPoint = QPoint()
        self._last_left_click: QPoint = QPoint()
        self._last_right_click: QPoint = QPoint()
        self._editing: bool = False

    @property
    def theme(self) -> ThemeType:
        """
        Get the current theme of the node view
        :return: ThemeType: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the node view
        :param new_theme: new theme
        :return: None
        """
        self._theme = new_theme

        # Set a new stylesheet
        style_sheet = f"""
            QGraphicsView {{
                selection-background-color: {new_theme.editor_color_region_select.name()};
            }}
        """
        self.setStyleSheet(style_sheet)

        # Propagate changed theme to scene and cutting line
        self.scene_graphics.theme = new_theme
        self._cutter.theme = new_theme

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Listen for mouse press events
        :param event: mouse event
        :return: None
        """
        # Call custom handler for button presses
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_press(event)
        elif event.button() == Qt.LeftButton:
            self.left_mouse_button_press(event)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button_press(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Listen for mouse release events
        :param event: mouse event
        :return: None
        """
        # Call custom handler for button releases
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_release(event)
        elif event.button() == Qt.LeftButton:
            self.left_mouse_button_release(event)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button_release(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Listen for mouse movement
        :param event: mouse move event
        :return: None
        """
        self.mouse_move(event)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Listen for mouse scroll events
        :param event: mouse scroll event
        :return: None
        """
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Listen for key presses
        :param event: key press event
        :return: None
        """
        # Remove selected items (if content is not being edited)
        if event.key() == Qt.Key_Delete and not self._editing:
            self.remove_selected()
            return event.accept()

        # Handle cut/copy/paste from/to scene
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self.scene_graphics.scene.clipboard.copy()
                return event.accept()
            if event.key() == Qt.Key_X:
                self.scene_graphics.scene.clipboard.cut()
                return event.accept()
            if event.key() == Qt.Key_V:
                self.scene_graphics.scene.clipboard.paste()
                return event.accept()

        # Handle selection duplication
        if event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_D:
            self.duplicate_selection()
            return event.accept()

        # TODO: remove temp theme switching
        if event.key() == Qt.Key_L:
            self.theme = LightTheme
            return event.accept()
        if event.key() == Qt.Key_D:
            self.theme = DarkTheme
            return event.accept()

        # TODO: remove temp evaluate
        if event.key() == Qt.Key_E:
            self.scene_graphics.scene.evaluate()
            return event.accept()

        # Use default handler otherwise
        super().keyPressEvent(event)

    def left_mouse_button_press(self, event: QMouseEvent) -> None:
        """
        Handle left mouse button press
        :param event: mouse press event
        :return: None
        """
        self._last_left_click = self.mapToScene(event.pos())
        clicked_item = self.itemAt(event.pos())

        # Start drag if socket is clicked (and in default mode)
        if self._state == self.STATE_DEFAULT and isinstance(clicked_item, SocketGraphics):
            self.start_drag(clicked_item)
            return event.accept()

        # End drag if user clicks anywhere while dragging (and connect sockets if applicable)
        if self._state == self.STATE_DRAGGING:
            if not isinstance(clicked_item, SocketGraphics):
                socket = self.get_drag_socket(event.pos())
                if socket is not None:
                    clicked_item = socket.graphics
            self.end_drag(clicked_item)
            return event.accept()

        # Start node duplication if user shift+clicks on node
        if (self._state == self.STATE_DEFAULT and event.modifiers() == Qt.ShiftModifier
                and isinstance(clicked_item, NodeGraphics)):
            self._started_place = True
            self.duplicate_node(clicked_item)
            return event.accept()

        # Prevent interaction while placing
        if self._state == self.STATE_PLACING:
            return event.accept()

        # Start cutting edges if user shift+clicks on empty space
        if (self._state == self.STATE_DEFAULT and event.modifiers() == Qt.ShiftModifier
                and clicked_item is None):
            self._cutter.reset(self.mapToScene(event.pos()))
            self._state = self.STATE_CUTTING
            return event.accept()

        # Use default handler otherwise
        super().mousePressEvent(event)

    def right_mouse_button_press(self, event: QMouseEvent) -> None:
        """
        Handle right mouse button press
        :param event: mouse press event
        :return: None
        """
        self.prev_mouse_pos = event.pos()
        self._last_right_click = event.globalPos()

    def middle_mouse_button_press(self, event: QMouseEvent) -> None:
        """
        Handle middle mouse button press
        :param event: mouse press event
        :return: None
        """
        # Use default handler otherwise
        super().mousePressEvent(event)

    def left_mouse_button_release(self, event: QMouseEvent) -> None:
        """
        Handle left mouse button release
        :param event: mouse release event
        :return: None
        """
        released_item = self.itemAt(event.pos())

        # End drag if mouse was moved by enough
        if self._state == self.STATE_DRAGGING and self.mouse_dragged(self.mapToScene(event.pos())):
            if not isinstance(released_item, SocketGraphics):
                socket = self.get_drag_socket(event.pos())
                if socket is not None:
                    released_item = socket.graphics
            self.end_drag(released_item)
            return event.accept()

        # End placement if mouse is released
        if self._state == self.STATE_PLACING:
            if self._started_place:
                self._started_place = False
            else:
                self._state = self.STATE_DEFAULT
            return event.accept()

        # End cutting edges if mouse is released
        if self._state == self.STATE_CUTTING:
            self._cutter.cut()
            self._cutter.reset()
            self._state = self.STATE_DEFAULT
            return event.accept()

        # Use default handler otherwise
        super().mouseReleaseEvent(event)

    def right_mouse_button_release(self, event: QMouseEvent) -> None:
        """
        Handle right mouse button release
        :param event: mouse release event
        :return: None
        """
        # Open context menu if mouse was not dragged
        if (self._state == self.STATE_DEFAULT and
                not self.mouse_dragged(event.globalPos(), Qt.RightButton)):
            self.create_context_menu(event.globalPos())
            return event.accept()

        # End placement by removing node
        if (self._state == self.STATE_PLACING and
                not self.mouse_dragged(event.globalPos(), Qt.RightButton)):
            self.remove_selected()
            self._state = self.STATE_DEFAULT
            return event.accept()

        if self._state == self.STATE_CUTTING:
            return event.accept()

        # Use default handler otherwise
        super().mouseReleaseEvent(event)

    def middle_mouse_button_release(self, event: QMouseEvent) -> None:
        """
        Handle middle mouse button release
        :param event: mouse release event
        :return: None
        """
        # Use default handler otherwise
        super().mouseReleaseEvent(event)

    def mouse_move(self, event: QMouseEvent) -> None:
        """
        Handle mouse movement
        :param event: mouse move event
        :return: None
        """
        # Calculate mouse position change
        offset = self.prev_mouse_pos - event.pos()
        self.prev_mouse_pos = event.pos()

        # Move scene with right-click + drag
        if event.buttons() == Qt.RightButton or (self._state == self.STATE_CUTTING and
                                                 event.buttons() == Qt.RightButton | Qt.LeftButton):
            dx, dy = offset.x(), offset.y()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() + dx))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() + dy))

        # Set dragged edge end position to mouse position
        if self._state == self.STATE_DRAGGING:
            if self._drag_edge.graphics is None:
                self._state = self.STATE_DEFAULT
            else:
                pos = self.calculate_drag_pos(event.pos())
                self._drag_edge.graphics.pos_end = pos

        # Set placed node position to mouse position
        if self._state == self.STATE_PLACING:
            self.move_selection(self.mapToScene(event.pos()))

        # Add mouse position to cut line
        if self._state == self.STATE_CUTTING:
            self._cutter.add_point(self.mapToScene(event.pos()))

    def set_editing_flag(self, editing: bool) -> None:
        """
        Set flag that indicates whether content is being edited
        :param editing: whether content is being edited
        :return: None
        """
        self._editing = editing

    def start_drag(self, socket_graphics: SocketGraphics) -> None:
        """
        Start dragging an edge from this socket
        :param socket_graphics: start socket for edge
        :return: None
        """
        self._state = self.STATE_DRAGGING
        self._drag_start = socket_graphics.socket
        self._drag_edge = Edge(scene=self.scene_graphics.scene, theme=self.theme)

        # Set both start and end position of dragged edge to the start socket
        pos = self._drag_start.graphics.get_scene_position()
        self._drag_edge.graphics.pos_start = pos
        self._drag_edge.graphics.pos_end = pos

    def end_drag(self, item: QGraphicsItem or None) -> None:
        """
        Stop dragging the edge
        :param item: item that was clicked to end the drag
        :return: None
        """
        # Reset tracking variables
        self._state = self.STATE_DEFAULT
        self._drag_edge.remove()
        self._drag_edge = None

        # Check if the drag ended on a valid socket that the edge can be connected to
        if not isinstance(item, SocketGraphics):
            return
        if item.socket == self._drag_start:
            return
        if item.socket.entry.node == self._drag_start.entry.node:
            return
        if item.socket.entry.entry_type == self._drag_start.entry.entry_type:
            return

        # Check if an edge already exists between these two sockets
        for edge in self.scene_graphics.scene.edges:
            if ((edge.start == self._drag_start and edge.end == item.socket) or
                    (edge.end == self._drag_start and edge.start == item.socket)):
                return

        # Remove all present edges from input sockets (only single edge allowed)
        if item.socket.entry.entry_type == Entry.TYPE_INPUT:
            item.socket.remove_all_edges()
        if self._drag_start.entry.entry_type == Entry.TYPE_INPUT:
            self._drag_start.remove_all_edges()

        # Create a new edge to connect the start and end sockets
        Edge(self._drag_start, item.socket, self.scene_graphics.scene, self.theme)
        self._drag_start = None

    def calculate_drag_pos(self, mouse_pos: QPoint) -> QPoint:
        """
        Determine the dragged edge end position based on the mouse location (snap to sockets)
        :param mouse_pos: mouse position (in scene coordinates)
        :return: QPoint: end location for dragged edge
        """
        dragged_socket = self.get_drag_socket(mouse_pos)
        if dragged_socket is not None:
            return dragged_socket.graphics.get_scene_position()
        return self.mapToScene(mouse_pos)

    def get_drag_socket(self, mouse_pos: QPoint) -> Socket or None:
        """
        Get the socket the drag should connect to (or None if not connected to any socket)
        :param mouse_pos: mouse position (global coordinates)
        :return: Socket or None: dragged socket (or None if hovering freely)
        """
        # Use nearest socket position if within snap radius
        socket, dist = self.closest_socket(self.mapToScene(mouse_pos))
        if dist <= self._snap_radius:
            return socket

        # Otherwise, use socket connected to hovered entry
        hovered_item = self.itemAt(mouse_pos)
        if isinstance(hovered_item, EntryGraphics) and hovered_item.entry.socket is not None:
            return hovered_item.entry.socket

        # Otherwise, return None
        return None

    def closest_socket(self, pos: QPoint) -> tuple[Socket, float]:
        """
        Find the socket closest to a position
        :param pos: position relative to which to look for sockets
        :return: tuple[Socket, float]: closest socket and its distance to the specified position
        """
        min_dist = float('inf')
        min_socket = None
        px, py = pos.x(), pos.y()
        for node in self.scene_graphics.scene.nodes:
            for socket in node.sockets():
                if socket != self._drag_start:
                    socket_pos = socket.graphics.get_scene_position()
                    sx, sy = socket_pos.x(), socket_pos.y()
                    dist = sqrt((px - sx) * (px - sx) + (py - sy) * (py - sy))
                    if dist < min_dist:
                        min_dist = dist
                        min_socket = socket
        return min_socket, min_dist

    def mouse_dragged(self, release_point: QPoint, button: Qt.MouseButton = Qt.LeftButton,
                      threshold: int = 3) -> bool:
        """
        Determine if the mouse was dragged more than some threshold
        :param release_point: point of release
        :param button: which mouse button was pressed
        :param threshold: minimum distance to classify as drag
        :return: bool: whether mouse was dragged
        """
        press_point = self._last_left_click if button == Qt.LeftButton else self._last_right_click
        delta = sqrt((press_point.x() - release_point.x()) * (press_point.x() - release_point.x()) +
                     (press_point.y() - release_point.y()) * (press_point.y() - release_point.y()))
        return delta >= threshold

    def zoom_in(self) -> None:
        """
        Zoom in by a step
        :return: None
        """
        # Increase internal zoom tracker
        self._zoom += 1.0

        # Scale the window to the new zoom level (except when maximum zoom level is reached)
        if self._zoom > self._zoom_max:
            self._zoom = self._zoom_max
        else:
            self.scale(self._zoom_speed, self._zoom_speed)

    def zoom_out(self) -> None:
        """
        Zoom out by a step
        :return: None
        """
        # Decrease internal zoom tracker
        self._zoom -= 1.0

        # Scale the window to the new zoom level (except when minimum zoom level is reached)
        if self._zoom < self._zoom_min:
            self._zoom = self._zoom_min
        else:
            self.scale(1 / self._zoom_speed, 1 / self._zoom_speed)

    def zoom_reset(self) -> None:
        """
        Reset the zoom level to initial value
        :return: None
        """
        if self._zoom > 10:
            while self._zoom > 10:
                self.zoom_out()
        else:
            while self._zoom < 10:
                self.zoom_in()

    def remove_selected(self) -> None:
        """
        Remove all selected items in the scene
        :return: None
        """
        for item in self.scene_graphics.selectedItems():
            if isinstance(item, EdgeGraphics):
                item.edge.remove()
            elif isinstance(item, NodeGraphics):
                item.node.remove()

    def create_context_menu(self, position: QPoint) -> None:
        """
        Create a context menu and open it in the specified position
        :param position: global position to open context menu at
        :return: None
        """
        # Create context menu
        context_menu = QMenu()

        # Add menu actions for clicked item
        item = self.itemAt(self.mapFromGlobal(position))
        if isinstance(item, NodeGraphics):
            self._add_node_actions(context_menu, item)
            context_menu.addSeparator()
        elif isinstance(item, SocketGraphics):
            self._add_socket_actions(context_menu, item)
            context_menu.addSeparator()

        # Otherwise, add menu and actions for adding nodes, clipboard, and zooming
        else:
            self._create_add_menu(context_menu)
            context_menu.addSeparator()
            self._add_clipboard_actions(context_menu)
            context_menu.addSeparator()
            self._add_zoom_actions(context_menu)

        # Show context menu at specified position
        context_menu.exec_(position)

    def _create_add_menu(self, parent_menu: QMenu) -> None:
        """
        Add a nested menu with available nodes in the scene
        :param parent_menu: parent menu
        :return: None
        """
        # Helper function that recursively adds actions to the context menu
        def _add_actions(section: dict[str, Type[Node] or dict], menu: QMenu):
            for key, value in section.items():

                # Create a sub-menu for nested dictionary
                if isinstance(value, dict):
                    sub_menu = QMenu(key, menu)
                    _add_actions(value, sub_menu)
                    menu.addMenu(sub_menu)

                # Create an action for a node class
                else:
                    action = QAction(key, parent_menu)
                    action.triggered.connect(partial(self.add_node, value))
                    menu.addAction(action)

        # Create QMenu and add nested menus for all available nodes
        add_menu = QMenu('Add node', parent_menu)
        _add_actions(self.scene_graphics.scene.available_nodes, add_menu)
        add_menu.setDisabled(len(self.scene_graphics.scene.available_nodes) == 0)
        parent_menu.addMenu(add_menu)

    def _add_clipboard_actions(self, parent_menu: QMenu) -> None:
        """
        Add menu actions for clipboard (cut/copy/paste and delete)
        :param parent_menu: parent menu
        :return: None
        """
        # Create actions
        action_cut = QAction('Cut selection', parent_menu)
        action_copy = QAction('Copy selection', parent_menu)
        action_paste = QAction('Paste', parent_menu)
        action_remove = QAction('Remove selection', parent_menu)
        action_duplicate = QAction('Duplicate selection', parent_menu)

        # Connect actions to function
        action_cut.triggered.connect(self.scene_graphics.scene.clipboard.cut)
        action_copy.triggered.connect(self.scene_graphics.scene.clipboard.copy)
        action_paste.triggered.connect(self.scene_graphics.scene.clipboard.paste)
        action_remove.triggered.connect(self.remove_selected)
        action_duplicate.triggered.connect(self.duplicate_selection)

        # Disable actions if no scene items are selected
        if len(self.scene_graphics.selectedItems()) == 0:
            action_cut.setDisabled(True)
            action_copy.setDisabled(True)
            action_remove.setDisabled(True)
            action_duplicate.setDisabled(True)

        # Add actions to menu
        parent_menu.addAction(action_duplicate)
        parent_menu.addAction(action_cut)
        parent_menu.addAction(action_copy)
        parent_menu.addAction(action_remove)
        parent_menu.addAction(action_paste)

    def _add_zoom_actions(self, parent_menu: QMenu) -> None:
        """
        Add menu actions for zooming (zoom in, zoom out, reset zoom)
        :param parent_menu: parent menu
        :return: None
        """
        # Create actions
        action_zoom_in = QAction('Zoom in', parent_menu)
        action_zoom_out = QAction('Zoom out', parent_menu)
        action_zoom_reset = QAction('Reset zoom', parent_menu)

        # Connect actions to function
        action_zoom_in.triggered.connect(self.zoom_in)
        action_zoom_out.triggered.connect(self.zoom_out)
        action_zoom_reset.triggered.connect(self.zoom_reset)

        # Disable zoom in/out if limit is reached
        if self._zoom >= self._zoom_max:
            action_zoom_in.setDisabled(True)
        if self._zoom <= self._zoom_min:
            action_zoom_out.setDisabled(True)

        # Add actions to menu
        parent_menu.addAction(action_zoom_in)
        parent_menu.addAction(action_zoom_out)
        parent_menu.addAction(action_zoom_reset)

    def _add_node_actions(self, parent_menu: QMenu, node_graphics: NodeGraphics) -> None:
        """
        Add menu actions that can be performed on a right-clicked node
        :param parent_menu: parent menu
        :param node_graphics: NodeGraphics object that was right-clicked
        :return: None
        """
        # Create actions
        action_remove = QAction('Remove node', parent_menu)
        action_duplicate = QAction('Duplicate node', parent_menu)

        # Connect actions to function
        action_remove.triggered.connect(node_graphics.node.remove)
        action_duplicate.triggered.connect(partial(self.duplicate_node, node_graphics))

        # Add actions to menu
        parent_menu.addAction(action_remove)
        parent_menu.addAction(action_duplicate)

    @staticmethod
    def _add_socket_actions(parent_menu: QMenu, socket_graphics: SocketGraphics) -> None:
        """
        Add menu actions that can be performed on a right-clicked socket
        :param parent_menu: parent menu
        :param socket_graphics: SocketGraphics object that was right-clicked
        :return: None
        """
        # Create action
        action_disconnect = QAction('Disconnect edges', parent_menu)

        # Connect action to function
        action_disconnect.triggered.connect(socket_graphics.socket.remove_all_edges)

        # Add action to menu
        parent_menu.addAction(action_disconnect)

    def add_node(self, node_class: Type[Node]) -> None:
        """
        Add a new node to the scene at the specified position
        :param node_class: node class definition to add
        :return: None
        """
        node = node_class()
        self.scene_graphics.scene.add_node(node)
        node.graphics.theme = self.theme

        # Select only the added node and start placing it
        self.scene_graphics.clearSelection()
        node.graphics.setSelected(True)
        self.move_selection(self.mapToScene(self.mapFromGlobal(QCursor.pos())))
        self._state = self.STATE_PLACING

    def duplicate_node(self, node_graphics: NodeGraphics) -> None:
        """
        Duplicate an instance of a node
        :param node_graphics: graphics of node to duplicate
        :return: None
        """
        # Create duplicate node to add to the scene
        duplicate = type(node_graphics.node)()
        duplicate.set_state(node_graphics.node.get_state())
        self.scene_graphics.scene.add_node(duplicate)

        # Select only the duplicated node and start placing it
        self.scene_graphics.clearSelection()
        duplicate.graphics.setSelected(True)
        self.move_selection(self.mapToScene(self.mapFromGlobal(QCursor.pos())))
        self._state = self.STATE_PLACING

    def move_selection(self, position: QPoint) -> None:
        """
        Center the selected items in the scene around a position
        :param position: scene position to center selected items around
        :return: None
        """
        # Calculate the coordinate of the center of the selected items
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        items = self.scene_graphics.selectedItems()
        for item in items:
            if isinstance(item, NodeGraphics):
                x, y = item.pos().x(), item.pos().y()
                min_x, max_x = min(min_x, x), max(max_x, x + item.width)
                min_y, max_y = min(min_y, y), max(max_y, y + item.height)
        center_x = (max_x - min_x) / 2 + min_x
        center_y = (max_y - min_y) / 2 + min_y

        # Calculate offset and move all items by that much
        offset_x, offset_y = position.x() - center_x, position.y() - center_y
        for item in items:
            if isinstance(item, NodeGraphics):
                item.moveBy(offset_x, offset_y)

    def duplicate_selection(self) -> None:
        """
        Duplicate the selected items
        :return:
        """
        # Check if there are selected nodes
        selected_nodes = False
        for item in self.scene_graphics.selectedItems():
            if isinstance(item, NodeGraphics):
                selected_nodes = True
        if not selected_nodes:
            return

        # Duplicate selection and start placing it
        selected_state = self.scene_graphics.scene.clipboard.get_selected_state()
        self.scene_graphics.scene.clipboard.add_state(selected_state)
        self.move_selection(self.mapToScene(self.mapFromGlobal(QCursor.pos())))
        self._state = self.STATE_PLACING

    def __str__(self) -> str:
        """
        Get a string representation of the view
        :return: str: string representation of the view
        """
        return f"<NodeView for '{self.scene_graphics.scene}'>"
