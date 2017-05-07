#!/usr/bin/env sh

if which mypy >/dev/null 2>&1; then
	mypy -m lenses
	test "$?" = '0' || exit
fi

coverage run -m pytest lenses tests --doctest-modules "$@"
test "$?" = '0' || exit

python -m doctest readme.md
test "$?" = '0' || exit

coverage report -m
