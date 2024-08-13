import json

from problems.serializers import CreateProblemSerializer

def process_problem(data: dict):

    # add complexities
    for i in range(len(data['solutions'])):
        data['solutions'][i]['complexities'] = []

    # convert all input values to string
    for i in range(len(data['testcases'])):
        for j in range(len(data['testcases'][i]['inputs'])):
            data['testcases'][i]['inputs'][j]['value'] = str(data['testcases'][i]['inputs'][j]['value'])

    return data

def main():

    with open("problems_list.json", "r") as file:
        data = json.loads(file.read())

    for problem in data:
        data = process_problem(problem)
        print(f"Attempting to add {problem['name']}")
        try:
            serializer = CreateProblemSerializer(data = problem)
            if serializer.is_valid():
                serializer.create(serializer.validated_data)
            else:
                print(serializer.errors)
        except Exception as ex:
            print(f"Failed to create problem {problem['name']}: {ex}")


main()