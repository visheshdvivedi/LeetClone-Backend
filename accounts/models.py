import os
from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

def generate_uuid():
    return str(uuid4())

def path_and_rename(instance, filename):
    upload_to = 'static/profile_pictures/'
    if '.' not in filename:
        raise Exception("Invalid file without extension")
    ext = filename.split('.')[-1]
    filename = f"{instance.public_id}.{ext}"
    return os.path.join(upload_to, filename)

class LoginType(models.IntegerChoices):
    EMAIL = 0
    GOOGLE = 1

class AccountManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):

        if not email:
            raise ValueError("User must have an email address")
        
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(
            email = email,
            is_staff = is_staff,
            is_active = True,
            is_superuser = is_superuser,
            last_login = now,
            date_joined = now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)
    

class AccountSolvedProblems(models.Model):
    public_id = models.UUIDField(default=generate_uuid, unique=True)
    problem = models.ForeignKey('problems.Problem', to_field="public_id", on_delete=models.CASCADE)
    account = models.ForeignKey('Account', to_field="public_id", on_delete=models.CASCADE)

class Account(AbstractBaseUser, PermissionsMixin):

    public_id = models.UUIDField(default=generate_uuid, unique=True)

    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    login_type = models.IntegerField(choices=LoginType.choices, default=LoginType.EMAIL)
    solved_problems = models.ManyToManyField('problems.Problem', through="AccountSolvedProblems")

    max_streak = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to=path_and_rename, null=True, blank=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = AccountManager()

    def get_full_name(self):
        return self.first_name + " " + self.last_name