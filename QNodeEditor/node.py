"""
Node containing entries with widgets and sockets

This module contains a class derived from QObject. The object contains a list of entries that make
up the structure of the node and determine its look. Contains a graphics object that exists in a
:py:class:`~.scene.NodeScene`..
"""
# pylint: disable = no-name-in-module
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Iterable, overload, Any, Type

from PyQt5.QtCore import QObject, pyqtSignal

from QNodeEditor.entry import Entry
from QNodeEditor.graphics.node import NodeGraphics
from QNodeEditor.metas import ObjectMeta
from QNodeEditor.util import NoValue, get_widget_value
from QNodeEditor.entries import ValueBoxEntry, ComboBoxEntry, LabeledEntry
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene
    from QNodeEditor.socket import Socket


class Node(QObject, metaclass=ObjectMeta):
    """
    Node container holding inputs, outputs, widgets, and various utility methods.

    This class is abstract and cannot be used by itself. To define nodes for the node editor,
    inherit from this class and implement (some of) the following functions:

    - :py:meth:`create`: To add entries to the node and set properties such as its title
    - :py:meth:`evaluate`: To use the inputs and static widgets of the node to determine its outputs
    - :py:meth:`save`: To save any variables that are needed to restore the node state
    - :py:meth:`load`: To use any saved variables to restore the node to its desired state

    From these, only the py:meth:`create` method is strictly required.

    Examples
    --------
    To define a node that takes two number inputs and uses their sum as the output:

    .. code-block:: python

        class MyNode(Node):
            code = 1  # Unique to MyNode

            def create(self):
                self.title = 'Add'  # Set the title of the node

                self.add_label_output('Output')  # Add a labeled output 'Output'
                self.add_value_input('Value 1')  # Add a number input 'Value 1'
                self.add_value_input('Value 2')  # Add another input 'Value 2'

            def evaluate(self, values):
                result = values['Value 1'] + values['Value 2']  # Calculate sum of Value 1 and 2
                self.set_output_value('Output', result)         # Set 'Output' value

    Here, the :py:meth:`create` method is called when the node is created. The :py:meth:`evaluate`
    function is called when the node scene is evaluated (and the node is somehow connected to the
    output). It receives as its argument ``values``. This is a dictionary of the values for each
    entry in the node. In this case, ``values`` would look like this:

    .. code-block:: python

            values = {
                'Output': None,
                'Value 1': 10.0,  # some number
                'Value 2': 5.0    # another number
            }

    For ``MyNode``, we do not need to implement the :py:meth:`save` or :py:meth:`load` function,
    since the value inputs are automatically saved. In case you implement custom entries, you can
    use these functions to store variables. The :py:meth:`save` function should return a dictionary
    and can contain any data you want to save (as long as it is JSON-parsable). Whatever you choose
    to save will be provided back in the :py:meth:`load` function, so you can restore the state of
    your node.

    Attributes
    ----------
    graphics : :py:class:`~.graphics.node.NodeGraphics`
        Graphics object that is shown in the scene representing this edge
    entries : list[:py:class:`~.entry.Entry`]
        List of the entries in the node. List order is the same as vertical order of entries.
    output : dict[str, Any] or None
        Cached output of the node (do not use)
    """

    code: int
    """int: Unique code that only one derived Node class can use"""

    evaluated: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the node is evaluated"""

    def __init__(self, title: str = 'Node'):
        """
        Create a new node.

        Defines an empty node and a graphics object to represent it in the scene.

        Parameters
        ----------
        title : str, default='Node'
            Title of the node (can be accessed through :py:attr:`title`)
        """
        super().__init__()
        # Set node properties
        self.entries: list[Entry] = []
        self.title: str = title
        self.output: Optional[dict[str, Any]] = None

        # Create node graphics
        self.graphics: NodeGraphics = NodeGraphics(self)
        self.scene: Optional['NodeScene'] = None

        # Run function that creates node to be implemented by inheriting class
        self.create()

    @property
    def title(self) -> str:
        """
        Get or set the title of the node
        """
        return self._title

    @title.setter
    def title(self, new_title: str) -> None:
        self._title = new_title
        if hasattr(self, 'graphics'):
            self.graphics.set_title(new_title)

    @abstractmethod
    def create(self) -> None:
        """
        Override this method to add elements to the node and set its properties.

        Returns
        -------
            None
        """

    def evaluate(self, entry_values: dict[str, Any]) -> None:
        """
        Override this method to use the inputs of the node to determine the outputs of the node.

        Use the :py:meth:`set_output_value` method to set output values of the node.

        By default, the entry outputs are set using the corresponding widget value.

        Parameters
        ----------
        entry_values : dict[str, Any]
            Dictionary with (name, value) pairs for each entry in this node.

        Returns
        -------
            None
        """
        for entry in self.entries:
            if entry.entry_type == Entry.TYPE_OUTPUT:
                self.set_output_value(entry, get_widget_value(entry.widget))

    @property
    def scene(self) -> Optional['NodeScene']:
        """
        Get or set the scene this node is part of
        """
        return self._scene

    @scene.setter
    def scene(self, new_scene: Optional['NodeScene']) -> None:
        self.disconnect_signals()
        self._scene = new_scene
        self.connect_signals()

    @property
    def output(self) -> dict[str, Any]:
        """
        Get or set the cached output for this node. (private)

        :meta private:
        """
        # If there is no cached output, evaluate the node
        if self._output is None:
            self._run_evaluate()

        # Return the output
        return self._output

    @output.setter
    def output(self, new_output: Optional[dict[str, Any]]) -> None:
        # If argument is None, reset cached output
        if new_output is None:
            self._output = None
            return

        # Otherwise, store the output in cache
        self._output = new_output

    def _run_evaluate(self) -> None:
        """
        Evaluate this node with the current settings.

        This function contains three steps:
        1. Gather the values of the inputs (either through connected wires or the entry widget)
        2. Run the :py:meth:`evaluate` method (providing the inputs)
        3. Make sure that all node outputs have been set

        If these steps are completed successfully, the results are stored in the output cache. In
        this way, even if the node outputs are connected to multiple other nodes, the evaluation
        only has to run once.

        In the first step, if an input entry is connected to another node, that node is evaluated to
        obtain the calculation result.

        Returns
        -------
            None
        """
        # Get the entry values for the evaluate function
        values = {}
        for entry in self.entries:
            values[entry.name] = entry.calculate_value()

        # Reset outputs and run evaluate function to be implemented by derived nodes
        self._reset_outputs()
        self.evaluate(values)

        # Read the output values (ensure that all of them are set) and store it in node cache
        outputs = {}
        for entry in self.entries:
            if entry.entry_type == Entry.TYPE_OUTPUT:
                if entry.value is NoValue:
                    raise ValueError(f"Output for entry '{entry.name}' in node "
                                     f"'{self.title}' was not set")
                outputs[entry.name] = entry.value
        self.output = outputs
        self.evaluated.emit()

    def _reset_outputs(self) -> None:
        """
        Set the value of all output entries to :py:class:`~.util.NoValue`.

        Returns
        -------
            None
        """
        for entry in self.entries:
            if entry.entry_type == Entry.TYPE_OUTPUT:
                entry.value = NoValue

    def set_output_value(self, entry: str or Entry, value: Any) -> None:
        """
        Set the value of an output entry.

        Use this function in the :py:meth:`evaluate` method in derived classes. The outputs can then
        be used by any nodes connected to them.

        Parameters
        ----------
        entry : str or :py:class:`!.entry.Entry`
            The (name of the) output entry to set the output value for
        value : Any
            The value to give the output

        Returns
        -------
            None
        """
        # If string is provided, find entry by name
        if isinstance(entry, str):
            entry = self.get_entry(entry)

        # Check if entry exists in node and is an output
        if entry not in self:
            raise ValueError(f"No entry '{entry}' exists in this node")
        if entry.entry_type != Entry.TYPE_OUTPUT:
            raise ValueError(f"Entry '{entry}' is not an output")

        # Set the output value
        entry.value = value

    def connect_signals(self) -> None:
        """
        Connect signals from all entries to the scene

        Returns
        -------
            None
        """
        for entry in self.entries:
            entry.connect_signal()

    def disconnect_signals(self) -> None:
        """
        Disconnect signals from all entries from the scene

        Returns
        -------
            None
        """
        for entry in self.entries:
            entry.disconnect_signal()

    def remove(self) -> None:
        """
        Remove this node from the scene.

        The node will be removed from the scene. Any edges connected to the node are removed as
        well.

        Returns
        -------
            None
        """
        # Disconnect all edges from the node
        for socket in self.sockets():
            for edge in reversed(socket.edges):
                edge.remove()

        # Remove the node from the scene
        self.scene.graphics.removeItem(self.graphics)
        self.scene.remove_node(self)
        self.graphics = None

    def add_entry(self, entry: Entry) -> None:
        """
        Add an entry to this node.

        Append a new entry to the node content. The entry will be placed as the last entry (bottom)
        of the node.

        See Also
        --------
        :py:meth:`add_entries`: Add multiple entries
        :py:meth:`insert_entry`: Add an entry at a specific index
        :py:meth:`insert_entries`: Add multiple entries at a specific index

        Parameters
        ----------
        entry : :py:class:`~.entry.Entry`
            Entry to add to the node

        Returns
        -------
            None
        """
        if entry.name in self.entry_names():
            raise ValueError(f'An entry with the name "{entry.name}" already exists')

        self.entries.append(entry)
        entry.node = self

    def add_entries(self, entries: Iterable[Entry]) -> None:
        """
        Add multiple entries to this node.

        Append multiple new entries to the node content. The entries will be placed at the end
        (bottom) of the node.

        See Also
        --------
        :py:meth:`add_entry`: Add a single entry
        :py:meth:`insert_entry`: Add an entry at a specific index
        :py:meth:`insert_entries`: Add multiple entries at a specific index

        Parameters
        ----------
        entries : Iterable[:py:class:`~.entry.Entry`]
            Iterable of entries to add to the node

        Returns
        -------
            None
        """
        for entry in entries:
            self.add_entry(entry)

    def insert_entry(self, entry: Entry, index: int) -> None:
        """
        Insert an entry into this node at a specific index.

        Inserts a new entry into the node content. The position of the entry is determined by the
        index (``0`` being the first (top) element).

        See Also
        --------
        :py:meth:`add_entry`: Add a single entry at the end
        :py:meth:`add_entries`: Add multiple entries at the end
        :py:meth:`insert_entries`: Add multiple entries at a specific index

        Parameters
        ----------
        entry : :py:class:`~.entry.Entry`
            Entry to add to the node
        index : int
            Index at which to insert the entry

        Returns
        -------
            None
        """
        if entry.name in self.entry_names():
            raise ValueError(f'An entry with the name "{entry.name}" already exists')

        self.entries.insert(index, entry)
        entry.node = self

    def insert_entries(self, entries: Iterable[Entry], index: int) -> None:
        """
        Insert multiple entries into this node at a specific index.

        Inserts new entries into the node content. The position of the entries is determined by the
        index (``0`` being the top-most entry).

        See Also
        --------
        :py:meth:`add_entry`: Add a single entry at the end
        :py:meth:`add_entries`: Add multiple entries at the end
        :py:meth:`insert_entry`: Add a single entry at a specific index

        Parameters
        ----------
        entries : Iterable[:py:class:`~.entry.Entry`]
            Iterable of entries to add to the node
        index : int
            Index at which to insert the entries

        Returns
        -------
            None
        """
        for i, entry in enumerate(entries):
            self.insert_entry(entry, index + i)

    def index(self, entry: str or Entry) -> int:
        """
        Get the index of the specified entry.

        Finds the entry (optionally by name) and returns its index (``0`` being the top-most entry).

        Parameters
        ----------
        entry : str or :py:class:`~.entry.Entry`
            The (name of the) entry to get the index of

        Returns
        -------
        int
            Index of the specified entry

        Raises
        ------
        KeyError
            If the entry could not be found in the node
        """
        if isinstance(entry, str):
            entry = self.get_entry(entry)
        return self.entries.index(entry)

    @overload
    def remove_entry(self, name: str) -> None:
        pass

    @overload
    def remove_entry(self, entry: Entry) -> None:
        pass

    def remove_entry(self, entry) -> None:
        """
        Remove an entry from the node.

        Finds and removes the specified entry from the node. The node is automatically resized to
        fit the remaining content.

        Parameters
        ----------
        entry : str or :py:class:`~.entry.Entry`
            The (name of the) entry to remove.

        Returns
        -------
            None

        Raises
        ------
        TypeError
            If the ``entry`` argument is not a string or :py:class:`~.entry.Entry`
        """
        # If argument is not an Entry object or string, raise error
        if not isinstance(entry, (str, Entry)):
            raise TypeError(f'Cannot remove entry {entry}, incorrect type')

        # Get entry by name if string is provided
        if isinstance(entry, str):
            entry = self.get_entry(entry)

        # Remove the entry from the node
        entry.remove()

    def remove_all_entries(self) -> None:
        """
        Remove all entries from the node.

        This methods clears all of the content from the node. Since all entries are removed, any
        edges connected to inputs/outputs are also removed.

        Returns
        -------
            None
        """
        while len(self.entries) > 0:
            entry = self.entries.pop(0)
            entry.remove()

    def update_entries(self) -> None:
        """
        Update the geometry of all entries in the node.

        Returns
        -------
            None

        :meta private:
        """
        for entry in self.entries:
            entry.update_geometry()

    def entry_names(self) -> list[str]:
        """
        Get the names of all entries in the node.

        The result of this function is a list of names. Entry names within a node are unique.

        Returns
        -------
            None
        """
        return [entry.name for entry in self.entries]

    def get_entry(self, name: str) -> Entry:
        """
        Get an entry object by its name.

        Parameters
        ----------
        name : str
            Name of the entry to retrieve.

        Returns
        -------
        :py:class:`~.entry.Entry`
            The entry with the specified name.

        Raises
        ------
        KeyError
            If no entry with the specified name exists.
        """
        for entry in self.entries:
            if entry.name == name:
                return entry
        raise KeyError(f'Entry with name {name} does not exist')

    def add_value_entry(self, name: str, entry_type: int = Entry.TYPE_STATIC,
                        value: int or float = 0, minimum: int or float = -100,
                        maximum: int or float = 100,
                        value_type: Type[int] or Type[float] = float) -> None:
        """
        Add a new value box entry to the node.

        Adds a new entry to the node containing a :py:class:`~.widgets.value_box.ValueBox` widget.

        By default, the entry is static (no inputs/outputs).

        Parameters
        ----------
        name : str
            Name of this entry
        entry_type : int
            Type of entry (:py:attr:`~.entry.Entry.TYPE_STATIC`, :py:attr:`~.entry.Entry.TYPE_INPUT`
            , or :py:attr:`~.entry.Entry.TYPE_OUTPUT`)
        value : int or float
            Initial value of the :py:class:`~.widgets.value_box.ValueBox`
        minimum : int or float
            Minimum value of the :py:class:`~.widgets.value_box.ValueBox`
        maximum : int or float
            Maximum value of the :py:class:`~.widgets.value_box.ValueBox`
        value_type : Type[int] or Type[float]
            Type of :py:class:`~.widgets.value_box.ValueBox` (``float`` or ``int``)

        Returns
        -------
            None
        """
        entry = ValueBoxEntry(name, entry_type, value, minimum, maximum, value_type,
                              theme=self.graphics.theme)
        self.add_entry(entry)

    def add_value_input(self, name: str, value: int or float = 0,
                        minimum: int or float = -100, maximum: int or float = 100,
                        value_type: Type[int] or Type[float] = float) -> None:
        """
        Add a new value box input to the node.

        Adds a new entry to the node containing a :py:class:`~.widgets.value_box.ValueBox` widget.
        The entry has an input socket.

        Parameters
        ----------
        name : str
            Name of this entry
        value : int or float
            Initial value of the :py:class:`~.widgets.value_box.ValueBox`
        minimum : int or float
            Minimum value of the :py:class:`~.widgets.value_box.ValueBox`
        maximum : int or float
            Maximum value of the :py:class:`~.widgets.value_box.ValueBox`
        value_type : Type[int] or Type[float]
            Type of :py:class:`~.widgets.value_box.ValueBox` (``float`` or ``int``)

        Returns
        -------
            None
        """
        self.add_value_entry(name, Entry.TYPE_INPUT, value, minimum, maximum, value_type)

    def add_value_output(self, name: str, value: int or float = 0,
                         minimum: int or float = -100, maximum: int or float = 100,
                         value_type: Type[int] or Type[float] = float) -> None:
        """
        Add a new value box output to the node.

        Adds a new entry to the node containing a :py:class:`~.widgets.value_box.ValueBox` widget.
        The entry has an output socket.

        Parameters
        ----------
        name : str
            Name of this entry
        value : int or float
            Initial value of the :py:class:`~.widgets.value_box.ValueBox`
        minimum : int or float
            Minimum value of the :py:class:`~.widgets.value_box.ValueBox`
        maximum : int or float
            Maximum value of the :py:class:`~.widgets.value_box.ValueBox`
        value_type : Type[int] or Type[float]
            Type of :py:class:`~.widgets.value_box.ValueBox` (``float`` or ``int``)

        Returns
        -------
            None
        """
        self.add_value_entry(name, Entry.TYPE_OUTPUT, value, minimum, maximum, value_type)

    def add_label_entry(self, name: str, entry_type: int = Entry.TYPE_STATIC) -> None:
        """
        Add a new labeled entry to the node.

        Adds a new entry to the node containing only a label with the entry name.

        Parameters
        ----------
        name : str
            Name of this entry
        entry_type : int
            Type of entry (:py:attr:`~.entry.Entry.TYPE_STATIC`, :py:attr:`~.entry.Entry.TYPE_INPUT`
            , or :py:attr:`~.entry.Entry.TYPE_OUTPUT`)

        Returns
        -------
            None
        """
        entry = LabeledEntry(name, entry_type, self.graphics.theme)
        self.add_entry(entry)

    def add_label_input(self, name: str) -> None:
        """
        Add a new labeled input to the node.

        Adds a new entry to the node containing only a label with the entry name. The entry has an
        input socket.

        Parameters
        ----------
        name : str
            Name of this entry

        Returns
        -------
            None
        """
        self.add_label_entry(name, Entry.TYPE_INPUT)

    def add_label_output(self, name: str) -> None:
        """
        Add a new labeled output to the node.

        Adds a new entry to the node containing only a label with the entry name. The entry has an
        output socket.

        Parameters
        ----------
        name : str
            Name of this entry

        Returns
        -------
            None
        """
        self.add_label_entry(name, Entry.TYPE_OUTPUT)

    def add_combo_box_entry(self, name: str, items: Iterable[str] or dict[str, Any] = None) -> None:
        """
        Add a new combo box entry to the node.

        Adds a new entry to the node containing a combo box widget. This entry can only be static.

        Parameters
        ----------
        name : str
            Name of this entry
        items : Iterable[str] or dict[str, Any]
            Possible values of the combo box.

            Can be a list of strings used as the ``name`` of each option.

            Can be a dictionary of (``name``, ``data``) pairs.

            If a dictionary is used, the ``values`` argument for the :py:meth:`evaluate` method will
            contain the ``data`` for the selected option. Otherwise, it will contain the ``name``.

        Returns
        -------
            None
        """
        entry = ComboBoxEntry(name, items=items)
        self.add_entry(entry)

    def __getitem__(self, item: int or str) -> Entry:
        """
        Get an entry in the node by name or index.

        Parameters
        ----------
        item : int or str
            Index or name of entry to get

        Returns
        -------
        :py:class:`~.entry.Entry`
            Entry with specified name or index

        Raises
        ------
        TypeError
            If the specified item is not a string or integer
        """
        if isinstance(item, str):
            return self.get_entry(item)
        if isinstance(item, int):
            return self.entries[item]
        raise TypeError(f'Cannot get item, type "{type(item)}" not supported')

    def __delitem__(self, key: int or str) -> None:
        """
        Remove an entry from the node by name or index.

        Parameters
        ----------
        key : int or str
            Index or name of entry to remove from the node.

        Returns
        -------
            None

        Raises
        ------
        TypeError
            If the specified key is not a string or integer
        """
        # Find entry to remove
        if isinstance(key, str):
            entry = self.get_entry(key)
        elif isinstance(key, int):
            entry = self.entries[key]
        else:
            raise TypeError(f'Cannot remove item, type "{type(key)}" not supported')

        # Remove the entry
        self.remove_entry(entry)

    def __contains__(self, item: Entry or str) -> bool:
        """
        Check if this node contains the specified entry.

        Parameters
        ----------
        item : :py:class:`~.entry.Entry` or str
            The (name of the) entry to locate in the node

        Returns
        -------
        bool
            Whether the specified entry exists in the node
        """
        if isinstance(item, str):
            return item in self.entry_names()
        return item in self.entries

    def __len__(self) -> int:
        """
        Get the number of entries in this node..

        Returns
        -------
        int
            Number of entries in the node
        """
        return len(self.entries)

    def __str__(self) -> str:
        """
        Get a string representation of the node

        Returns
        -------
        str
            String representation of the node
        """
        return f"<Node '{self.title}' with {len(self)} entries>"

    def sockets(self) -> list['Socket']:
        """
        Get a list of all sockets in this node.

        Goes through each entry and collects its socket (if it has one)

        Returns
        -------
        list[:py:class:`~.socket.Socket`]
            List of :py:class:`~.socket.Socket` objects that are in this node
        """
        result = []
        for entry in self.entries:
            if entry.socket is not None:
                result.append(entry.socket)
        return result

    def save(self) -> dict:
        """
        Override this method to save any additional values to the node state.

        The dictionary returned by this function is saved along with the rest of the node state. It
        is provided back to the :py:meth:`load` method when the node is loaded again.

        Use this method to add any variables to the node state that are needed to restore the node
        to the desired state when the node is loaded.

        Returns
        -------
        dict:
            Additional values to save (key, value) pairs.

            Must be JSON-safe.

        :meta abstract:
        """
        return {}

    def load(self, state: dict) -> bool:
        """
        Override this method to load the saved additional values and restore the node state.

        The received ``state`` is the same as the dictionary returned by the :py:meth:`save`
        method (an empty dictionary if not overridden).

        Use this method to use the saved values to restore the node to the desired state.

        Parameters
        ----------
        state : dict
            Saved additional values by :py:meth:`save`

        Returns
        -------
        bool
            Whether the method executed successfully
        """
        return True

    def get_state(self) -> dict:
        """
        Get the state of this node as a (JSON-safe) dictionary.

        The dictionary contains:

        - ``code``: the unique code assigned to this node type
        - ``title``: Title of the node
        - ``pos_x``: X-location of the node in the scene
        - ``pos_y``: Y-location of the node in the scene
        - ``entries``: list of states for each entry
        - ``custom``: additional values saved through the :py:meth:`save` method

        Returns
        -------
        dict
            JSON-safe dictionary representing the node state
        """
        return {
            'code': self.code,
            'title': self.title,
            'pos_x': self.graphics.scenePos().x(),
            'pos_y': self.graphics.scenePos().y(),
            'entries': [entry.get_state() for entry in self.entries],
            'custom': self.save()
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set ths state of this node from a state dictionary.

        The dictionary contains:

        - ``code``: the unique code assigned to this node type
        - ``title``: Title of the node
        - ``pos_x``: X-location of the node in the scene
        - ``pos_y``: Y-location of the node in the scene
        - ``entries``: list of states for each entry
        - ``custom``: additional values saved through the :py:meth:`save` method

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired node state
        restore_id : bool
            Whether to restore the internal IDs of the node sockets (used to reconnect saved edges)

            Is set to ``False`` for copy-paste operations (sockets take on new unique ID)

        Returns
        -------
        bool
            Whether setting the node state succeeded

        Raises
        ------
        ValueError
            If the number of entry states in the ``state`` argument does not match the number of
            entries in the node after running the :py:meth:`create` method.

            If this occurs, the node does not have the same entries as when it was saved. Use the
            :py:meth:`save` and :py:meth:`load` methods to save and restore additional values such
            that the node ends up with the same entries.
        """
        # Call custom function that could be overloaded by derived classes
        result = self.load(state.get('custom', {}))

        # Set node properties
        self.title = state.get('title', 'Node')
        x, y = state.get('pos_x', 0), state.get('pos_y', 1)
        self.graphics.setPos(x, y)

        # Set state for all entries
        entry_states = state.get('entries', [])
        if len(entry_states) != len(self.entries):
            raise ValueError(f'Length of entry states ({len(entry_states)}) does not '
                             f'match number of node entries ({len(self.entries)})')
        for entry_state, entry in zip(entry_states, self.entries):
            result &= entry.set_state(entry_state, restore_id)

        return result & True
