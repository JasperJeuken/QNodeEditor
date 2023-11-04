# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'QNodeEditor'
copyright = '2023, Jasper Jeuken'
author = 'Jasper Jeuken'
release = '1.0.1'
today_fmt = '%-d %B %Y at %H:%M'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx_toolbox.sidebar_links',
              'sphinx_toolbox.github']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

github_username = 'JasperJeuken'
github_repository = 'QNodeEditor'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_sidebars = {
    '**': [
        'globaltoc.html'
    ]
}
html_last_updated_fmt = '%b %d, %Y'
html_show_sphinx = False
