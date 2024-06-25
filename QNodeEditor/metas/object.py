"""
Module containing metaclass for classes deriving from QObject and serializable
"""
# pylint: disable = no-name-in-module
try:
    from PySide6.QtCore import QObject
except ImportError:
    from PyQt5.QtCore import QObject

from QNodeEditor.serialise import Serializable


class ObjectMeta(type(QObject), type(Serializable)):
    """
    Metaclass for classes deriving from QObject (avoids metaclass conflict)
    """
