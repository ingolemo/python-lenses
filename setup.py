import setuptools
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'readme.md')) as handle:
    long_desc = handle.read()

setuptools.setup(
    name='lenses',
    version='0.1.0',
    description='A lens library for python',
    long_description=long_desc,
    url='https://github.com/ingolemo/python-lenses',
    author='Adrian Room',
    author_email='<ingolemo@gmail.com>',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='lens lenses immutable functional',
    packages=setuptools.find_packages(exclude=['tests']),
    install_requires=[
        'singledispatch',
    ],
    extras_require={
        'test': ['coverage', 'hypothesis'],
    },
)
