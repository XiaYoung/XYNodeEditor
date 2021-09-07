#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

# TODO:TOX 找不到这两个文件
# with open('HISTORY.rst') as history_file:
#     history = history_file.read()

# with open('requirements.txt') as requirements_file:
#     requirements = requirements_file.read()

requirements = []

test_requirements = []

setup(
    author="XiaYoung",
    author_email='xia.young.xy@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    license="MIT license",
    # TODO:TOX 找不到这两个文件
    # long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='xynodeeditor',
    name='xynodeeditor',
    # packages=find_packages(include=['template', 'template.*']),
    packages=find_packages(include=['xynodeeditor*'], exclude=['examples*', 'tests*']),
    package_data={'': ['qss/*']},
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/xiayoung/template',
    version='0.9.0',
    zip_safe=False,
)
