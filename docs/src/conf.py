#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys


os.environ["PROJECT_ROOT"] = os.path.abspath("../..")

# Add the project
sys.path.insert(0, os.path.abspath("../.."))

# Add the extensions
sys.path.insert(0, os.path.join(os.path.abspath("."), "_exts"))

# -- Project information -----------------------------------------------------

project = "os-migrate"
copyright = "2020, os-migrate"
author = "os-migrate"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx_rtd_theme", "sphinx.ext.autodoc", "ansible-autodoc"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

master_doc = "index"

# The suffix of source filenames.
source_suffix = ".rst"

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "native"

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
# html_theme = '_theme'
# html_static_path = ['static']

# html_favicon = "favicon.ico"
# html_logo = "logo.png"
# html_theme_options = {
#     'logo_only': True,
#     'display_version': False,
# }

# Output file base name for HTML help builder.
htmlhelp_basename = "%sdocs" % project
html_theme = "sphinx_rtd_theme"

# Comment out or remove the following block if you do not need to load module_utils
from ansible.plugins.loader import init_plugin_loader, module_utils_loader

init_plugin_loader()

needed_module_utils = ["module_1", "module_2"]

# load our custom module_utils so that modules can be imported for
# generating docs
for m in needed_module_utils:
    try:
        module_utils_loader.get(m)
    except AttributeError:
        pass
