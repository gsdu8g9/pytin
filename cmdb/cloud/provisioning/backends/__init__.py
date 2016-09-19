__author__ = 'dmitry'


class MockResult():
    def __init__(self):
        self.id = 1

    def ready(self):
        return True

    def get(self):
        return {'name1': 'val1', 'name2': 'val2'}


class MockCelery():
    def send_task(self, *opts, **kwargs):
        return MockResult()

    def AsyncResult(self, id):
        return MockResult()
