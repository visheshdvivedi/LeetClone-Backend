import os, json

from problems.models import Language
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Setup python, java and javascript as languages"

    def handle(self, *args, **options):

        if not os.path.exists("languages.json"):
            raise CommandError(f"File 'languages.json' does not exist")
        
        with open("languages.json", "r") as file:
            content = json.loads(file.read())

        for language in content:
            lang = Language.objects.create(**language)
            print(f"name: {lang.name}, id: {lang.public_id}")

        print("Command executed successfully ...")