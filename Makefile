.ONESHELL:

install:
	poetry install --with dev --no-root

lock:
	poetry lock

test:
	pytest --no-migrations

check-migrations:
	python -B manage.py makemigrations --check --dry-run

migrate:
	python -B manage.py migrate

collectstatic:
	python -B manage.py collectstatic --noinput

check:
	black . --check \
	&& ruff check . \
	&& safety check \
	&& make check-migrations \

check-fix:
	black .
	ruff check --fix-only --show-fixes --statistics .

celery-worker-run:
	celery -A config worker --loglevel=info

celery-beat-run:
	celery -A config beat --loglevel=info

run_crontab:
	service cron start && python manage.py crontab add

run: migrate collectstatic
	python -B manage.py runserver 0.0.0.0:8000

run_server: collectstatic migrate
	daphne -b 0.0.0.0 -p 8000 config.asgi:application

up:
	docker compose up -d

down:
	docker compose down