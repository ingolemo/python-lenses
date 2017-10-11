#!/usr/bin/env sh

if which mypy >/dev/null 2>&1; then
	mypy -m lenses
	test "$?" = '0' || exit
fi

exec pytest \
	lenses \
	tests \
	tutorial \
	readme.md \
	--doctest-glob='*.md' \
	--doctest-modules \
	--cov
