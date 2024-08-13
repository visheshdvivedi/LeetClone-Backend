from datetime import datetime

from .models import Account, AccountSolvedProblems
from .services import get_user_data
from .serializers import CreateAccountSerializer, RetrieveAccountSerializer, ListAccountSerializer, GoogleAuthSerializer

from problems.models import Submission, DifficultyChoices, Problem
from problems.serializers import SubmissionSerializer

from django.shortcuts import redirect

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import AccountPermissions

class AccountViewSet(ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AccountPermissions]

    def create(self, request):
        serializer = CreateAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            return Response({"message": "Account created successfully"})
        return Response(serializer.errors)
    
    def list(self, request):
        queryset = Account.objects.filter(is_active=True).all()
        serializer = ListAccountSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk):
        account = Account.objects.filter(is_active=True, public_id=pk).first()
        serializer = RetrieveAccountSerializer(account)
        return Response(serializer.data)
    
    @action(detail=False, methods=['GET'], url_path='me', authentication_classes=[JWTAuthentication])
    def get_me_details(self, request):
        account = request.user
        serializer = RetrieveAccountSerializer(account)
        return Response(serializer.data)
    
    @action(detail=False, methods=['GET'], url_path="recent_submissions", authentication_classes=[JWTAuthentication])
    def get_recent_submissions(self, request):
        query_params = request.GET

        page_size = query_params.get("size", 10)
        try:
            page_size = int(page_size)
        except:
            return Response({"message": "Invalid page size"}, status=status.HTTP_400_BAD_REQUEST)
    
        data = Submission.objects.filter(account=request.user).order_by('-date')[:page_size].all()
        serializer = SubmissionSerializer(data, many=True)
        return Response(serializer.data)
    

    @action(detail=False, methods=['GET'], url_path="stats", authentication_classes=[JWTAuthentication])
    def get_user_stats(self, request):
        account = request.user
        output = {
            'solved': {
                'all': 0,
                'easy': 0,
                'school': 0,
                'medium': 0,
                'hard': 0
            },
            'total': {
                'all': 0,
                'easy': 0,
                'school': 0,
                'medium': 0,
                'hard': 0
            }
        }

        # get all problems count
        problems = Problem.objects.all()
        for problem in problems:
            output['total']['all'] += 1

            if problem.difficulty == DifficultyChoices.SCHOOL:
                output['total']['school'] += 1
            elif problem.difficulty == DifficultyChoices.EASY:
                output['total']['easy'] += 1
            elif problem.difficulty == DifficultyChoices.MEDIUM:
                output['total']['medium'] += 1
            elif problem.difficulty == DifficultyChoices.HARD:
                output['total']['hard'] += 1

        # get problems solved
        entries = AccountSolvedProblems.objects.filter(account=request.user).all()
        for entry in entries:
            output['solved']['all'] += 1

            if problem.difficulty == DifficultyChoices.SCHOOL:
                output['solved']['school'] += 1
            elif entry.problem.difficulty == DifficultyChoices.EASY:
                output['solved']['easy'] += 1
            elif entry.problem.difficulty == DifficultyChoices.MEDIUM:
                output['solved']['medium'] += 1
            elif entry.problem.difficulty == DifficultyChoices.HARD:
                output['solved']['hard'] += 1

        return Response(output)

class LogoutView(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = []

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response({"message": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as ex:
            print(ex)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
class GoogleLoginView(APIView):
    def get(self, request, *args, **kwargs):
        serializer = GoogleAuthSerializer(data=request.GET)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_data = get_user_data(data)

        if isinstance(user_data, str):
            return redirect(user_data)

        account = Account.objects.get(email=user_data['email'])
        refresh = RefreshToken.for_user(account)

        return redirect(f"https://leetclone-frontend.vercel.app/login/google?access={str(refresh.access_token)}&refresh={str(refresh)}")