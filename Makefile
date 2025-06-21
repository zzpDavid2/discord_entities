.PHONY: install dev-install lock sync clean test run

# Install dependencies
install:
	uv pip install -e .

# Install development dependencies (if any)
dev-install:
	uv pip install -e ".[dev]"

# Update lock file
lock:
	uv lock

# Sync dependencies with lock file
sync:
	uv sync

# Clean up
clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run tests (if you have pytest)
test:
	uv run pytest

# Run the main application
run:
	uv run python run_ghosts.py

# Activate virtual environment
venv:
	uv venv

# Add a new dependency
add:
	@read -p "Enter package name: " package; \
	uv add $$package

# Add a development dependency
add-dev:
	@read -p "Enter package name: " package; \
	uv add --dev $$package 