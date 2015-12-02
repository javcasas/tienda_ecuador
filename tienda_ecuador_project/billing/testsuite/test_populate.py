import os
from django.test import TestCase
import populate_billing

populate_billing.print_instance = lambda a, b: None


class FieldsTests(TestCase):
    """
    Tests that check if a given model has all the required fields
    """
    def test_all_clases(self):
        db_path = os.path.join(os.getcwd(), "db.sqlite3")
        db_bak_path = os.path.join(os.getcwd(), "a.db.sqlite3.bak")
        if os.path.exists(db_path):
            os.rename(db_path, db_bak_path)

        try:
            os.system("python manage.py migrate")
            os.system("python load_fixtures.py")
            os.system("python populate_billing.py")
        finally:
            os.unlink(db_path)
            if os.path.exists(db_bak_path):
                os.rename(db_bak_path, db_path)
