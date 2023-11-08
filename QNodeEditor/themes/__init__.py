"""
Module containing graphical themes for all node editor elements.

The package comes with two themes:

- :py:class:`~.dark.DarkTheme`: dark theme
- :py:class:`~.light.LightTheme`: light theme

To set the theme for an entire node scene, use the
:py:attr:`~QNodeEditor.graphics.view.NodeView.theme` property of a
:py:class:`~QNodeEditor.graphics.view.NodeView` the scene is displayed in.

Both the :py:class:`~QNodeEditor.dialog.NodeEditorDialog` and
:py:class:`~QNodeEditor.editor.NodeEditor` have ``theme`` properties that can also be used to set
the theme of a node editor.

Examples
--------
To define your own theme, derive a class from :py:class:`~.theme.Theme` and set all the properties:

.. code-block:: python

    from PyQt5.QtGui import QColor


    class MyTheme(Theme):

        # Editor properties
        editor_color_background = QColor('#ff0000')
        editor_color_grid = QColor('#00ff00')
        font_size = 10
        ...

See the :py:class:`~.theme.Theme` class for all properties that need to be set.

Once you created a theme, use the :py:attr:`~QNodeEditor.graphics.view.NodeView.theme` property of a
:py:class:`~QNodeEditor.graphics.view.NodeView` to apply your theme:

.. code-block:: python

    # For a new scene
    theme = MyTheme
    scene = NodeScene()
    view = NodeView(scene, MyTheme)

    # For an existing scene
    view.theme = MyTheme

    # Inside of the node editor widget
    editor = NodeEditor()
    editor.theme = MyTheme

    # Inside of the node editor dialog
    dialog = NodeEditorDialog()
    dialog.theme = MyTheme

Note that you do not need to create an instance of the theme class.

"""
from .theme import ThemeType
from .dark import DarkTheme
from .light import LightTheme
