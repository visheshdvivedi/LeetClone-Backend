from .models import Account
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

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
        fields = ['public_id', 'username', 'email', 'is_superuser', 'is_staff']

class GoogleAuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)

class UploadProfilePicSerializer(serializers.Serializer):
    image = Base64ImageField(required=True)