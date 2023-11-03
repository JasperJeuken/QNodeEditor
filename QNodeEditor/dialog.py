"""Dialog containing a node editor and interaction buttons"""
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
    """Node editor dialog containing a node editor and interaction buttons"""

    def __init__(self, parent: QWidget = None, theme: ThemeType = DarkTheme):
        """
        Create a node editor and set the layout of the dialog
        :param parent: parent widget
        :param theme: node editor dialog theme
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
        self.status_layout = QHBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.addWidget(QLabel(''))

        # Create dialog buttons
        button_layout = QHBoxLayout()
        button_cancel = QPushButton('Cancel')
        button_calculate = QPushButton('Calculate')
        button_cancel.clicked.connect(self.reject)
        button_calculate.clicked.connect(self.calculate)
        button_calculate.setDefault(True)
        button_layout.addWidget(button_cancel)
        button_layout.addWidget(button_calculate)

        # Create horizontal layout below the node editor
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(11, 0, 11, 8)
        bottom_layout.addLayout(self.status_layout, 1)
        bottom_layout.addLayout(button_layout)
        layout.addLayout(bottom_layout)

        # Set dialog theme
        self.theme: ThemeType = theme

    def calculate(self) -> None:
        """
        Evaluate the node editor scene and return as the dialog result (if no error occurred)
        :return: None
        """
        # Disable the node editor
        self.editor.view.setDisabled(True)

        # Show a label in the status layout
        self._clear_status()
        self.status_layout.addWidget(QLabel('Evaluating node scene...'))

        # Start evaluation
        self.editor.scene.evaluate()

    def _handle_result(self, result: dict[str, Any]) -> None:
        """
        If the evaluation was successful, store the result and close the dialog
        :param result: evaluation result
        :return: None
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
        If the evaluation resulted in an error, show the error and a details button
        :param error: error that occurred during evaluation
        :return: None
        """
        # Add an 'Error' title to the status
        self._clear_status()
        error_title = QLabel('Error:')
        error_title.setStyleSheet('QLabel { color: red; }')
        self.status_layout.addWidget(error_title)

        # Add the short error title to the status
        font_metrics = QFontMetrics(self.font())
        elided_error = font_metrics.elidedText(str(error), Qt.ElideRight, int(0.5 * self.width()))
        self.status_layout.addWidget(QLabel(elided_error))

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
        self.status_layout.addWidget(details_button)

        self.status_layout.addStretch()
        self.editor.view.setDisabled(False)

    def _clear_status(self) -> None:
        """
        Clear the status layout
        :return: None
        """
        clear_layout(self.status_layout)

    @property
    def theme(self) -> ThemeType:
        """
        Get the current node editor dialog theme
        :return: ThemeType: current theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new theme for the node editor dialog
        :param new_theme: new theme
        :return: None
        """
        self._theme = new_theme
        self.editor.view.theme = new_theme

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Prevent pressing return/enter from closing dialog
        :param event: key press event
        :return: None
        """
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            return event.accept()
        super().keyPressEvent(event)
