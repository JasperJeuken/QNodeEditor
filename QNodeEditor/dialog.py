"""
Dialog containing a node editor with result handling.

This module contains a class derived from QDialog. The dialog contains a node editing scene and
handling for results and errors. The dialog is successfully executed when the node scene evaluation
succeeds. Any errors that occur are caught and displayed to the user.
"""
# pylint: disable = no-name-in-module
from typing import Optional, Any
import traceback

from PyQt5.QtWidgets import (QDialog, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QKeyEvent

from QNodeEditor.editor import NodeEditor
from QNodeEditor.themes import ThemeType, DarkTheme
from QNodeEditor.util import clear_layout


class NodeEditorDialog(QDialog):
    """
    Dialog containing a node editor and handling buttons

    This dialog houses a node editor and provides an easy way to evaluate scenes. The internal
    :py:class:`~.editor.NodeEditor` provides all the node editing capabilities, and the dialog
    handles all errors and calculation results for you. The :py:class:`~.editor.NodeEditor` can be
    accessed through the :py:attr:`~editor` attribute.

    If the scene is evaluated and no error occurs, the dialog is accepted and closes. If the dialog
    was opened using ``.exec()``, this will return ``True``. The calculation result is stored
    in the :py:attr:`~result` attribute, such that it can be accessed.

    If the scene is evaluated and an error does occur, the dialog remains open. An error message
    appears below the editor with the name of the error. Besides it is a button that opens a
    popup with the exact error traceback and further details.

    Examples
    --------
    Create a new dialog and run it using the ``.exec()`` method. Once the node scene is
    successfully evaluated, it will return ``True`` (and ``False`` otherwise). If the scene was
    evaluated, the result of the calculation can be found in the :py:attr:`~result` attribute.

    .. code-block:: python

        dialog = NodeEditorDialog()
        if dialog.exec():
            print(dialog.result)

    Attributes
    ----------
    editor : :py:class:`~.editor.NodeEditor`
        Node editor widget that shows an interactive node scene
    result : dict[str, Any] or None
        Result of the evaluated scene (``None`` if not evaluated).
        There is an item in the dictionary for each input of the selected output node. The keys are
        the names of the entries, and the values the input result that they received.
    """

    def __init__(self, parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create a new node editor dialog.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget for this dialog (if any)
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the dialog (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle('Node editor')
        self.setWindowModality(Qt.ApplicationModal)
        self.result: Optional[dict[str, Any]] = None

        # Create dialog layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Add node editor
        self.editor: NodeEditor = NodeEditor(self, theme)
        self.editor.scene.evaluated.connect(self._handle_result)
        self.editor.scene.errored.connect(self._handle_error)
        layout.addWidget(self.editor, 1)

        # Create status display
        self._status_layout = QHBoxLayout()
        self._status_layout.setContentsMargins(0, 0, 0, 0)
        self._status_layout.addWidget(QLabel(''))

        # Create dialog buttons
        button_layout = QHBoxLayout()
        button_cancel = QPushButton('Cancel')
        button_calculate = QPushButton('Calculate')
        button_cancel.clicked.connect(self.reject)
        button_calculate.clicked.connect(self._calculate)
        button_calculate.setDefault(True)
        button_layout.addWidget(button_cancel)
        button_layout.addWidget(button_calculate)

        # Create horizontal layout below the node editor
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(11, 0, 11, 8)
        bottom_layout.addLayout(self._status_layout, 1)
        bottom_layout.addLayout(button_layout)
        layout.addLayout(bottom_layout)

        # Set dialog theme
        self.theme: ThemeType = theme

    def _calculate(self) -> None:
        """
        Start the evaluation of the node editor scene.

        The result or any errors are handled by :py:meth:`_handle_result` and
        :py:meth:`_handle_error`.

        Returns
        -------
            None
        """
        # Disable the node editor
        self.editor.view.setDisabled(True)

        # Show a label in the status layout
        self._clear_status()
        self._status_layout.addWidget(QLabel('Evaluating node scene...'))

        # Start evaluation
        self.editor.scene.evaluate()

    def _handle_result(self, result: dict[str, Any]) -> None:
        """
        Handle the result of a successful node scene evaluation.

        Stores the result in the class attribute :py:attr:`result` and accepts the dialog.

        Parameters
        ----------
        result : dict[str, Any]
            Result of the node scene evaluation. (Name, value) pairs for all output node entries.

        Returns
        -------
            None
        """
        # Store the evaluation result in the dialog for later access
        self.result = result

        # Accept the dialog (and enable node editor in case dialog is opened again)
        self._state = self.editor.scene.get_state()
        self._clear_status()
        self.accept()
        self.editor.view.setDisabled(False)

    def _handle_error(self, error: Exception) -> None:
        """
        Handle any errors that occur during node scene evaluation.

        Displays the error name and adds a button that opens a popup with the error trace.

        Parameters
        ----------
        error : Exception
            The error that occurred during scene evaluation

        Returns
        -------
            None
        """
        # Add an 'Error' title to the status
        self._clear_status()
        error_title = QLabel('Error:')
        error_title.setStyleSheet('QLabel { color: red; }')
        self._status_layout.addWidget(error_title)

        # Add the short error title to the status
        font_metrics = QFontMetrics(self.font())
        elided_error = font_metrics.elidedText(str(error), Qt.ElideRight, int(0.5 * self.width()))
        self._status_layout.addWidget(QLabel(elided_error))

        # Create a dialog containing the error details
        details_dialog = QMessageBox(self)
        details_dialog.setIcon(QMessageBox.Critical)
        details_dialog.setWindowTitle('Node editor')
        details_dialog.setText('<b>An error occurred during the evaluation.</b>')
        details_dialog.setInformativeText(f"{error}\n\nClick 'Details' to view the error trace.")
        details_dialog.setDetailedText('\n'.join(traceback.format_exception(error)))
        details_dialog.findChild(QTextEdit).setFixedSize(500, 300)

        # Add a button that shows the error details
        details_button = QPushButton('Details')
        details_button.clicked.connect(details_dialog.exec)
        self._status_layout.addWidget(details_button)

        self._status_layout.addStretch()
        self.editor.view.setDisabled(False)

    def _clear_status(self) -> None:
        """
        Clear the status message layout.

        Returns
        -------
            None
        """
        clear_layout(self._status_layout)

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the theme of the node editor dialog.

        Setting the dialog theme automatically affects all child elements including the node
        editor itself.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme
        self.editor.view.theme = new_theme

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Prevent dialog from closing if return or enter is pressed. (private)

        Parameters
        ----------
        event : QKeyEvent
            Key press event

        Returns
        -------
            None

        :meta private:
        """
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            return event.accept()
        super().keyPressEvent(event)
