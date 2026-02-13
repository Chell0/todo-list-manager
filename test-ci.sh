#!/bin/bash
set -e

echo "=== Installing dependencies ==="
pip install flake8 pytest pytest-cov

echo "=== Running Flake8 ==="
flake8 todo.py tests/ --max-line-length=100 --extend-ignore=E203,W503

echo "=== Running tests ==="
pytest --cov=todo --cov-report=term

echo "=== All checks passed! ==="

#chmod +x test-ci.sh && ./test-ci.sh