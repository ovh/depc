.PHONY: ui tests docs scheduler consumer

api:
	python manage.py runserver

ui:
	cd ui/ && grunt serve

webserver:
	airflow webserver

scheduler:
	airflow scheduler

clean-docs:
	cd docs/ && make clean

docs: clean-docs
	cd docs/ && make html

tests:
	export DEPC_ENV=test && pytest tests/ -vv

consumer:
	python consumer/main.py
