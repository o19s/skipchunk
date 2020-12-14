#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'spacy==2.3.2', 
    'nltk==3.5',
    'pysolr==3.9.0',
    'elasticsearch==7.9.1',
    'Click>=6.0',
    'tqdm>=4.48',
    'requests>=2.23',
    'jsonpickle==1.4.1',
    'bs4==0.0.1',
    'lxml==4.5.2',
    'multidict==4.7.6'
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Max Irwin",
    author_email='mirwin@opensourceconnections.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8'
    ],
    description="Instant Knowledge Graphs from text documents.",
    entry_points={
        'console_scripts': [
            'skipchunk=skipchunk.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='skipchunk',
    name='skipchunk',
    packages=find_packages(include=['skipchunk']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/o19s/skipchunk',
    version='1.2.0',
    zip_safe=False,
)