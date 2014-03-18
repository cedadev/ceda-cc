USAGE
-----

From the command line:
----------------------

Required arguments:

python c4.py -p <project> -D <directory>  ## check all files in directory tree, for project in SPECS, CORDEX, CCMI.
python c4.py -p <project> -d <directory>  ## check all files in directory
python c4.py -p <project> -f <file>       ## check a single file.

Optional arguments:

  --ld <log file directory>  ## directory to take log files;
  -R <record file name> ## file name for file to take one record per file checked;
  --cae                 ## "catch all errors": will trap exceptions and record
                             in  log files, and then continue. Default is to
                            stop after unrecognised exceptions.
  --log <single|multi>  ## Set log file management option -- see "Single log" and "Multi-log" below.
  --blfmode <mode>      # set mode for batch log file -- see log file modes
  --flfmode <mode>      # set mode for file-level log file -- see log file modes


Called from python:
------------------
The code can also be called from a python script:

import c4
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

The library uses the cmds2 module to read NetCDF files.

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
"git clone git://uv-cdat.llnl.gov/gitweb/cordex-cmor-tables.git"

EXCEPTIONS
----------
The exception handling is designed to ensure that problems analysing one file do not prevent testing of other files.
Traceback information is written to log file.

BUGS
----
The cmds2 library generates a data array for dimensions if there is none present in the file. Tests applied to this library generated array will generate mis-leading error messages. Within cmds2 there is no clear method of distinguishing between library generates arrays and those which exist in the data file. The solution may be to move to using the NetCDF4 module instead.

----------
