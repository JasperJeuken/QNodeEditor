"""
Metaclass for classes deriving from QGraphicsPathItem and ABC meta
"""
# pylint: disable = no-name-in-module
from abc import ABCMeta

try:
    from PySide6.QtWidgets import QGraphicsPathItem
except ImportError:
    from PyQt5.QtWidgets import QGraphicsPathItem


class GraphicsPathItemMeta(type(QGraphicsPathItem), ABCMeta):
    """
    Metaclass for classes deriving from QGraphicsPathItem (to avoid PyQt metaclass conflict)
    """
