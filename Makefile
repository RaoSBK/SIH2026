.PHONY: setup start stop test clean

setup:
	@echo "Setting up the project..."
	python -m venv .venv
	.venv/Scripts/activate && pip install -r backend/requirements.txt -r ml/requirements.txt
	cd frontend && npm install

start:
	docker-compose up -d

stop:
	docker-compose down

test:
	pytest tests/

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} +
