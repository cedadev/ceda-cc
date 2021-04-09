USAGE
-----

From the command line:
----------------------

- `ceda-cc -p <project> -D <directory>`  ## check all files in directory tree, for project in SPECS, CORDEX, CCMI, CMIP5, ccmi2022.
- `ceda-cc -p <project> -d <directory>`  ## check all files in directory
- `ceda-cc -p <project> -f <file>`       ## check a single file.
- `ceda-cc --copy-config <dest-dir>`     ## copy the default configuration directory to `<dest-dir>` to enable customisation.
- `ceda-cc -h`                           ## print help text

From the source code:
---------------------

- `python -m ceda_cc.c4 -p <project> -D <directory>`  ## check all files in directory tree, for project in SPECS, CORDEX, CCMI, CMIP5, ccmi2022.
- `python -m ceda_cc.c4 -p <project> -d <directory>`  ## check all files in directory
- `python -m ceda_cc.c4 -p <project> -f <file>`       ## check a single file.
- `python -m ceda_cc.c4 --copy-config <dest-dir>`     ## copy the default configuration directory to `<dest-dir>` to enable customisation.



