USAGE
-----

From the command line:
----------------------

Required arguments:

python ceda_cc/c4.py -p <project> -D <directory>  ## check all files in directory tree, for project in SPECS, CORDEX, CCMI, CMIP5.
python ceda_cc/c4.py -p <project> -d <directory>  ## check all files in directory
python ceda_cc/c4.py -p <project> -f <file>       ## check a single file.
python ceda_cc/c4.py --copy-config <dest-dir>     ## copy the default configuration directory to <dest-dir> to enable customisation.

Optional arguments:

  --ld <log file directory>  ## directory to take log files;
  -R <record file name> ## file name for file to take one record per file checked;
  --cae                 ## "catch all errors": will trap exceptions and record
                             in  log files, and then continue. Default is to
                            stop after unrecognised exceptions.
  --log <single|multi>  ## Set log file management option -- see "Single log" and "Multi-log" below.
  --blfmode <mode>      # set mode for batch log file -- see log file modes
  --flfmode <mode>      # set mode for file-level log file -- see log file modes
  --aMap                # Read in some attribute mappings and run tests with virtual substitutions, see also amap2nco.py

Environment variables:

  CC_CONFIG_DIR  ## Set to the location of a custom configuration directory.  If unset the default configuration will be used.

After running:

The log file directory may contain hundreds of files with reports of errors. To get a summary, run:

python summary.py <log file directory>

This will produce a listing of errors, the number of times they occur and up to two of the files which contain the error. It is hoped that inspection of one or 2 files will provide enough information to trace the problems which lead to the error reports.

python summary.py -html <log file directory>

This will create a set of html files in the "html" directory, which can be viewed through a browser (enter file://<path to html directory into your browser).

Installing as a package:
------------------------

You can also install the code into your Python environment and then use the "ceda-cc" command to invoke c4.py with the same arguments ans described above.

 1. If you have "pip" installed simply execute:
    $ pip install ceda-cc
    or after downloading the tarball
    $ pip install ceda-cc-$VERSION.tar.gz

 2. If you have the setuptools package you can execute the following from the distribution directory:
    $ python setup.py install

If you install ceda-cc in this way you can use the --copy-config command to export the default configuration into a directory where you can edit the configuration.


Called from python:
------------------
The code can also be called from a python script:

from ceda_cc import c4
m = c4.main( args=argList )     # argList is a python list of command line arguments
if not m.ok:
  print 'check failed'
else:
  print 'success'
  print 'DRS dictionary:', m.cc.drs    # print drs of last file checked -- not useful in multiple file mode.

e.g.
m = c4.main( args=[ '-p', 'CORDEX', '-f', dataFilePath, '--ld', logFileDirectory] )
## run checks on a single file located at dataFilePath, and write logs to logFileDirectory

DEPENDENCIES
------------

The library can uses the cdms2, python-netCDF4 or Scientific module to read NetCDF files.
By default, it will use the cdms2 module if available. Support for the netCDF4 and Scientific modules has been added recently.
To change the default, change the order in which modules are listed in the "supportedNetcdf" list in file_utils.py

Is available as part of the cdat-lite package (http://proj.badc.rl.ac.uk/cedaservices/wiki/CdatLite ).
For python-netCDF4, see http://code.google.com/p/netcdf4-python/.
For Scientific see http://dirac.cnrs-orleans.fr/plone/software/scientificpython/  . Note that search engines confuse "ScientificPython" with "SciPy". The SciPy package also contains a netcdf API, but when tested in April 2014 this could not read data from NetCDF 4 files, and so is not supported here.

OUTPUT
------

Single log (default for single file):  
  -- log of errors found and checks passed
  -- "Rec.txt" -- single record summarising results. If no errors are found, the archive directory path for the file will be in this record.

Multi-log (default for multiple files):
  -- separate log of errors for each file;
  -- summary log, 3 records per file;
  -- "Rec.txt" -- single record for each file, as above

Log file modes.
Valid modes are: 'a': append
                 'n', 'np': new file, 'np': protect after closing (mode = 444)
                 'w', 'wo': write (overwrite if present), 'wo': protect after closing (mode = 444)

Note that the log files generated in multi-log mode will re-use file names. If running with --flfmode set to 'n','np' or 'wo' it will be necessary to change or clear the target directory. The names of batch log files include the time, to the nearest second, when the process is started, so will not generally suffer from re-use.

Vocabulary lists GCMModelName.txt and RCMModelName.txt are held on the DMI CORDEX site:

  http://cordex.dmi.dk/joomla/images/CORDEX/GCMModelName.txt
  http://cordex.dmi.dk/joomla/images/CORDEX/RCMModelName.txt

To update the CMOR tables use: 
"git clone https://github.com/PCMDI/cordex-cmor-tables"

VIRTUAL MODE
------------

The virtual mode can be used to validate substituions before adjusting systems which have been used to generate data, or as the first step of a procedure for repairing some classes of errors.

To use this mode, a mapping file is needed. This can be generated by an initial run of the checker with no virtual substitutions. A file named "amapDraft.txt" will be generated. This file should be inspected to ensure that suggested changes make sense.

A typical directive will be of the form:
@var=rlus;standard_name=surface_upward_longwave_flux_in_air|standard_name=surface_upwelling_longwave_flux_in_air

The meaning is: for variable "rlus", set the attribute "standard_name" to "surface_upwelling_longwave_flux_in_air" where the input file has "surface_upward_longwave_flux_in_air".

"amapDraft.txt" should be copied to a new location before running in virtual mode. This draft will only contain directives for errors if the corect value is unique. The suggested corrections to variable attributes will make these consistent with the variable name. If the inconsistency has arisen because a variable has been given the wrong name this will exaggerate the problem rather than solving it. All changes should be checked. 

Additional directives can be added. e.g.
@;institute_id=mohc|institute_id=MOHC
will instruct the code to replace "mohc" with "MOHC" in the global attribute "institute_id".

If run with the --aMap flag, the checker will test attributes after making virtual substituions. I.e. there are no changes made to the files at this stage, but results of the tests apply as if changes have been made.

After running in virtual mode, c4.py will generate a file named "attributeMappingsLog.txt" which contains a record for every change to every file. If the results of running in virtual mode are positive, this file can be used to create a script to modify the files, by running "amap2nco.py":

python amap2nco.py attributeMappingsLog.txt /tmp/batch1 /tmp/batch1_corrected
## this will generate a list of NCO commands in "ncoscript.sh", which will apply the changes and create new files in "/tmp/batch1_corrected".

It is recommended that the data values in the corrected files should be checked after running this script.

By default, the amap2nco.py program will generate commands to modify the tracking_id and creation_date global attributes at the same time as making other changed. The "history" attribute is modified by the NCO library. 

EXCEPTIONS
----------
The exception handling is designed to ensure that problems analysing one file do not prevent testing of other files.
Traceback information is written to log file.

BUGS
----
The cmds2 library generates a data array for dimensions if there is none present in the file. Tests applied to this library generated array will generate mis-leading error messages. Within cmds2 there is no clear method of distinguishing between library generates arrays and those which exist in the data file. The solution may be to move to using the NetCDF4 module instead.

----------
