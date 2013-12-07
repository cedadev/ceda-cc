

Documentation
-------------
#01.001: Need to create a clearer description of what each class is intended to do.

Unit testing
------------
#02.001: Create some unit tests (dependent on #001).
#02.002: Create a __dummy project, to support testing of logging system etc.
   --- added to mip vocabs and config -- need to pt something in the NetCDF file reader.
#02.003: Make sure S2 unit tests can capture and report exceptions that get passed to log files

Configuration
-------------
#03.001: Put project dependent information into a specific class instance -- projectConfig. Done (Dec 5th)
#03.002: Merge back version configured for SPECS -- [Martin, 18th Oct]
#03.003: Create basic configuration for CMIP5 and run to exercise code and identify problems.
#03.004: Clean up special case for CORDEX in domain checks (allowing 2nd formulation for Antarctica, as it is cyclic)
#03.005: Extend checkByVar to SPECS and CCMI data
#03.006: Add CCMI configuration
#03.007: Complete SPECS configuration (additional global attributes)

Organisation of files
---------------------
#04.001: Move checking classes into a seperate file -- to make it easier for different people to work on different parts of the code.  -- [Martin, 18th Oct]
#04.002: Move class definitions out of the c4.py script.




