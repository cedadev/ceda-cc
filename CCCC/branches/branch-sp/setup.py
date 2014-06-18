# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys, os

setup(name='ceda_cc',
      version='0.1',
      description="CEDA Conformance Checker",
      #long_description="",
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 2.6',
        ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Martin Juckes',
      author_email='Martin.Juckes@stfc.ac.uk',
      #url='',
      #download_url=''
      license='BSD',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      # We won't manage dependencies here for now.
      #install_requires=[
      #],
      entry_points= {
        'console_scripts': ['ceda-cc = ceda_cc.c4:main_entry'],
        },
      )
