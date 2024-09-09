from datetime import datetime
from django.db import models
from uuid import uuid4

from accounts.models import Account

def generate_default_uuid():
    return str(uuid4())

class ComplexityType(models.IntegerChoices):
    TIME = 1, "Time"
    SPACE = 2, "Space"

class DifficultyChoices(models.IntegerChoices):
    SCHOOL = 0, "School"
    EASY = 1, "Easy"
    MEDIUM = 2, "Medium"
    HARD = 3, "Hard"

class FieldType(models.IntegerChoices):
    INT = 1, "Integer"
    STRING = 2, "String"
    ARRAY_INT = 3, "Integer Array"
    ARRAY_STR = 4, "String Array",
    ARRAY_INT_2D = 5, "2D Integer Array"
    ARRAY_STR_2D = 6, "2D String Array"
    BOOLEAN = 7, "Boolean"
    FLOAT = 8, "Float"

class SubmissionStatus(models.IntegerChoices):
    ACCEPTED = 1, "Accepted"
    REJECTED = 2, "Rejected"
    RUNTIME_ERROR = 3, "Runtime Error"

class Problem(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    name = models.CharField(max_length=100, unique=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    difficulty = models.IntegerField(choices=DifficultyChoices.choices)
    description = models.TextField()
    constraints = models.TextField()
    tags = models.ManyToManyField("Tag", through="ProblemTag")
    published = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    
    def get_total_accepted_submissions_count(self):
        return len(self.submissions.filter(status=SubmissionStatus.ACCEPTED).all())

    def get_total_submissions_count(self):
        return len(self.submissions.all())
    
    def get_global_acceptance_rate(self):
        acceptance = self.get_total_accepted_submissions_count()
        total = self.get_total_submissions_count()

        if total == 0:
            return "0.00%"

        return str(round((acceptance / total) * 100, 2)) + "%"
    
class Tag(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name
    
class ProblemTag(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    problem = models.ForeignKey(Problem, to_field="public_id", on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, to_field="public_id", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.problem.name} - {self.tag.name}"

class ValueField(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    name = models.CharField(max_length=20)
    type = models.IntegerField(choices=FieldType.choices)
    value = models.TextField(null=True)
    testcase = models.ForeignKey("TestCase", related_name="inputs", to_field="public_id", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.testcase.problem}_{self.name}_{self.value}"

class Language(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    name = models.CharField(max_length=20)
    judge_id = models.IntegerField()

    def __str__(self):
        return self.name

class TestCase(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    problem = models.ForeignKey(Problem, related_name="testcases", to_field="public_id", on_delete=models.CASCADE, null=True)
    is_sample = models.BooleanField()

class Code(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    language = models.ForeignKey(Language, related_name="codes", to_field="public_id", on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, related_name="defaultCode", to_field="public_id", on_delete=models.CASCADE)
    value = models.TextField(null=True)

class Solution(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    problem = models.ForeignKey(Problem, to_field="public_id", related_name="solutions", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    intution = models.TextField(null=True)
    algorithm = models.TextField(null=True)

class Implementation(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    language = models.ForeignKey(Language, related_name="implementations", to_field="public_id", on_delete=models.CASCADE)
    solution = models.ForeignKey(Solution, related_name="implementations", to_field="public_id", on_delete=models.CASCADE)
    value = models.TextField(null=True)

class Complexity(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    value = models.CharField(max_length=20)
    explanation = models.TextField()
    type = models.IntegerField(choices=ComplexityType.choices)
    solution = models.ForeignKey(Solution, related_name="complexities", to_field="public_id", on_delete=models.CASCADE)

class Submission(models.Model):
    public_id = models.UUIDField(default=generate_default_uuid, unique=True)
    problem = models.ForeignKey(Problem, to_field="public_id", related_name="submissions", on_delete=models.CASCADE, null=True)
    account = models.ForeignKey(Account, to_field="public_id", related_name="submissions", on_delete=models.CASCADE, null=True)

    status = models.IntegerField(choices=SubmissionStatus.choices)
    code = models.TextField()
    language = models.ForeignKey(Language, related_name="submissions", to_field="public_id", on_delete=models.CASCADE)
    time = models.CharField(max_length=100)
    memory = models.IntegerField()
    date = models.DateTimeField(default=datetime.now)
    time_percent = models.FloatField()
    memory_percent = models.FloatField()
    error_string = models.TextField(null=True, blank=True)
    reject_details = models.JSONField(null=True, blank=True)