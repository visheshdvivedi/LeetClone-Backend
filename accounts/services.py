from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Account

from urllib.parse import urlencode
from typing import Dict, Any

import requests
import jwt

GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
LOGIN_URL = f'https://leetclone-backend.azurewebsites.net/api/v1/login/google/'

def google_get_access_token(code:str, redirect_uri:str) -> str:
    data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    if not response.ok:
        print(response.content)
        raise ValidationError(response.content)
    
    access_token = response.json()['access_token']
    return access_token

def google_get_user_info(access_token:str) -> Dict[str, Any]:
    response = requests.get(
        GOOGLE_USER_INFO_URL,
        params={'access_token': access_token}
    )

    if not response.ok:
        raise ValidationError("Failed to get user details from google")
    
    return response.json()

def get_user_data(validated_data):
    domain = settings.BASE_API_URL
    redirect_uri = f"https://leetclone-backend.azurewebsites.net/api/v1/login/google/"

    code = validated_data.get("code")
    error = validated_data.get("error")

    if error or not code:
        params = urlencode({'error': error})
        return f"{LOGIN_URL}/{params}"
    
    access_token = google_get_access_token(code, redirect_uri)
    user_data = google_get_user_info(access_token)

    account = Account.objects.filter(email=user_data.get('email')).first()
    if not account:
        Account.objects.get_or_create(
            username = f"{user_data.get('given_name').lower()}_{user_data.get('family_name').lower()}",
            email = user_data.get("email")
        )

    profile_data = {
        'email': user_data['email'],
    }
    return profile_data