from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Account, LoginType

from urllib.parse import urlencode
from typing import Dict, Any

import requests

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
    redirect_uri = settings.GOOGLE_OAUTH_BACKEND_REDIRECT_URL

    code = validated_data.get("code")
    error = validated_data.get("error")

    if error or not code:
        raise Exception(error)
    
    access_token = google_get_access_token(code, redirect_uri)
    user_data = google_get_user_info(access_token)

    # get values
    email = user_data.get("email")
    username = email.split("@")[0]
    first_name = user_data.get("given_name")
    last_name = user_data.get("family_name")
    picture_url = user_data.get("picture")

    account = Account.objects.filter(username=username).first()
    if not account:
        return Account.objects.create(
            username = username,
            email = username,
            login_type = LoginType.GOOGLE,
            first_name = first_name,
            last_name = last_name,
            profile_picture = picture_url
        )
    return account