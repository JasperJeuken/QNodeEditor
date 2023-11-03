"""Metaclass for classes deriving from QObject and serializable"""
# pylint: disable = no-name-in-module
from PyQt5.QtCore import QObject

from QNodeEditor.serialise import Serializable


class ObjectMeta(type(QObject), type(Serializable)):
    """Metaclass for classes deriving from QObject (avoids metaclass conflict)"""
