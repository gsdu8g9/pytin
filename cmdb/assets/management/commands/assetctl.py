from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<resource_id resource_id ...>'
    help = 'Just a test'

    def handle(self, *args, **options):
        print args, options