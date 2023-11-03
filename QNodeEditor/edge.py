"""Edge container storing start+end and other edge properties"""
# pylint: disable = no-name-in-module
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal

from QNodeEditor.graphics.edge import EdgeGraphics, BezierEdgeGraphics, DirectEdgeGraphics
from QNodeEditor.socket import Socket
from QNodeEditor.metas import ObjectMeta
from QNodeEditor.themes import ThemeType, DarkTheme
from QNodeEditor.entry import Entry
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene


class Edge(QObject, metaclass=ObjectMeta):
    """Class housing all elements of a connection between sockets"""

    # Create edge signals
    start_changed: pyqtSignal = pyqtSignal()
    end_changed: pyqtSignal = pyqtSignal()
    edge_type_changed: pyqtSignal = pyqtSignal()

    def __init__(self,
                 start: Optional[Socket] or Optional[Entry] = None,
                 end: Optional[Socket] or Optional[Entry] = None,
                 scene: Optional['NodeScene'] = None,
                 theme: ThemeType = DarkTheme):
        """
        Create a new edge with a start and end with a specific line type
        :param start: start socket (or entry with start socket)
        :param end: end socket (or entry with end socket)
        :param scene: scene the edge should be part of
        :param theme: theme to use for edge
        """
        super().__init__()
        # Get socket if start or end is an Entry
        if isinstance(start, Entry):
            start: Socket = start.socket
        if isinstance(end, Entry):
            end: Socket = end.socket

        # If the scene is not provided, try to derive it from the start/end sockets
        if scene is None:

            # Get scene start socket is in (if any)
            if start is not None and start.entry.node is not None:
                start_scene = start.entry.node.scene
            else:
                start_scene = None

            # Get scene end socket is in (if any)
            if end is not None and end.entry.node is not None:
                end_scene = end.entry.node.scene
            else:
                end_scene = None

            # Use start/end socket scene, or raise an error
            if start_scene is not None and end_scene is None:
                scene = start_scene
            elif start_scene is None and end_scene is not None:
                scene = end_scene
            elif start_scene is not None and end_scene is not None and start_scene == end_scene:
                scene = start_scene
            elif start_scene is not None and end_scene is not None:
                raise ValueError('Start and end sockets are in different scenes')
            else:
                raise ValueError('No scene provided and could not deduce it from sockets')

        # Set edge properties
        self.graphics: EdgeGraphics = None
        self._start: Optional[Socket] = None
        self._end: Optional[Socket] = None
        self.theme: ThemeType = theme
        self.scene: 'NodeScene' = scene

        # Add edge to start and end points (if specified)
        if start is not None:
            self.start = start
        if end is not None:
            self.end = end

    @property
    def theme(self) -> ThemeType:
        """
        Get the current edge theme
        :return: ThemeType: edge theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the edge
        :param new_theme: new edge theme
        :return: None
        """
        self._theme = new_theme
        self.create_graphics()
        self.graphics.theme = new_theme
        self.update_positions()

    def create_graphics(self) -> None:
        """
        Create edge graphics based on the selected edge type
        :return: None
        """
        # Remove old edge graphics and remember the start and end positions (if it exists)
        if (hasattr(self, 'graphics') and hasattr(self, 'scene') and
                self.graphics is not None and self.scene is not None):
            old_start = self.graphics.pos_start
            old_end = self.graphics.pos_end
            self.scene.graphics.removeItem(self.graphics)
        else:
            old_start = None
            old_end = None

        # Create new graphics for the edge
        if self.theme.edge_type == 'direct':
            self.graphics = DirectEdgeGraphics(self)
        elif self.theme.edge_type == 'bezier':
            self.graphics = BezierEdgeGraphics(self)
        else:
            raise ValueError(f'Unknown edge type "{self.theme.edge_type}"')

        # Revert to the old positions if they are available
        if old_start is not None:
            self.graphics.pos_start = old_start
        if old_end is not None:
            self.graphics.pos_end = old_end

        # Add new graphics to the scene (if it exists)
        if hasattr(self, 'scene') and self.scene is not None:
            self.scene.graphics.addItem(self.graphics)
        self.edge_type_changed.emit()

    @property
    def start(self) -> Optional[Socket]:
        """
        Get the socket the edge starts in
        :return: NodeScene: edge start socket
        """
        return self._start

    @start.setter
    def start(self, new_start: Socket) -> None:
        """
        Set the start socket for the edge
        :param new_start: new start socket
        :return: None
        """
        # Remove edge from old socket if present
        if self._start is not None:
            self._start.remove_edge(self)

        # Set new socket and attach edge
        self._start = new_start
        if new_start is not None:
            self._start.add_edge(self)

        # Update the graphics of the edge
        if self.graphics is not None:
            self.update_positions()

        # Emit signal
        self.start_changed.emit()

    @property
    def end(self) -> Optional[Socket]:
        """
        Get the socket the edge ends in
        :return: NodeScene: edge end socket
        """
        return self._end

    @end.setter
    def end(self, new_end: Socket) -> None:
        """
        Set the end socket for the edge
        :param new_end: new end socket
        :return: None
        """
        # Remove edge from old socket if present
        if self._end is not None:
            self._end.remove_edge(self)

        # Set new socket and attach edge
        self._end = new_end
        if new_end is not None:
            self._end.add_edge(self)

        # Update the graphics of the edge
        if self.graphics is not None:
            self.update_positions()

        # Emit signal
        self.end_changed.emit()

    @property
    def scene(self) -> 'NodeScene':
        """
        Get the scene the edge is part of
        :return: NodeScene: scene edge is in
        """
        return self._scene

    @scene.setter
    def scene(self, new_scene: 'NodeScene') -> None:
        """
        Set a new scene for the edge to be part of
        :param new_scene: new scene to place edge in
        :return: None
        """
        self._scene = new_scene

        # Add edge graphics to the scene if not None
        new_scene.edges.append(self)
        new_scene.graphics.addItem(self.graphics)
        self.update_positions()
        self.graphics.update()

    def update_positions(self) -> None:
        """
        Update the positions of the start and end points
        :return: None
        """
        # Calculate start position
        if self.start is not None and self.start.entry.node is not None:
            self.graphics.pos_start = self.start.graphics.get_scene_position()

        # Calculate end position (use start position if None)
        if self.end is not None and self.end.entry.node is not None:
            self.graphics.pos_end = self.end.graphics.get_scene_position()
        elif self.start is not None and self.start.entry.node is not None:
            self.graphics.pos_end = self.start.graphics.get_scene_position()

        self.graphics.update()

    def remove_from_sockets(self) -> None:
        """
        Remove the edge from the sockets it is connected to (if any)
        :return: None
        """
        self.start = None
        self.end = None

    def remove(self) -> None:
        """
        Remove this edge from the scene
        :return: None
        """
        # Remove the edge from all sockets
        self.remove_from_sockets()

        if self.scene is not None:

            # Remove graphics from the scene
            if self.graphics is not None:
                self.scene.graphics.removeItem(self.graphics)
                self.graphics = None

            # Remove object from scene edges
            if self in self.scene.edges:
                self.scene.edges.remove(self)

    def __str__(self) -> str:
        """
        Get a string representation of the edge
        :return: str: string representation of the edge
        """
        return f"<Edge from '{self.start}' to '{self.end}'>"

    def get_state(self) -> dict:
        """
        Get the state of the edge as a dictionary
        :return: dict: representation of the edge state
        """
        return {
            'start': None if self.start is None else self.start.id,
            'end': None if self.end is None else self.end.id
        }

    def set_state(self, state: dict, lookup: dict[str, str] = None) -> bool:
        """
        Set the state of the edge from a dictionary
        :param state: representation of the edge state
        :param lookup: lookup table for socket id in state and socket id in scene
        :return: bool: whether setting state succeeded
        """
        # Read start and end socket ids from state (convert to scene id using lookup table)
        start_id, end_id = state.get('start', None), state.get('end', None)
        if start_id is not None:
            start_id = lookup[start_id]
        if end_id is not None:
            end_id = lookup[end_id]

        # Ensure the start and end sockets exist in the scene (if not None)
        sockets = self.scene.socket_instances()
        if ((start_id is not None and start_id not in sockets) or
                (end_id is not None and end_id not in sockets)):
            return False

        # Set the start and end sockets for this edge (if not None)
        if start_id is None:
            self.start = None
        else:
            self.start = sockets[start_id]
        if end_id is None:
            self.end = None
        else:
            self.end = sockets[end_id]
        return True
