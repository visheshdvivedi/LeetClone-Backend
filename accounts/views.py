from datetime import datetime, timedelta

from .models import Account, AccountSolvedProblems
from .services import get_user_data
from .serializers import CreateAccountSerializer, RetrieveAccountSerializer, ListAccountSerializer, GoogleAuthSerializer, UploadProfilePicSerializer, GetProfilePictureSerializer

from problems.models import Submission, DifficultyChoices, Problem, DifficultyChoices, SubmissionStatus
from problems.serializers import SubmissionSerializer

from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import AccountPermissions
from .blob import upload_file_from_bytes, download_blob, get_all_blobs

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

            if entry.problem.difficulty == DifficultyChoices.SCHOOL:
                output['solved']['school'] += 1
            elif entry.problem.difficulty == DifficultyChoices.EASY:
                output['solved']['easy'] += 1
            elif entry.problem.difficulty == DifficultyChoices.MEDIUM:
                output['solved']['medium'] += 1
            elif entry.problem.difficulty == DifficultyChoices.HARD:
                output['solved']['hard'] += 1

        return Response(output)
    
    @action(detail=False, methods=['POST'], url_path="upload_profile_picture", authentication_classes=[JWTAuthentication])
    def upload_profile_picture(self, request):
        serializer = UploadProfilePicSerializer(data=request.data)
        if serializer.is_valid():
            account = request.user
            old_image = request.user.profile_picture

            account.profile_picture = serializer.validated_data["image"]
            account.save()

            if old_image:
                old_image.delete(save=False)

            return Response({"message": "Profile picture uploaded successfully."})
        return Response(serializer.errors, status=400)
    
    @action(detail=False, methods=['GET'], url_path="get_profile_picture", authentication_classes=[JWTAuthentication])
    def get_profile_picture(self, request):
        serializer = GetProfilePictureSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path="profile", authentication_classes=[JWTAuthentication])
    def get_profile_info(self, request):
        user = request.user

        solved_problems_stats = {
            "total": 0,
            "count_by_difficulty": {
                "school": 0, "easy": 0, "medium": 0, "hard": 0
            },
            "count_by_language": {},
            "count_by_tags": {}
        }
        solved_problems = AccountSolvedProblems.objects.filter(account=user).all()
        submissions = Submission.objects.filter(account=user, status=SubmissionStatus.ACCEPTED).all()
        solved_problems_stats['total'] = len(solved_problems)

        for solved_problem in solved_problems:
            org_problem = solved_problem.problem
            
            # count problems by difficulty
            if org_problem.difficulty == DifficultyChoices.SCHOOL: 
                if 'school' in solved_problems_stats['count_by_difficulty']: solved_problems_stats['count_by_difficulty']['school'] += 1
                else: solved_problems_stats['count_by_difficulty']['school'] = 1
            elif org_problem.difficulty == DifficultyChoices.EASY: 
                if 'easy' in solved_problems_stats['count_by_difficulty']: solved_problems_stats['count_by_difficulty']['easy'] += 1
                else: solved_problems_stats['count_by_difficulty']['school'] = 1
            elif org_problem.difficulty == DifficultyChoices.MEDIUM: 
                if 'medium' in solved_problems_stats['count_by_difficulty']: solved_problems_stats['count_by_difficulty']['medium'] += 1
                else: solved_problems_stats['count_by_difficulty']['medium'] = 1
            elif org_problem.difficulty == DifficultyChoices.HARD: 
                if 'hard' in solved_problems_stats['count_by_difficulty']: solved_problems_stats['count_by_difficulty']['hard'] += 1
                else: solved_problems_stats['count_by_difficulty']['hard'] = 1

            # count problems by tags
            for tag in org_problem.tags.all():
                if tag.name in solved_problems_stats['count_by_tags']: solved_problems_stats['count_by_tags'][tag.name] += 1
                else: solved_problems_stats['count_by_tags'][tag.name] = 1

        for submission in submissions:

            # count submissions by language
            if submission.language.name in solved_problems_stats['count_by_language']: solved_problems_stats['count_by_language'][submission.language.name] += 1
            else: solved_problems_stats['count_by_language'][submission.language.name] = 1

        # calculate data for heatmap
        heatmap = [[0] * 24, [0] * 24, [0] * 24, [0] * 24, [0] * 24, [0] * 24, [0] * 24]
        start_date = datetime.now() - timedelta(days=168)
        end_date = datetime.now()
        
        # calculate streaks
        all_time_max = user.max_streak
        curr_max = 0

        active_days = 0
        last_active_date = datetime.now()
        calculate_active_days = True

        for submission in Submission.objects.filter(account=user, date__gte=start_date, date__lte=end_date).order_by('-date').all():
            
            submit_day = submission.date.replace(tzinfo=None)

            # calculate streak
            if calculate_active_days:
                diff = abs((submit_day - last_active_date).days)
                if diff == 1:
                    active_days += 1
                    last_active_date -= timedelta(days=1)
                elif diff == 0:
                    calculate_active_days = False

            # calculate heatmap details
            diff_days = (end_date - submit_day).days
            day = submit_day.weekday()
            heatmap[day][diff_days // 7] += 1

        heatmap = [map[::-1] for map in heatmap]
        
        if all_time_max < active_days:
            user.max_streak = active_days
            user.save()
            all_time_max = active_days

        output = {
            "username": user.username,
            "full_name": user.get_full_name(),
            "active_days": active_days,
            "max_streak": all_time_max,
            "solved_problems": solved_problems_stats,
            "heatmap": heatmap
        }
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
        redirect_url = settings.GOOGLE_OAUTH_FRONTEND_REDIRECT_URL
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        try:
            account = get_user_data(data)
        except Exception as ex:
            return Response({ "message": "Failed to get user details from Google", "error": str(ex) }, status=400)

        refresh = RefreshToken.for_user(account)
        new_redirect = f"{redirect_url}?access={str(refresh.access_token)}&refresh={str(refresh)}"

        return redirect(new_redirect)