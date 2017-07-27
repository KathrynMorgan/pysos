PYTHON = /usr/bin/python

all: rpm

rpm:
	$(PYTHON) setup.py bdist_rpm --binary-only

srpm:
	$(PYTHON) setup.py bdist_rpm --source-only

clean:
	$(RM) -rf dist/
	$(RM) -rf build/
	$(RM) -rf MANIFEST
