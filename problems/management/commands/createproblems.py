import json
from django.core.management.base import BaseCommand, CommandError
from problems.serializers import CreateProblemSerializer

class Command(BaseCommand):
    help = "Create problems from predefined JSON file"

    def add_arguments(self, parser):
        parser.add_argument("file")

    def handle(self, *args, **options):

        with open(options.get("file")) as file:
            data = json.loads(file.read())

        for problem in data:
            
            for iter in range(len(problem['solutions'])):
                problem['solutions'][iter]['complexities'] = []

            for i in range(len(problem['testcases'])):
                for j in range(len(problem['testcases'][i]['inputs'])):
                    problem['testcases'][i]['inputs'][j]['value'] = str(problem['testcases'][i]['inputs'][j]['value'])

            print(f"Attempting to add {problem['name']}")

            try:
                serializer = CreateProblemSerializer(data = problem)
                if serializer.is_valid():
                    serializer.create(serializer.validated_data)
                else:
                    print(serializer.errors)
            except Exception as ex:
                CommandError(f"Failed to create problem {problem['name']}: {ex}")

        print("Command ran successfully ...")