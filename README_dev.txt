

Documentation
-------------
#01.001: Need to create a clearer description of what each class is intended to do.  

Unit testing
------------
&02.001: Create some unit tests (dependent on #001).  Done
&02.002: Create a __dummy project, to support testing of logging system etc. DOne
   --- added to mip vocabs and config -- need to pt something in the NetCDF file reader.
&02.003: Make sure S2 unit tests can capture and report exceptions that get passed to log files Done

Configuration
-------------
&03.001: Put project dependent information into a specific class instance -- projectConfig. Done (Dec 5th)
&03.002: Merge back version configured for SPECS -- [Martin, 18th Oct] 
&03.003: Create basic configuration for CMIP5 and run to exercise code and identify problems.
#03.004: Clean up special case for CORDEX in domain checks (allowing 2nd formulation for Antarctica, as it is cyclic)
#03.005: Extend checkByVar to SPECS and CCMI data **URGENT** -- to look for overlaps
&03.006: Add CCMI configuration
&03.007: Complete SPECS configuration (additional global attributes) Done

Organisation of files
---------------------
#04.001: Move checking classes into a seperate file -- to make it easier for different people to work on different parts of the code.  -- [Martin, 18th Oct]
#04.002: Move class definitions out of the c4.py script.

Compatibility with archive
----------
## see also 03.005
#05.001: Vocabulary terms for compatibility errors.
#05.002: Add "--target" option, and method to scan latest file names.
#05.003: Add option to check for overlaps in time range in archive
#05.004: Add retraction configuration script and associated check against target
#05.005: Unit tests for all compatibility checks.

#06.001: Version control tag in project: project variable --> namedTuple



Issues:
ECMWF found a HDF warning which raised an exception. Suppressed by setting the environment variable HDF5_DISABLE_VERSION_CHECK=1. Reason for this unclear -- probably local library issues.
