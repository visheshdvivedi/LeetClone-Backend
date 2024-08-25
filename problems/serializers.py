from typing import List

from .judge import JudgeManager
from .models import Problem, TestCase, Code, Language, ValueField, Solution, Implementation, Complexity, Tag
from .models import Submission

import rest_framework.serializers as serializers
from django.db import models

# TODO: Update the code to change the function return type for Java, C# and C++
def createCode(name: str, inputs: List[dict]):
    return JudgeManager.create_default_code(name, inputs)

class VoteType(models.IntegerChoices):
    LIKE = (0, "Like")
    DISLIKE = (1, "Dislike")

class TagNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class ProblemNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['public_id', 'name']

class ValueFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValueField
        fields = ["name", "type", "value"]
        extra_kwargs = {
            "public_id": {
                "read_only": True
            }
        }

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["public_id", "name"]

class CodeSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()

    class Meta:
        model = Code
        fields = ["language", "value"]

class TestCaseSerializer(serializers.ModelSerializer):
    inputs = ValueFieldSerializer(many=True)

    class Meta:
        model = TestCase
        fields = ["inputs", "is_sample"]
        extra_kwargs = {
            "public_id": {
                "read_only": True
            }
        }

    def create(self, validated_data):
        testcase = TestCase.objects.create(
            is_sample = validated_data.get("is_sample")
        )
        
        # create inputs in database
        for entry in validated_data.get("inputs"):
            field = ValueField.objects.create(
                name = entry.get("name"),
                type = entry.get("type"),
                value = entry.get("value")
            )
            testcase.inputs.add(field)

        return testcase
    
class CreateImplementationSerializer(serializers.ModelSerializer):   

    class Meta:
        model = Implementation
        fields = ['language', 'value']

    def to_internal_value(self, data):
        val = super().to_internal_value(data)
        val['language'] = val['language'].public_id
        return val
    
class ListImplementationSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()

    class Meta:
        model = Implementation
        fields = ['language', 'value']

    def to_internal_value(self, data):
        val = super().to_internal_value(data)
        val['language'] = val['language'].public_id
        return val

class ComplexitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Complexity
        fields = ['type', 'value', 'explanation']
    
class CreateSolutionSerializer(serializers.ModelSerializer):
    implementations = CreateImplementationSerializer(many=True)
    complexities = ComplexitySerializer(many=True)

    class Meta:
        model = Solution
        fields = ["public_id", "name", "intution", "algorithm", "implementations", "complexities"]

    def create(self, validated_data):
        solution = Solution.objects.create(
            name = validated_data.get("name"),
            intution = validated_data.get("intution"),
            algorithm = validated_data.get("algorithm")
        )

        # create implementations
        for entry in validated_data.get("implementations"):
            serializer = CreateImplementationSerializer(data=entry)
            language = Language.objects.filter(public_id=entry.get("language")).first()
            if serializer.is_valid():
                implementation = Implementation.objects.create(
                    value = entry.get("value"),
                    language_id = language.public_id,
                    solution_id = solution.public_id
                )
                solution.implementations.add(implementation)
                language.implementations.add(implementation)
            else:
                return serializer.errors
            
        # create complexities
        for entry in validated_data.get("complexities"):
            serializer = ComplexitySerializer(data=entry)
            if serializer.is_valid():
                complexity = Complexity.objects.create(
                    value = entry.get("value"),
                    type = entry.get("type"),
                    explanation = entry.get("explanation"),
                    solution_id = solution.public_id
                )
                solution.complexities.add(complexity)
            else:
                return serializer.errors
            
        return solution
    
class ViewSolutionSerializer(serializers.ModelSerializer):
    implementations = ListImplementationSerializer(many=True)
    complexities = ComplexitySerializer(many=True)

    class Meta:
        model = Solution
        fields = ["public_id", "name", "intution", "algorithm", "implementations", "complexities"]

    def create(self, validated_data):
        solution = Solution.objects.create(
            name = validated_data.get("name"),
            intution = validated_data.get("intution"),
            algorithm = validated_data.get("algorithm")
        )

        # create implementations
        for entry in validated_data.get("implementations"):
            serializer = ListImplementationSerializer(data=entry)
            language = Language.objects.filter(public_id=entry.get("language")).first()
            if serializer.is_valid():
                implementation = Implementation.objects.create(
                    value = entry.get("value"),
                    language_id = language.public_id,
                    solution_id = solution.public_id
                )
                solution.implementations.add(implementation)
                language.implementations.add(implementation)
            else:
                return serializer.errors
            
        # create complexities
        for entry in validated_data.get("complexities"):
            serializer = ComplexitySerializer(data=entry)
            if serializer.is_valid():
                complexity = Complexity.objects.create(
                    value = entry.get("value"),
                    type = entry.get("type"),
                    explanation = entry.get("explanation"),
                    solution_id = solution.public_id
                )
                solution.complexities.add(complexity)
            else:
                return serializer.errors
            
        return solution

