import os

import setuptools

here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, "readme.rst")) as handle:
        long_desc = handle.read()
except IOError:
    # the readme should get included in source tarballs, but it shouldn't
    # be in the wheel. I can't find a way to do both, so we'll just ignore
    # the long_description when installing from the source tarball.
    long_desc = None

dependencies = []

documentation_dependencies = [
    "sphinx",
]

optional_dependencies = [
    "pyrsistent",
]

test_dependencies = optional_dependencies + [
    "pytest",
    "pytest-sugar",
    "coverage",
    "pytest-coverage",
    "hypothesis",
]

lint_dependencies = optional_dependencies + [
    "ufmt",
    "flake8",
    'mypy;implementation_name=="cpython"',
]

setuptools.setup(
    name="lenses",
    version="1.1.0",
    description="A lens library for python",
    long_description=long_desc,
    url="https://github.com/ingolemo/python-lenses",
    author="Adrian Room",
    author_email="ingolemo@gmail.com",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="lens lenses immutable functional optics",
    packages=setuptools.find_packages(exclude=["tests"]),
    python_requires=">=3.7, <4",
    install_requires=dependencies,
    tests_require=test_dependencies,
    extras_require={
        "docs": documentation_dependencies,
        "optional": optional_dependencies,
        "tests": test_dependencies,
        "lints": lint_dependencies,
    },
)
