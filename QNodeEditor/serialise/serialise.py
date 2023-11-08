"""
Module containing base class for serializable objects.
"""
from abc import ABCMeta, abstractmethod


class Serializable(metaclass=ABCMeta):
    """
    Base for serializable objects.

    This class is abstract and cannot be used by itself. Various node editor classes inherit from
    this class.
    """

    @abstractmethod
    def get_state(self) -> dict:
        """
        Get the state of this object as a (JSON-safe) dictionary

        Returns
        -------
        dict
            JSON-safe dictionary representing object state
        """

    @abstractmethod
    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of this object from a state dictionary.

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired object state
        restore_id : bool, optional
            Whether to restore the internal IDs of the entry sockets (used to reconnect saved edges)

        Returns
        -------
        bool
            Whether setting the object state succeeded
        """
