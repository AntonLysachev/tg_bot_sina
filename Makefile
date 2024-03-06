install:
	poetry install --no-root

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) bot:app

dev:
	poetry run flask --app bot:app --debug run --port 8000

lint:
	poetry run flake8 bot
