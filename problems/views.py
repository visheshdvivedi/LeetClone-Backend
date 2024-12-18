import time
import base64
from http import HTTPMethod, HTTPStatus

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Submission
from .models import Problem, Language, SubmissionStatus, TestCase, Tag
from .serializers import CreateProblemSerializer, ViewProblemSerializer, VoteSerializer, RunSerializer, LanguageSerializer, SubmissionSerializer, RetrieveProblemSerializer, TagSerializer, ListProblemSerializer

from accounts.models import AccountSolvedProblems

from django.conf import settings

from django.db.models import Q
from django.db import reset_queries, connection

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .judge import JudgeManager

JUDGE_MANAGER = JudgeManager()

class ProblemViewSet(ViewSet):
    """
    Viewset for managing problems
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CreateProblemSerializer(data=request.data)
        if serializer.is_valid():
            problem = serializer.create(serializer.validated_data)
            if not isinstance(problem, Problem):
                return Response({"message": problem})
            return Response({"id": problem.public_id, "message": "Problem created successfully"}, status=201)
        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
    
    # cache response for 24 hours
    def retrieve(self, request, pk=None):
        if not pk:
            return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)

        problem = Problem.objects.filter(published=True, public_id=pk).first()
        if not problem:
            return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)

        serializer = RetrieveProblemSerializer(problem)
        data = serializer.data
        data['testcases'] = serializer.get_testcases(problem.public_id)
        return Response(data)
    
    # cache response for 24 hours
    def list(self, request):

        filters = request.GET
        difficulty = filters.get("difficulty")
        search = filters.get("search")
        tags = filters.get("tags")

        filter_obj = Q()

        # process difficulty filters
        if search:
            filter_obj &= Q(name__icontains=search)
        if difficulty:
            filter_obj &= Q(difficulty=difficulty)
        if tags:
            if "," in tags:
                for tag in tags.split(","):
                    filter_obj |= Q(tags__name__contains=tag)
            else:
                filter_obj &=Q(tags__name__contains=tags)

        problems = Problem.objects.filter(published=True).filter(filter_obj).all()
        serializer = ListProblemSerializer(problems, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=[HTTPMethod.GET])
    def list_all_tags(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=[HTTPMethod.PUT])
    def vote(self, request, pk=None):
        serializer = VoteSerializer(data=request.data)
        if serializer.is_valid():
            vote_type = serializer.validated_data.get("vote_type")

            problem = Problem.objects.filter(public_id=pk, published=True).first()
            if not problem:
                return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)
            
            if vote_type not in [0, 1]:
                return Response({"message": "Invalid vote ID"}, status=HTTPStatus.BAD_REQUEST)
            
            if vote_type == 0:
                problem.likes += 1
            elif vote_type == 1:
                problem.dislikes += 1
            problem.save()

            return Response({"message": "Vote submitted successfully"})

        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
    
    @action(detail=True, methods=[HTTPMethod.POST])
    def run(self, request, pk=None):
        serializer = RunSerializer(data=request.data)
        if serializer.is_valid():

            # get language ID and code
            language_id = serializer.validated_data.get("language_id")
            code = serializer.validated_data.get("code")

            # check if language id is valid or not
            language = Language.objects.filter(public_id=language_id).first()
            if not language:
                return Response({"message", "Invalid language ID"}, status=HTTPStatus.BAD_REQUEST)
            
            # check if problem id is valid or not
            problem = Problem.objects.filter(public_id=pk, published=True).first()
            if not problem:
                return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)
            
            # add stdin and stdout code
            code = base64.b64decode(code).decode('utf-8')
            codes = JUDGE_MANAGER.create_boilerplate_code(code, problem, language)
            
            # run code
            count = problem.testcases.filter(is_sample=True).count()
            status, response = JUDGE_MANAGER.create_batch(codes=codes, language=language.judge_id)
            if not status:
                return Response({"message": str(response)}, status=HTTPStatus.BAD_REQUEST)
            
            tokens = [entry['token'] for entry in response]
            while True:

                status, response = JUDGE_MANAGER.get_batch(tokens)
                if not status:
                    return Response({"message": str(response)}, status=HTTPStatus.BAD_REQUEST)
                
                loop_state = False
                for entry in response['submissions']:
                    id = entry['status']['id']
                    if id == 2 or id == 1:
                        loop_state = True
                        break

                if loop_state:
                    time.sleep(2)
                    continue
                else:
                    for index, _ in enumerate(response['submissions']):
                        del response['submissions'][index]['token']
                        response['submissions'][index]['stdout'] = JUDGE_MANAGER.parse_stdout(response['submissions'][index]['stdout'])

                return Response(response)
                
        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
    
    @action(detail=True, methods=[HTTPMethod.GET])
    def submissions(self, request, pk=None):

        # check if problem id is valid or not
        problem = Problem.objects.filter(public_id=pk, published=True).first()
        if not problem:
            return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)
        
        submissions = Submission.objects.filter(problem=problem).order_by('-date').all()
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=200)
    
    @action(detail=True, methods=[HTTPMethod.POST])
    def submit(self, request, pk=None):
        serializer = RunSerializer(data=request.data)
        if serializer.is_valid():
            
            # get language ID and code
            language_id = serializer.validated_data.get("language_id")
            code = serializer.validated_data.get("code")

            # check if language id is valid or not
            language = Language.objects.filter(public_id=language_id).first()
            if not language:
                return Response({"message", "Invalid language ID"}, status=HTTPStatus.BAD_REQUEST)
            
            # check if problem id is valid or not
            problem = Problem.objects.filter(public_id=pk, published=True).first()
            if not problem:
                return Response({"message": "Invalid problem ID"}, status=HTTPStatus.BAD_REQUEST)
            
            # add stdin and stdout code
            code = base64.b64decode(code).decode('utf-8')
            codes = JUDGE_MANAGER.create_boilerplate_code(code, problem, language, is_sample=False)
            
            # run code
            status, response = JUDGE_MANAGER.create_batch(codes=codes, language=language.judge_id)
            if not status:
                return Response({"message": str(response)}, status=HTTPStatus.BAD_REQUEST)
            
            tokens = [entry['token'] for entry in response]
            while True:

                status, response = JUDGE_MANAGER.get_batch(tokens)
                if not status:
                    return Response({"message": str(response)}, status=HTTPStatus.BAD_REQUEST)
                
                loop_state = False
                for entry in response['submissions']:
                    id = entry['status']['id']
                    if id == 2 or id == 1:
                        loop_state = True
                        break

                if loop_state:
                    import time
                    time.sleep(2)
                    continue
            
                status = True
                total_time = 0
                total_memory = 0
                count = len(codes)
                error_string = ""

                # check for errors in code and parse stdout
                for index, entry in enumerate(response['submissions']):
                    if entry['stderr']:
                        error_string = entry['stderr']
                        status = None
                        break
                    elif entry['compile_output']:
                        error_string = entry['compile_output']
                        status = None
                        break

                    total_time += float(entry['time'])
                    total_memory += entry['memory']

                    response['submissions'][index]['stdout'] = JUDGE_MANAGER.parse_stdout(entry['stdout'])

                # check if answers are right or not
                if status != None:
                    testcases = TestCase.objects.filter(problem=problem).all()
                    status, failed_testcase_details = JUDGE_MANAGER.get_submission_status(testcases, response['submissions'])

                avg_time = float(total_time / count)
                avg_memory = float(total_memory / count)

                # create submission
                submission = Submission.objects.create(
                    problem = problem,
                    account = request.user,
                    language = language,
                    status = SubmissionStatus.ACCEPTED if status == True else SubmissionStatus.REJECTED if status == False else SubmissionStatus.RUNTIME_ERROR,
                    code = code,
                    time = str(avg_time),
                    memory = avg_memory,
                    time_percent = 93.5,
                    memory_percent = 98.3,
                    error_string = error_string,
                    reject_details = {} if status else failed_testcase_details
                )

                # if the solution is accepted, update the solved problems for the user
                if status:

                    # check if the same problem for the same account does not exist already
                    existing_solved = AccountSolvedProblems.objects.filter(account=request.user, problem=problem).first()

                    if not existing_solved:
                        AccountSolvedProblems.objects.create(
                            account = request.user,
                            problem = problem
                        )

                serializer = SubmissionSerializer(submission)
                output = serializer.data

                # add failed test case details in case if the 
                # submission was rejected
                if not status:
                    output['details'] = failed_testcase_details

                return Response(output)

        return Response(serializer.errors, status=400)


class LanguageViewSet(ViewSet):
    """
    ViewSet for managing languages
    """

    def list(self, request):
        languages = Language.objects.all()
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)
