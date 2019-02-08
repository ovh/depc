.PHONY: ui tests docs scheduler

api:
	python manage.py runserver

ui:
	cd ui/ && grunt serve

worker:
	celery worker -A celery_launch.cel

flower:
	celery flower -A celery_launch.cel

webserver:
	airflow webserver

scheduler:
	airflow scheduler

clean-docs:
	cd docs/ && make clean

docs: clean-docs
	cd docs/ && make html

tests:
	pytest tests/ -vv
