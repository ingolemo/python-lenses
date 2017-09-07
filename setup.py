import setuptools
import os

here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, 'readme.md')) as handle:
        long_desc = handle.read()
except IOError:
    # the readme should get included in source tarballs, but it shouldn't
    # be in the wheel. I can't find a way to do both, so we'll just ignore
    # the long_description when installing from the source tarball.
    long_desc = None

setuptools.setup(
    name='lenses',
    version='0.2.1',
    description='A lens library for python',
    long_description=long_desc,
    url='https://github.com/ingolemo/python-lenses',
    author='Adrian Room',
    author_email='ingolemo@gmail.com',
    license='GPLv3+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='lens lenses immutable functional optics',
    packages=setuptools.find_packages(exclude=['tests']),
    install_requires=['singledispatch', 'typing;python_version<"3"'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'coverage', 'hypothesis', 'mypy'],
)
