"""Class handling history for node scenes"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene


class History:
    """Class that handles state history for node scenes"""

    def __init__(self, scene: 'NodeScene', enabled: bool = True):
        """
        Store the scene the history is associated with
        :param scene: node scene history management is for
        :param enabled: whether storing/restoring history is enabled
        """
        self.scene: 'NodeScene' = scene
        self.enabled: bool = enabled

        # Set tracking variables
        self._stack: list[dict] = [self.scene.get_state()]
        self._current_step: int = 0
        self._limit: int = 32

    def undo(self) -> None:
        """
        Revert the last change
        :return: None
        """
        # Only undo if history is enabled
        if not self.enabled:
            return

        # Move one step back in the stack (if possible)
        if self._current_step > 0:
            self._restore()
            self._current_step -= 1

    def redo(self) -> None:
        """
        Restore the last undo
        :return: None
        """
        # Only redo if history is enabled
        if not self.enabled:
            return

        # Move one step forward in the stack (if possible)
        if self._current_step < len(self._stack) - 1:
            self._current_step += 1
            self._restore()

    def store_change(self, description: str) -> None:
        """
        Store a new stamp in the history stack with a description of the changes in it
        :param description: description of the change for this stamp
        :return: None
        """
        # Only store state if history is enabled
        if not self.enabled:
            return

        # Clear any history after the current step
        if self._current_step < len(self._stack) - 1:
            self._stack = self._stack[:self._current_step - 1]

        # Remove the last element if the history stack limit is reached
        if self._current_step >= self._limit - 1:
            self._stack = self._stack[1:]
            self._current_step -= 1

        # Add a new stamp to the stack
        self._stack.append(self._create_stamp(description))
        self._current_step += 1

    def descriptions(self) -> list[str]:
        """
        Get a list of the descriptions of the changes in the history stack
        :return: list[str]: list of history change descriptions
        """
        return [stamp['description'] for stamp in self._stack]

    def reset(self) -> None:
        """
        Clear the history of all stamps and store current state
        :return: None
        """
        self._stack = [self.scene.get_state()]
        self._current_step = 0

    def _create_stamp(self, description: str) -> dict:
        """
        Add a new snapshot to the history stack with a description of the change
        :param description: description of the change for this stamp
        :return: dict: new history stamp
        """
        return {
            'description': description,
            'snapshot': self.scene.get_state()
        }

    def _restore(self) -> None:
        """
        Restore the current step to the scene
        :return: None
        """
        stamp: dict = self._stack[self._current_step]
        self.scene.set_state(stamp['snapshot'], reset_history=False)
