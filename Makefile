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

.PHONY: docs
docs:
	cd docs && uv run sphinx-build -b html source build
	@echo "📚 문서가 docs/build/ 디렉토리에 생성되었습니다."
	@echo "📖 문서를 보려면: open docs/build/index.html"

.PHONY: docs-clean
docs-clean:
	rm -rf docs/build/
	@echo "🧹 문서 빌드 파일이 삭제되었습니다."

.PHONY: docs-serve
docs-serve: docs
	cd docs/build && python -m http.server 8000
	@echo "🌐 문서 서버가 http://localhost:8000 에서 실행 중입니다."
