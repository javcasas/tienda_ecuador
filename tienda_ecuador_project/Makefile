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

reset_db: clear_db deploy_db


.PHONY: help deploy_db reset_db clear_db reset_db
