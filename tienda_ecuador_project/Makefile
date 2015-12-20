APPS = sri \
	company_accounts \
    customer_accounts \
	inventory \
	billing \
	accounts_receivable \
	reports \
	public_receipts

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
	$(foreach app, $(APPS), python manage.py makemigrations $(app) && ) true

deletemigrations:
	rm */migrations/0*.py
	rm */migrations/0*.pyc

reset_db: clear_db deploy_db

test_models:
	$(foreach app, $(APPS), python manage.py test $(app).testsuite.test_models && ) true

test_views:
	$(foreach app, $(APPS), python manage.py test $(app).testsuite.test_views && ) true

.PHONY: help deploy_db reset_db clear_db reset_db makemigrations deletemigrations test_models test_views
