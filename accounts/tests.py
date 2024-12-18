import json
from .models import Account

from django.test import TestCase, Client
from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken

class AccountTestCase(TestCase):
    def setUp(self) -> None:
        self.bob = {
            "username": "bobjohnson",
            "email": "bob.johnson@example.com",
            "password": "password"
        }
        self.alice = {
            "username": "alicesmith",
            "email": "alice.smith@example.com",
            "password": "password"
        }
        self.empty_stats = {
            "solved": {
                "all": 0,
                "easy": 0,
                "school": 0,
                "medium": 0,
                "hard": 0
            },
            "total": {
                "all": 0,
                "easy": 0,
                "school": 0,
                "medium": 0,
                "hard": 0
            }
        }

        self.client = Client()

        # setting password 
        self.alice_account = Account.objects.create(**self.alice)
        self.alice_account.set_password(self.alice['password'])
        self.alice_account.save()

    def test_account_registration(self):
        '''
        Test successful account creation with valid values
        '''
        response = self.client.post("/api/v1/account/", self.bob)
        self.assertEqual(response.status_code, 200)

        account = Account.objects.filter(username=self.bob['username']).first()
        self.assertIsNot(account, None)

    def test_account_login(self):
        '''
        Test successful account login with valid credentials
        '''
        response = self.client.post("/api/v1/token/", self.alice)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'refresh')
        self.assertContains(response, 'access')

    def test_account_get_me_details(self):
        '''
        Test successful retrieval of account details
        '''
        refresh = RefreshToken.for_user(self.alice_account)

        response = self.client.get("/api/v1/account/me/", headers={
            'Authorization': "Bearer " + str(refresh.access_token)
        })
        self.assertEqual(response.status_code, 200)
        
        keys = ['public_id', 'username', 'email', 'is_superuser', 'is_staff', 'first_name', 'last_name']

        for key in keys:
            self.assertContains(response, key)

    
    def test_account_stats(self):
        '''
        Test successful retrieval of account statistics
        '''
        refresh = RefreshToken.for_user(self.alice_account)
        response = self.client.get("/api/v1/account/stats/", headers={
            "Authorization": "Bearer " + str(refresh.access_token)
        })

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), self.empty_stats)