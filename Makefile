.PHONY: install test run example clean format lint help

help:
	@echo "HL-Delta V2 - Available commands:"
	@echo "  make install    - Install package with dev dependencies"
	@echo "  make test       - Run test suite"
	@echo "  make run        - Start the bot"
	@echo "  make example    - Run example script"
	@echo "  make clean      - Remove build artifacts and cache"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linters (flake8, mypy)"

install:
	pip3 install --upgrade pip setuptools wheel
	pip3 install -e ".[dev]"

test:
	pytest -v --cov=delta_bot --cov-report=term-missing

test-quick:
	pytest -v

run:
	python3 entrypoint.py

example:
	python3 example.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -f delta.log
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

format:
	black src/ tests/ *.py
	isort src/ tests/ *.py

lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/

docker-build:
	docker build -t hl-delta:2.0.0 .

docker-run:
	docker run -d --name delta-bot -p 8080:8080 --env-file .env hl-delta:2.0.0
