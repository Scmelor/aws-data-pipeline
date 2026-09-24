.PHONY: install data run test lint docker

install:
	pip install -r requirements.txt

data:
	python scripts/generate_data.py --rows 50000

run: data
	python -m src.jobs.run_local

test:
	python -m pytest -q

lint:
	ruff check .

docker:
	docker build -t aws-data-pipeline . && docker run --rm aws-data-pipeline
