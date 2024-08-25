from django.contrib import admin
from .models import Problem, Solution, Implementation, Submission, Language, ProblemTag, Tag, ValueField

admin.site.register(Problem)
admin.site.register(Solution)
admin.site.register(Implementation)
admin.site.register(Submission)
admin.site.register(Language)
admin.site.register(ProblemTag)
admin.site.register(Tag)
admin.site.register(ValueField)