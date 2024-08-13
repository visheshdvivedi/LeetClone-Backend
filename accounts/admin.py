from django.contrib import admin
from .models import Account, AccountSolvedProblems

# Register your models here.
admin.site.register(Account)
admin.site.register(AccountSolvedProblems)