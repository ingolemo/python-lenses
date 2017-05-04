#!/usr/bin/env sh

coverage run -m pytest lenses tests --doctest-modules "$@"
test "$?" = '0' || exit

python -m doctest readme.md
test "$?" = '0' || exit

coverage report -m
