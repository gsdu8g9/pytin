import os

from django.test import TestCase

from assets.models import Server


class QSW8300ImportDataTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_create_with_id_test(self):
        new_server = Server.create(label="test server", id=103)
        new_server.refresh_from_db()

        self.assertEqual(103, new_server.id)
