# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys, os
import ceda_cc
from ceda_cc.versionConfig import version, versionComment

# Load long_description from README.txt
here = os.path.dirname(__file__)
readme_txt = os.path.join(here, 'README.md')
long_description = '\n\n' + open(readme_txt).read()

setup(name='ceda-cc',
      version=version,
      description="CEDA Conformance Checker",
      long_description=long_description,
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3',
        ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Martin Juckes',
      author_email='Martin.Juckes@stfc.ac.uk',
      url='https://github.com/cedadev/ceda-cc',
      #download_url=''
      license='BSD',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      # We won't manage dependencies here for now.
      #install_requires=[
      #],
      entry_points= {
        'console_scripts': ['ceda-cc=ceda_cc.c4:main_entry',
                          'ceda-cc-nco=ceda_cc.amap2nco:main_entry'],
        },
      )
