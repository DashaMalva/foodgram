import csv

from django.core.management import BaseCommand

from recipes.models import Ingredient

FILE_PATH = './data/ingredients.csv'


class Command(BaseCommand):
    help = """
        Loads data from csv 'file'.
        If something goes wrong when you load data from the CSV file,
        first delete the db.sqlite3 file to destroy the database.
        Then, run `python manage.py migrate` for a new empty
        database with tables.
        """

    def load_ingredients_data(self):
        with open(FILE_PATH, 'r', encoding='utf-8') as csv_file:
            file_reader = csv.reader(csv_file)
            for row in file_reader:
                Ingredient.objects.get_or_create(
                    name=row[0], measurement_unit=row[1]
                )

    def handle(self, *args, **options):
        self.load_ingredients_data()
        self.stdout.write(self.style.SUCCESS('Data was loaded successfully.'))
