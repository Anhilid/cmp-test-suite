help:
	@echo  'Commands:'
	@echo  '  test         - Run all compliance tests (results will be in out/)'
	@echo  '  teslog       - Run all compliance tests, store results in timestamped subirectories in out/'
	@echo  '  doc          - Produce documentation files and store them in doc/'
	@echo  '  unittest     - Run unit tests for the test suite itself'
	@echo  ''


# By default, run the tests against the local environment from config/local.robot
# You can override it, e.g., `make test env=cloudpki`
env ?= local
test:
	robot --outputdir=out --variable environment:$(env) tests

# As above, but keep the results in timestamped subdirectories, so they keep accumulating. This is useful because you
# won't overwrite test reports from previous runs, which may contain interesting information about exotic errors you
# encountered.
testlog:
	robot --outputdir=out/`date +%Y-%m-%d_%H-%M_%B-%d` --variable environment:$(env) tests

unittest:
	# adjust path such that the unit tests can be started from the root directory, to make it easier to load
	# example files from data/
	PYTHONPATH=./resources python -m unittest discover -s unit_tests

docs:
	python -m robot.libdoc resources/keywords.resource doc/keywords.html
	python -m robot.libdoc resources/cryptoutils.py doc/cryptoutils.html
	python -m robot.libdoc resources/cmputils.py doc/cmputils.html
	python -m robot.libdoc resources/asn1utils.py doc/asn1utils.html
	python -m robot.libdoc resources/certutils.py doc/certutils.html
	python -m robot.testdoc tests/ doc/tests-suites.html
