# HOW TO RELEASE!
# 1. Decide on the {semver} version number (i.e. 1.2.3)
# 2. Change setup.py::setup(version={semver})
# 3. Change setup.cfg::current_version = {semver})
# 4. Add the changes to a new {semver} heading in HISTORY.rst
# 5. Add any additional authors to AUTHORS.rst
# 6. Go and run this script!

mv dist/* ./dist.old/
python convert_md_2_rst.py
python setup.py sdist bdist_wheel
python -m twine upload --skip-existing dist/*