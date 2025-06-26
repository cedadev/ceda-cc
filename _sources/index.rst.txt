.. ceda-cc documentation master file, created by
   sphinx-quickstart on Wed Mar  4 10:21:58 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The ceda-cc file compliance checker: technical documentation 
=============================================================

.. toctree::
   :maxdepth: 2

Usage (ccinit)
===============

Calling options
---------------

=============================================  ==========================================================
Command line                                   Description
=============================================  ==========================================================
ceda-cc -p <project> -D <directory>  [..]      check all data in directory tree under specified directory
ceda-cc -p <project> -d <directory>  [..]      check all data in specified directory
ceda-cc -p <project> -f <file>       [..]      check a single file 
ceda-cc --sum <log file directory>   [..]      create an overview of results
ceda-cc --copy-config  <target diectory> [..]  copy configuration files to a new directory
=============================================  ==========================================================

.. automodule:: ceda_cc.ccinit
   :members:

c4
===============

.. automodule:: ceda_cc.c4
   :members:


c4_run
===============

.. automodule:: ceda_cc.c4_run
   :members:


config_c4
===============

.. automodule:: ceda_cc.ceda_cc_config.config_c4
   :members:


utils_c4
===============

.. automodule:: ceda_cc.utils_c4
   :show-inheritance:
   :members:

file_utils
===============

.. automodule:: ceda_cc.file_utils
   :show-inheritance:
   :members:

xceptions
=========

.. automodule:: ceda_cc.xceptions
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

