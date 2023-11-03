"""Serialization class for objects that are serializable"""
from abc import ABCMeta, abstractmethod


class Serializable(metaclass=ABCMeta):
    """Abstract base class for serializable objects"""

    @abstractmethod
    def get_state(self) -> dict:
        """
        Get the state of this object as a dictionary
        :return: dict: representation of object state
        """

    @abstractmethod
    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of this object based on a dictionary
        :param state: representation of object state
        :param restore_id: whether to restore the object id from state
        :return: bool: whether setting state succeeded
        """
