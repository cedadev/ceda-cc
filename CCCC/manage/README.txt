

USAGE
-----

python step1.py <version> "<comment on version>"  ## updates versionConfig.py and creates "step2.sh"
bash step2.sh    ## checks trunk into repository, creates tagged version

Recommended:
-- checkout latest tag
Install with python setup.py install
ceda-cc -v    ## check version of installed package
ceda-cc --unitTest  ## check unitests of installed package
