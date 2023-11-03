"""Custom extension of QLabel with node editor theme"""
# pylint: disable = no-name-in-module
from PyQt5.QtWidgets import QLabel

from QNodeEditor.themes import ThemeType, DarkTheme


class Label(QLabel):
    """Custom QLabel with node editor theme styling"""

    def __init__(self, *args, theme: ThemeType = DarkTheme, **kwargs):
        """
        Set the label stylesheet based on the theme
        :param theme: theme
        """
        super().__init__(*args, **kwargs)
        self.theme: ThemeType = theme

    @property
    def theme(self) -> ThemeType:
        """
        Get the current label theme
        :return: ThemeType: current label theme
        """
        return self._theme

    @theme.setter
    def theme(self, new_theme: ThemeType) -> None:
        """
        Set a new label theme
        :param new_theme: new theme
        :return: None
        """
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
