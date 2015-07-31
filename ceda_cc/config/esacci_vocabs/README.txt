
Configuration for new CCI datasets.
-----------------------------------
The "extraAtts.txt" and "variableInFile.txt" files need to be editted.

Each line in the extraAtts.txt file is of the form:
<naming_authority>, <id>, <key1>=<value1>[, <key2>=<value2>]

Addtional keys/value pairs can be added, but the main purpose is to specify the algorithm and frequency, which cannot be derived automatically from the data files.

"naming_authority" and "id" are global attributes in the NetCDF files, and the ESA CCI specification states that the combination of these two should be unique for each data product. If this is not the case, there are some additional options which can be used in order to create a line in "extraAtts.txt" which corresponds to a single data product. 

Where possible, the frequency value should use the same words as used for the frequency of other products.

The algorithm should be a single word which gives a clue as to the main processing step.

The "variableInFile.txt" documents the link between the product name used in the file names and the variables in the file. Each line is of the form:
<product name in file name> <variable name in file> <standard name>

This information should be gathered by inspecting one file, and the checker will ensure that all files are consistent.


