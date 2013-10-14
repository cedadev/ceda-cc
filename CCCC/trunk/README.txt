USAGE
-----

Required arguments:

python c4.py -D <directory>  ## check all files in directory tree
python c4.py -d <directory>  ## check all files in directory
python c4.py -f <file>       ## check a single file.

Optional arguments:

  --ld <log file directory>  ## directory to take log files;
  -R <record file name> ## file name for file to take one record per file checked;

OUTPUT
------

For single file:  
  -- log of errors found and checks passed
  -- "Rec.txt" -- single record summarising results. If no errors are found, the archive directory path for the file will be in this record.

For multiple files:
  -- separate log of errors for each file;
  -- summary log, 3 records per file;
  -- "Rec.txt" -- single record for each file, as above

VOCABULARIES
------------

Vocabulary lists GCMModelName.txt and RCMModelName.txt are held on the DMI CORDEX site:

  http://cordex.dmi.dk/joomla/images/CORDEX/GCMModelName.txt
  http://cordex.dmi.dk/joomla/images/CORDEX/RCMModelName.txt




