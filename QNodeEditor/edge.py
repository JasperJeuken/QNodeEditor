"""
Edge consisting of a connection between a start and end point

This module contains a class derived from QObject. The object contains a start and end socket that
determine the shape of the edge. Contains a graphics object that exists in a
:py:class:`~.scene.NodeScene`.
"""
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
    """
    Edge container holding a start and end socket, and various utility methods.
    
    This class represents a connection between two sockets. It is also possible for only one end of
    the edge to be connected to a socket.
    
    Edges can only connect an input to an output, or vice versa. It is not possible to connect two
    inputs or two outputs together.
    
    In general, it is not necessary to instantiate this class since it is handled by the node editor
    itself. However, in case you want to set the state of a node editor before opening it, this
    class can be used to already connect nodes in your scene.
    
    Examples
    --------
    To define an edge that connects two nodes:
    
    .. code-block:: python
        
        node1 = SomeNode()     # Node containing the output entry 'Output'
        node2 = AnotherNode()  # Node containing the input entry 'Value'
        
        edge = Edge(node1['Output'], node2['Value'])
        
    This adds an edge to the :py:class:`~.scene.NodeScene` the nodes are part of.

    Attributes
    ----------
    graphics : :py:class:`~.graphics.edge.EdgeGraphics`
        Graphics object that is shown in the scene representing this edge
    """
    # Create edge signals
    start_changed: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the start socket changed"""
    end_changed: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the end socket changed"""
    edge_type_changed: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the edge type is changed"""

    def __init__(self,
                 start: Optional[Socket] or Optional[Entry] = None,
                 end: Optional[Socket] or Optional[Entry] = None,
                 scene: Optional['NodeScene'] = None,
                 theme: ThemeType = DarkTheme):
        """
        Create a new edge.
        
        Parameters
        ----------
        start : :py:class:`~.socket.Socket` or :py:class:`~.entry.Entry`, optional
            Start point of the edge (either a socket or an entry with a socket)
        end : :py:class:`~.socket.Socket` or :py:class:`~.entry.Entry`, optional
            End point of the edge (either a socket or an entry with a socket)
        scene : :py:class:`~.scene.NodeScene`, optional
            Scene to place the edge in. In general, this argument is not needed and the scene is
            deduced from the start and end sockets. If neither are provided, this argument is
            required.
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the edge (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
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
        Get or set the theme of the edge.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self._create_graphics()
        self.graphics.theme = new_theme
        self.update_positions()

    def _create_graphics(self) -> None:
        """
        Create a graphics object for the edge based on the edge type in the theme

        The edge type defined in the edge :py:attr:`theme` can have the following values:
        - ``'linear'``: direct, linear line connecting the start and end point
        - ``'bezier'``: Bézier curve with automatic control points to create a smooth curve

        Returns
        -------
            None
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
        Get or set the start socket of the edge

        Setting a new start node removes the edge from the old starting point (if it was set) and
        connects the edge to the new start point.
        """
        return self._start

    @start.setter
    def start(self, new_start: Socket) -> None:
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
        Get or set the end socket of the edge

        Setting a new end node removes the edge from the old ending point (if it was set) and
        connects the edge to the new end point.
        """
        return self._end

    @end.setter
    def end(self, new_end: Socket) -> None:
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
        Get or set the scene this edge is part of.

        Setting a new scene removes the edge from the old scene (if it was set) and adds the edge to
        the new scene.
        """
        return self._scene

    @scene.setter
    def scene(self, new_scene: 'NodeScene') -> None:
        self._scene = new_scene

        # Add edge graphics to the scene if not None
        new_scene.edges.append(self)
        new_scene.graphics.addItem(self.graphics)
        self.update_positions()
        self.graphics.update()

    def update_positions(self) -> None:
        """
        Update the positions of the start and end points.

        Used when a node is moved to read the new positions of the start and end sockets and update
        them in the graphics of the edge.

        Returns
        -------
            None
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
        Remove the edge from the sockets it is connected to.

        Returns
        -------
            None
        """
        self.start = None
        self.end = None

    def remove(self) -> None:
        """
        Remove this edge from the scene (and from the sockets it is connected to)
        .
        Returns
        -------
            None
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

        Returns
        -------
        str
            Representation of the edge
        """
        return f"<Edge from '{self.start}' to '{self.end}'>"

    def get_state(self) -> dict:
        """
        Get the state of this edge as a (JSON-safe) dictionary.

        The dictionary contains:
        - ``start``: the ID of the start socket (or None if no start socket)
        - ``end``: the ID of the end socket (or None if no end socket)

        Returns
        -------
        dict
            JSON-safe dictionary representing the edge state
        """
        return {
            'start': None if self.start is None else self.start.id,
            'end': None if self.end is None else self.end.id
        }

    def set_state(self, state: dict, lookup: dict[str, str] = None) -> bool:
        """
        Set the state of this edge from a state dictionary.

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired edge state
        lookup: dict[str, str], optional
            Dictionary with mapping of state socket ID to actual socket ID. If the socket was
            added from a state with `restore_id=True`, these two are equal. Otherwise, the socket
            will take on a new unique ID, which will be the value in (key, value) pairs.

        Returns
        -------
        bool
            Whether setting the edge state succeeded
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
