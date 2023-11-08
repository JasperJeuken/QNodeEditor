"""
Module containing custom extension of QLabel with node editor theme
"""
# pylint: disable = no-name-in-module
from PyQt5.QtWidgets import QLabel

from QNodeEditor.themes import ThemeType, DarkTheme


class Label(QLabel):
    """
    Custom QLabel with node editor theme styling
    """

    def __init__(self, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Create a new themed label

        Parameters
        ----------
        theme : Type[:py:class:`~QNodeEditor.themes.theme.Theme`], optional
            Theme for the label (default: :py:class:`~QNodeEditor.themes.dark.DarkTheme`)
        """
        super().__init__(*args, **kwargs)
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get or set the current label theme.
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        self._theme = new_theme

        # Create and apply new style sheet
        style_sheet = f"""
            QLabel {{
                color: {new_theme.widget_color_text.name()};
                background: transparent;
            }}
        """
        self.setStyleSheet(style_sheet)
        self.setFont(self.theme.font())
        self.setFixedHeight(new_theme.widget_height)
