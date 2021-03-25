####################  post pypi upgrade....
##
## for local install:

# sudo python setup.py install --force

# compile egg etc (inc. wheel)
python setup.py sdist bdist_wheel

python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
#python -m twine upload --repository-url  https://upload.pypi.org/legacy/ dist/*
#python -m twine upload  dist/*
#python setup.py sdist upload -r https://test.pypi.org/legacy/
#python setup.py sdist upload -r https://upload.pypi.org/legacy
