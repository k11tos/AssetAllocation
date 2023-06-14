.PHONY: typehint
typehint:
	mypy --ignore-missing-imports *.py
#.PHONY: test
#test:
#	pytest tests/
.PHONY: lint
lint:
	for py in *.py;do \
		echo "Linting $$py"; \
		pylint -rn $$py; \
	done
#.PHONY: checklist
#checklist: lint typehint test
.PHONY: checklist
checklist: black lint typehint
.PHONY: black
black:
	black -l 79 *.py
.PHONY: clean
clean:
	find . -type f -name "*.pyc" | xargs rm -fr
	find . -type d -name __pycache__ | xargs rm -fr
