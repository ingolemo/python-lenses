coverage run -m pytest "$@"
if [ "$?" = '0' ]; then
	coverage report -m
fi
