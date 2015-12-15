help:
	@ echo "help make"
	@ echo "    deploy_db"
	@ echo "    reset_db"

deploy_db:
	python manage.py migrate
	python load_fixtures.py
	python populate_billing.py

clear_db:
	rm db.sqlite3

makemigrations:
	python manage.py makemigrations company_accounts
	python manage.py makemigrations sri
	python manage.py makemigrations inventory
	python manage.py makemigrations billing
	python manage.py makemigrations accounts_receivable
	python manage.py makemigrations reports
	python manage.py makemigrations public_receipts

deletemigrations:
	rm */migrations/0*.py
	rm */migrations/0*.pyc

reset_db: clear_db deploy_db


.PHONY: help deploy_db reset_db clear_db reset_db makemigrations deletemigrations
