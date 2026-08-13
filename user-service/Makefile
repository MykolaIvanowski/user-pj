.PHONY: install lint test run format typecheck

install:
    pip install -e .[dev]

lint:
    ruff check .
    black --check .
    isort --check-only .

format:
    black .
    isort .
    ruff check --fix .

typecheck:
    mypy app

test:
    pytest -q

run:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
