
start: virtualenv
	@echo '#You need to run those commands'
	@echo 'source ./virtualenv/bin/activate'
	@echo 'export PYTHONPATH=$$PYTHONPATH:`pwd`'

virtualenv:
	@echo '#You need to run those commands'
	@echo 'python -m virtualenv virtualenv'
	@echo 'source virtualenv/bin/activate'
	@echo 'pip install -r requirements.txt'
	@echo 'deactivate'



.PHONY: clean

clean:
	rm -rf virtualenv $(shell find . -type f -name '*.pyc')