class CreateProblemSerializer(serializers.ModelSerializer):
    testcases = TestCaseSerializer(many=True)
    defaultCode = CodeSerializer(many=True)
    solutions = CreateSolutionSerializer(many=True)
    tags = TagNameSerializer(many=True)

    class Meta:
        model = Problem
        fields = ["public_id", "name", "likes", "dislikes", "difficulty", "description", "testcases", "defaultCode", "solutions", "constraints", "tags"]
        extra_kwargs = {
            "defaultCode": { "read_only": True },
            "likes": { "read_only": True },
            "dislikes": { "read_only": True }
        }

    def to_internal_value(self, data):
        for field in ["defaultCode"]:
            data[field] = []
        data = super().to_internal_value(data)  
        return data
    
    def get_testcases(self, problem_id):
        testcases = TestCase.objects.filter(problem_id=problem_id, is_sample=True).all()
        serializer = TestCaseSerializer(testcases, many=True)
        return serializer.data

    def create(self, validated_data):
        problem = Problem.objects.create(
            name = validated_data.get("name"),
            difficulty = validated_data.get("difficulty"),
            description = validated_data.get("description"),
            constraints = validated_data.get("constraints")
        )

        # create test cases
        for entry in validated_data.get("testcases"):
            serializer = TestCaseSerializer(data=entry)

            if serializer.is_valid():
                testcase = serializer.create(serializer.validated_data)    
                problem.testcases.add(testcase)
            else:
                return serializer.errors

        # create default code
        codes = createCode(validated_data.get("name"), testcase.inputs.all())
        for key in codes:
            language = Language.objects.filter(name=key).first()
            if not language:
                print(f"Unable to find language '{key}'")
            Code.objects.create(
                language_id=language.public_id,
                problem=problem,
                value=codes[key]
            )

        # create solutions
        for entry in validated_data.get("solutions"):
            serializer = CreateSolutionSerializer(data=entry)
            if serializer.is_valid():
                solution = serializer.create(serializer.validated_data)
                if not solution:
                    return solution
                problem.solutions.add(solution)
            else:
                return serializer.errors
            
        # create/set tags
        for entry in validated_data.get("tags"):
            name = entry.get("name", None)
            if not name:
                continue

            tag = Tag.objects.filter(name=name).first()
            if not tag:
                tag = Tag.objects.create(name=name)
            
            problem.tags.add(tag)

        return problem
    
class ListProblemSerializer(serializers.ModelSerializer):
    tags = TagNameSerializer(many=True)

    class Meta:
        model = Problem
        fields = ['public_id', 'name', 'likes', 'dislikes', 'difficulty', 'tags']
        extra_kwargs = {
            "likes": { "read_only": True },
            "dislikes": { "read_only": True }
        }
    
class ViewProblemSerializer(serializers.ModelSerializer):
    testcases = TestCaseSerializer(many=True)
    defaultCode = CodeSerializer(many=True)
    solutions = ViewSolutionSerializer(many=True)
    tags = TagNameSerializer(many=True)

    class Meta:
        model = Problem
        fields = ["public_id", "name", "likes", "dislikes", "difficulty", "description", "testcases", "defaultCode", "solutions", "tags", "constraints"]
        extra_kwargs = {
            "defaultCode": { "read_only": True },
            "likes": { "read_only": True },
            "dislikes": { "read_only": True }
        }

    def to_internal_value(self, data):
        for field in ["defaultCode"]:
            data[field] = []
        data = super().to_internal_value(data)  
        return data
    
    def get_testcases(self, problem_id):
        testcases = TestCase.objects.filter(problem_id=problem_id, is_sample=True).all()
        serializer = TestCaseSerializer(testcases, many=True)
        return serializer.data
    
class RetrieveProblemSerializer(serializers.ModelSerializer):
    testcases = TestCaseSerializer(many=True)
    defaultCode = CodeSerializer(many=True)
    solutions = ViewSolutionSerializer(many=True)
    tags = TagNameSerializer(many=True)

    accepted_submissions = serializers.IntegerField(source="get_total_accepted_submissions_count")
    total_submissions = serializers.IntegerField(source="get_total_submissions_count")
    acceptance_percent = serializers.CharField(source="get_global_acceptance_rate")

    class Meta:
        model = Problem
        fields = ["public_id", "name", "likes", "dislikes", "difficulty", "description", "testcases", "defaultCode", "solutions", "tags", "constraints", "accepted_submissions", "total_submissions", "acceptance_percent"]
        extra_kwargs = {
            "defaultCode": { "read_only": True },
            "likes": { "read_only": True },
            "dislikes": { "read_only": True }
        }

    def to_internal_value(self, data):
        for field in ["defaultCode"]:
            data[field] = []
        data = super().to_internal_value(data)  
        return data
    
    def get_testcases(self, problem_id):
        testcases = TestCase.objects.filter(problem_id=problem_id, is_sample=True).all()
        serializer = TestCaseSerializer(testcases, many=True)
        return serializer.data

class VoteSerializer(serializers.Serializer):
    vote_type = serializers.IntegerField()

class RunSerializer(serializers.Serializer):
    language_id = serializers.UUIDField()
    code = serializers.CharField()

class SubmissionSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()
    problem = ProblemNameSerializer()

    class Meta:
        model = Submission
        fields = ["public_id", "problem", "status", "code", "language", "time", "memory", "date", "time_percent", "memory_percent", "error_string", "reject_details"]
        read_only_fields = ["__all__"]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['public_id', 'name']
        read_only_field = ['__all__']