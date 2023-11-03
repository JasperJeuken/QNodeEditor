"""Node container storing a node and its elements"""
# pylint: disable = no-name-in-module
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Iterable, overload, Any, Type

from PyQt5.QtCore import QObject

from QNodeEditor.entry import Entry
from QNodeEditor.graphics.node import NodeGraphics
from QNodeEditor.metas import ObjectMeta
from QNodeEditor.util import NoValue
from QNodeEditor.entries import ValueBoxEntry, ComboBoxEntry, LabeledEntry
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene
    from QNodeEditor.socket import Socket


class Node(QObject, metaclass=ObjectMeta):
    """Node container holding inputs, outputs, layout, connections, etc..."""

    code: int

    def __init__(self, title: str = 'Node'):
        """
        Create a new node with a title and associate it to a scene (if specified)
        :param title: title of the node
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
        Get the current title of the node
        :return: str
        """
        return self._title

    @title.setter
    def title(self, new_title: str) -> None:
        """
        Set a new title for the node
        :param new_title: new title
        :return: None
        """
        self._title = new_title
        if hasattr(self, 'graphics'):
            self.graphics.set_title(new_title)

    @abstractmethod
    def create(self) -> None:
        """
        Override to create and add the elements of the node
        :return: None
        """

    def evaluate(self, entry_values: dict[str, Any]) -> None:
        """
        Override to read input values and set output values
        :param entry_values: dictionary with (name, value) pairs for each input entry
        :return: None
        """
        raise NotImplementedError(f"The 'evaluate' function was not implemented for '{self}'")

    @property
    def scene(self) -> Optional['NodeScene']:
        """
        Get the scene this node is part of
        :return: NodeScene: scene node is part of
        """
        return self._scene

    @scene.setter
    def scene(self, new_scene: Optional['NodeScene']) -> None:
        """
        Change the scene this node is part of
        :param new_scene: new scene to add node to
        :return: None
        """
        self.disconnect_signals()
        self._scene = new_scene
        self.connect_signals()

    @property
    def output(self) -> dict[str, Any]:
        """
        Evaluate this node or use a cached output
        :return: dict[str, Any]: dictionary with (name, value) pairs for all output entries
        """
        # If there is no cached output, evaluate the node
        if self._output is None:
            self._run_evaluate()

        # Return the output
        return self._output

    @output.setter
    def output(self, new_output: Optional[dict[str, Any]]) -> None:
        """
        Set the cached output
        :param new_output: dictionary of (name, value) pairs for output entries
        :return: None
        """
        # If argument is None, reset cached output
        if new_output is None:
            self._output = None
            return

        # Otherwise, store the output in cache
        self._output = new_output

    def _run_evaluate(self) -> None:
        """
        Gather all node inputs and run the evaluate function to obtain the node outputs
        :return: None
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

    def _reset_outputs(self) -> None:
        """
        Reset the value of all output entries
        :return: None
        """
        for entry in self.entries:
            if entry.entry_type == Entry.TYPE_OUTPUT:
                entry.value = NoValue

    def set_output_value(self, entry: str or Entry, value: Any) -> None:
        """
        Set the value of an output entry
        :param entry: (name of) output entry
        :param value: value of output
        :return: None
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
        :return: None
        """
        for entry in self.entries:
            entry.connect_signal()

    def disconnect_signals(self) -> None:
        """
        Disconnect signals from all entries from the scene
        :return: None
        """
        for entry in self.entries:
            entry.disconnect_signal()

    def remove(self) -> None:
        """
        Remove this node
        :return: None
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
        Add an entry to the node
        :param entry: entry to add
        :return: None
        """
        if entry.name in self.entry_names():
            raise ValueError(f'An entry with the name "{entry.name}" already exists')

        self.entries.append(entry)
        entry.node = self

    def add_entries(self, entries: Iterable[Entry]) -> None:
        """
        Add multiple entries to the node
        :param entries: iterable of entries to add
        :return: None
        """
        for entry in entries:
            self.add_entry(entry)

    def insert_entry(self, entry: Entry, index: int) -> None:
        """
        Insert an entry into the node at a specific index
        :param entry: entry to add
        :param index: index to insert at
        :return: None
        """
        if entry.name in self.entry_names():
            raise ValueError(f'An entry with the name "{entry.name}" already exists')

        self.entries.insert(index, entry)
        entry.node = self

    def insert_entries(self, entries: Iterable[Entry], index: int) -> None:
        """
        Insert multiple entries into the node at a specified index
        :param entries: iterable of entries to add
        :param index: index to insert at
        :return: None
        """
        for i, entry in enumerate(entries):
            self.insert_entry(entry, index + i)

    def index(self, entry: str or Entry) -> int:
        """
        Get the index of the entry in the node (0=top-most, ...)
        :param entry: (name of) entry to find index of
        :return: int: index of the entry
        """
        if isinstance(entry, str):
            entry = self.get_entry(entry)
        return self.entries.index(entry)

    @overload
    def remove_entry(self, name: str) -> None:
        """
        Remove an entry from the node by name
        :param name: name of the entry to remove
        :return: None
        """

    @overload
    def remove_entry(self, entry: Entry) -> None:
        """
        Remove an entry from the node
        :param entry: entry to remove
        :return: None
        """

    def remove_entry(self, entry) -> None:
        """
        Implementation of remove entry function
        :param entry: entry to remove (or its name)
        :return: None
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
        Remove all entries from the node
        :return: None
        """
        while len(self.entries) > 0:
            entry = self.entries.pop(0)
            entry.remove()

    def update_entries(self) -> None:
        """
        Update the position and width of all entries in the node
        :return: None
        """
        for entry in self.entries:
            entry.update_geometry()

    def entry_names(self) -> list[str]:
        """
        Get a list of names for all entries
        :return: list[str]: list of names
        """
        return [entry.name for entry in self.entries]

    def get_entry(self, name: str) -> Entry:
        """
        Get an entry by name
        :param name: name of entry
        :return: None
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
        Add a new value box entry to the node
        :param name: name of the entry
        :param entry_type: type of entry (Entry.TYPE_INPUT, Entry.TYPE_STATIC, or Entry.TYPE_OUTPUT)
        :param value: initial value of the value box
        :param minimum: minimum value of the value box
        :param maximum: maximum value of the value box
        :param value_type: type of value (int or float)
        :return: None
        """
        entry = ValueBoxEntry(name, entry_type, value, minimum, maximum, value_type,
                              theme=self.graphics.theme)
        self.add_entry(entry)

    def add_value_input(self, name: str, value: int or float = 0,
                        minimum: int or float = -100, maximum: int or float = 100,
                        value_type: Type[int] or Type[float] = float) -> None:
        """
        Add a new value box input to the node
        :param name: name of the input
        :param value: initial value of the value box
        :param minimum: minimum value of the value box
        :param maximum: maximum value of the value box
        :param value_type: type of value (int or float)
        :return: None
        """
        self.add_value_entry(name, Entry.TYPE_INPUT, value, minimum, maximum, value_type)

    def add_value_output(self, name: str, value: int or float = 0,
                         minimum: int or float = -100, maximum: int or float = 100,
                         value_type: Type[int] or Type[float] = float) -> None:
        """
        Add a new value box output to the node
        :param name: name of the output
        :param value: initial value of the value box
        :param minimum: minimum value of the value box
        :param maximum: maximum value of the value box
        :param value_type: type of value (int or float)
        :return: None
        """
        self.add_value_entry(name, Entry.TYPE_OUTPUT, value, minimum, maximum, value_type)

    def add_label_entry(self, name: str, entry_type: int = Entry.TYPE_STATIC) -> None:
        """
        Add a new label entry to the node
        :param name: name of the entry
        :param entry_type: type of entry (Entry.TYPE_INPUT, Entry.TYPE_STATIC, or Entry.TYPE_OUTPUT)
        :return: None
        """
        entry = LabeledEntry(name, entry_type, self.graphics.theme)
        self.add_entry(entry)

    def add_label_input(self, name: str) -> None:
        """
        Add a new label input to the node
        :param name: name of the input
        :return: None
        """
        self.add_label_entry(name, Entry.TYPE_INPUT)

    def add_label_output(self, name: str) -> None:
        """
        Add a new label output to the node
        :param name: name of the output
        :return: None
        """
        self.add_label_entry(name, Entry.TYPE_OUTPUT)

    def add_combo_box_entry(self, name: str, items: Iterable[str] or dict[str, Any] = None) -> None:
        """
        Add a new combo box entry to the node
        :param name: name of the entry
        :param items: items to add to the combo box (either only texts or (text, data) pairs)
        :return: None
        """
        entry = ComboBoxEntry(name, items=items)
        self.add_entry(entry)

    def __getitem__(self, item: int or str) -> Entry:
        """
        Get an entry in the node by name or index
        :param item: name or index of entry to get
        :return: Entry: retrieved entry
        """
        if isinstance(item, str):
            return self.get_entry(item)
        if isinstance(item, int):
            return self.entries[item]
        raise TypeError(f'Cannot get item, type "{type(item)}" not supported')

    def __delitem__(self, key: int or str) -> None:
        """
        Remove an entry from the node by name or index
        :param key: name or index of entry to remove
        :return: None
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
        Check whether this node contains an entry
        :param item: entry or name of entry
        :return: bool: whether specified entry exists in the node
        """
        if isinstance(item, str):
            return item in self.entry_names()
        return item in self.entries

    def __len__(self) -> int:
        """
        Get the number of entries in this node
        :return: int: number of node entries
        """
        return len(self.entries)

    def __str__(self) -> str:
        """
        Get a string representation of the node
        :return: str: string representation of the node
        """
        return f"<Node '{self.title}' with {len(self)} entries>"

    def sockets(self) -> list['Socket']:
        """
        Get a list of all sockets in the node
        :return: list[Socket]: list of sockets
        """
        result = []
        for entry in self.entries:
            if entry.socket is not None:
                result.append(entry.socket)
        return result

    def save(self) -> dict:
        """
        Override to save any additional values to the node state
        :return: dict: representation of additional values to save (has to be JSON-safe)
        """
        return {}

    def load(self, state: dict) -> bool:
        """
        Override to load any saved additional values from the node state (as saved in save())
        :param state: representation of saved additional values to load
        :return: bool: whether setting state succeeded
        """
        return True

    def get_state(self) -> dict:
        """
        Get the state of the node as a dictionary
        :return: dict: representation of the node state
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
        Set the state of the node from a dictionary
        :param state: representation of the node state
        :param restore_id: whether to restore the object id from state
        :return: bool: whether setting state succeeded
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
