# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'FabSim3'
copyright = '2020, Derek Groen, Hamid Arabnejad, Robin Richardson, Robert Sinclair, Vytautas Jancauskas, Nicolas Monnier, Paul Karlshoefer, Peter Coveney, , Maxime Vassaux'
author = 'Derek Groen, Hamid Arabnejad, Robin Richardson, Robert Sinclair, Vytautas Jancauskas, Nicolas Monnier, Paul Karlshoefer, Peter Coveney, Maxime Vassaux'

# The short X.Y version
version = ''
# The full version, including alpha/beta/rc tags
release = 'Initial Release'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
master_doc = 'index'


# -- Options for HTML output -------------------------------------------------

html_logo = "../logo.jpg"


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'FabSim3doc'


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'fabsim3', 'FabSim3 Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'FabSim3', 'FabSim3 Documentation',
     author, 'FabSim3', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# https://pypi.org/project/msmb_theme/
html_theme = 'msmb_theme'
import msmb_theme
html_theme_path = [msmb_theme.get_html_theme_path()]


# sphinx-build -T -E -b readthedocs -d build/doctrees source build/html
