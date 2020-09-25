rm dist/*
python setup.py sdist bdist_wheel
#python -m twine upload --repository testpypi dist/*
python -m twine upload --skip-existing dist/*