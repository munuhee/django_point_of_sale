from django.core.management.base import BaseCommand
from .models import Tax

class Command(BaseCommand):
    help = 'Delete all records from the Tax table'

    def handle(self, *args, **options):
        try:
            Tax.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted all records from the Tax table.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
