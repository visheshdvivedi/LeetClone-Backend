from .models import Account
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from django.core import exceptions
from django.contrib.auth.password_validation import validate_password

class CreateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        account = Account.objects.create(**validated_data)
        account.set_password(validated_data.get("password"))
        account.save()
        return account

class ListAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['public_id', 'username', 'email']

class RetrieveAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['public_id', 'username', 'email', 'is_superuser', 'is_staff', 'first_name', 'last_name']

class GoogleAuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)

class UploadProfilePicSerializer(serializers.Serializer):
    image = Base64ImageField(required=True)

class GetProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['profile_picture']

class UpdateProfileSerializer(serializers.Serializer):
    confirm_password = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=254, required=True)
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)

    def validate(self, attrs):
        password = str(attrs.get("password"))

        errors = {"message": []} 
        length = len(password)

        if password not in attrs:
            return attrs
        
        # check for length
        if length < 8:
            errors['message'].append("Length must be at least 8 characters long")
        
        # check characters
        found_num = False
        found_upper = False
        found_lower = False
        found_special = False

        for char in password:
            if char.isnumeric(): found_num = True
            elif char.isupper(): found_upper = True
            elif char.islower(): found_lower = True
            else: found_special = True

        if not found_num: errors['message'].append("Password must have at least one number")
        if not found_lower: errors['message'].append("Password must have on lowercase character")
        if not found_upper: errors['message'].append("Password must have one uppercase character")
        if not found_special: errors['message'].append("Password must have one special character")
        
        if len(errors['message']):
            raise serializers.ValidationError(errors)

        return super().validate(attrs)