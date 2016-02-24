coverage run -m pytest lenses tests --doctest-modules "$@"
if [ "$?" = '0' ]; then
	coverage report -m
fi
