# -*- coding: utf-8 -*-
import sys
import os
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('..'))
needs_sphinx = '1.0'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
]

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
htmlhelp_basename = 'docker-wrapper-pydoc'
templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']

# General information about the project.
project = u'docker-wrapper-py'
copyright = u'2015, Fredrik Carlsen, Rolf Erik Lekang'

# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0.0'

pygments_style = 'sphinx'

latex_documents = [
    ('index', 'docker-wrapper-py.tex', u'docker-wrapper-py Documentation',
     u'Fredrik Carlsen, Rolf Erik Lekang', 'manual'),
]
man_pages = [
    ('index', 'docker-wrapper-py', u'docker-wrapper-py Documentation',
     [u'Fredrik Carlsen, Rolf Erik Lekang'], 1)
]

texinfo_documents = [
    ('index', 'docker-wrapper-py', u'docker-wrapper-py Documentation',
     u'Fredrik Carlsen, Rolf Erik Lekang', 'docker-wrapper-py', 'One line description of project.',
     'Miscellaneous'),
]
