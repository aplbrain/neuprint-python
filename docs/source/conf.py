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
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../..'))

import inspect
import neuprint
from os.path import relpath, dirname

import versioneer
import numpydoc

# -- Project information -----------------------------------------------------

project = 'neuprint-python'
copyright = '2019, FlyEM'
author = 'FlyEM'

# The short X.Y version
os.chdir(os.path.dirname(__file__) + '/../..')
version = versioneer.get_version()
os.chdir(os.path.dirname(__file__))

# The full version, including alpha/beta/rc tags
release = version

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    #'sphinx.ext.viewcode', # Link to sphinx-generated source code pages.
    'sphinx.ext.linkcode',  # Link to source code on github (see linkcode_resolve(), below.)
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'IPython.sphinxext.ipython_console_highlighting',
    'IPython.sphinxext.ipython_directive',
    'nbsphinx'
]

nbsphinx_execute = 'always'
os.environ['RUNNING_IN_SPHINX'] = '1'

nbsphinx_prolog = """

..
   (The following |br| definition is the only way
   I can force numpydoc to display explicit newlines...) 

.. |br| raw:: html

   <br />

.. note::

    This page corresponds to a Jupyter notebook you can
    `try out yourself`_. |br|
    (The original version is `here`_.)
    
    .. _try out yourself: https://mybinder.org/v2/gh/connectome-neuprint/neuprint-python/master?filepath=docs%2Fsource%2F{{ env.doc2path(env.docname, base=None) }}
    
    .. _here: https://github.com/connectome-neuprint/neuprint-python/tree/master/docs/source/{{ env.doc2path(env.docname, base=None) }}

    .. image:: https://mybinder.org/badge_logo.svg
     :target: https://mybinder.org/v2/gh/connectome-neuprint/neuprint-python/master?filepath=docs%2Fsource%2F{{ env.doc2path(env.docname, base=None) }}

----
"""

# generate autosummary pages
autosummary_generate = True
autoclass_content = 'both'

# Don't alphabetically sort functions
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'nature'

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    #'source_link_position': "footer",
    #'navbar_sidebarrel': False,
    #'navbar_links': [
    #                 ("API", "src/api"),
    #                 ],

    }

# Copied from dask docs.
html_context = {
    "css_files": ["_static/theme_overrides.css"]  # override wide tables in RTD theme
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'neuprintdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'neuprint-python.tex', 'neuprint-python Documentation',
     'Philipp Schlegel', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'neuprint-python', 'neuprint-python Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'neuprint-python', 'neuprint-python Documentation',
     author, 'neuprint-python', 'One line description of project.',
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


# -- Extension configuration -------------------------------------------------

# Function courtesy of NumPy to return URLs containing line numbers
# (with edits to handle wrapped functions properly)
def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object
    """
    if domain != 'py':
        return None

    modname = info['module']
    fullname = info['fullname']

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split('.'):
        try:
            obj = getattr(obj, part)
        except:
            return None

    obj = inspect.unwrap(obj)

    try:
        fn = inspect.getsourcefile(obj)
    except:
        fn = None
    if not fn:
        return None

    try:
        _source, lineno = inspect.findsource(obj)
    except:
        lineno = None

    if lineno:
        linespec = "#L%d" % (lineno + 1)
    else:
        linespec = ""

    fn = relpath(fn, start=dirname(neuprint.__file__))

    if '.g' in neuprint.__version__:
        return ("https://github.com/connectome-neuprint/neuprint-python/blob/"
                "master/neuprint/%s%s" % (fn, linespec))
    else:
        return ("https://github.com/connectome-neuprint/neuprint-python/blob/"
                "%s/neuprint/%s%s" % (neuprint.__version__, fn, linespec))