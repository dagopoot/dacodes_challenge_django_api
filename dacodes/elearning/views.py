from django.shortcuts import get_object_or_404, render
from django.db.models import Exists, OuterRef

from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from core.permissions import HasValidTeacherRole, HasValidStudentRole
from core.views import MultiSerializerViewSet

from .serializer import (
    CourseAvailableSerializer,
    CourseEnrollmentSerializer,
    CourseSerializer,
    EmptySerializer,
    GetLessonQuestionSerializer,
    LessonsAvailableSerializer,
    LessonEnrollmentSerializer,
    LessonPreviewSerializer,
    LessonSerializer,
    LogicSerializer,
    QuestionSerializer,
    SendTestSerializer,
)

from .models import (
    Answer,
    Course,
    CourseEnrollment,
    Lesson,
    LessonEnrollment,
    Question,
    UserAnswer
)

from .services.review import TestReview
from .services.logic import LogicTest


class CourseViewSet(viewsets.ModelViewSet):
    """
    Course administration
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (HasValidTeacherRole, )


class LessonViewSet(viewsets.ModelViewSet):
    """
    Lesson administration
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (HasValidTeacherRole, )

    def get_queryset(self):
        return self.queryset.filter(course_id=self.kwargs.get('course_pk'))


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Questions and answers administration
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = (HasValidTeacherRole, )

    def get_queryset(self):
        return self.queryset.filter(lesson_id=self.kwargs.get('lesson_pk'))


class CoursesAvailableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    courses that students have access to, courses have dependent courses, 
    it is necessary to pass the dependent course in order to subscribe
    """
    queryset = Course.objects.all()
    serializer_class = CourseAvailableSerializer
    permission_classes = (HasValidStudentRole, )

    def get_queryset(self):
        queryset = Course.objects.all().annotate(
            is_subscribed=Exists(
                CourseEnrollment
                .objects
                .filter(
                    course_id=OuterRef('id'),
                    user_id=self.request.user.id
                )
            ),
            is_approved=Exists(
                CourseEnrollment
                .objects
                .filter(
                    course_id=OuterRef('id'),
                    user_id=self.request.user.id,
                    is_approved=True
                )
            ),
            dependent_is_approved=Exists(
                CourseEnrollment
                .objects
                .filter(
                    course_id=OuterRef('dependent_id'),
                    user_id=self.request.user.id,
                    is_approved=True
                )
            )
        )

        return queryset

    @action(detail=True, methods=['post'], serializer_class=EmptySerializer)
    def subscribe(self, request, pk):
        """
        subscribe a user to a course
        """
        course_id = pk
        user_id = request.user.id

        if Course.objects.is_subscribed(course_id, user_id):
            message = {
                "message": "The user is already subscribed to this course"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        if Course.objects.subscribe(course_id, user_id):
            return Response({"message": "success"}, status=status.HTTP_201_CREATED)

        message = {"message": "User cannot register for this course"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class LessonsAvailableViewSet(MultiSerializerViewSet, viewsets.ReadOnlyModelViewSet):
    """
    lessons of a course that students have access to, lessons have dependent lessons, 
    it is necessary to pass the dependent lesson in order to subscribe
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonsAvailableSerializer
    permission_classes = (HasValidStudentRole, )
    custom_serializer_classes = {
        'list': LessonPreviewSerializer,
        'send_test': SendTestSerializer
    }

    def get_queryset(self):
        queryset = Lesson.objects.filter(
            course_id=self.kwargs.get('course_pk'),
            course__enrollments__user_id=self.request.user.id
        ).annotate(
            is_approved=Exists(
                LessonEnrollment
                .objects
                .filter(
                    lesson_id=OuterRef('id'),
                    user_id=self.request.user.id,
                    is_approved=True
                )
            ),
            dependent_is_approved=Exists(
                LessonEnrollment
                .objects
                .filter(
                    lesson_id=OuterRef('dependent_id'),
                    user_id=self.request.user.id,
                    is_approved=True
                )
            )
        )

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        get the content of the lesson, register the student if not registered
        """
        try:
            instance = self.get_object()
            user_id = request.user.id

            if not Lesson.objects.is_subscribed(instance.id, user_id):
                if not Lesson.objects.can_subscribe(instance.id, user_id):
                    message = {"message": "Lesson not available to user"}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)

                # subscribe the user to the lesson
                Lesson.objects.subscribe(instance.id, user_id)

            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Exception as ex:
            message = {"message": f"Error when obtaining the lesson {ex}"}
            return Response(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def get_test(self, request, *args, **kwargs):
        """
        Obtain the test of a lesson, it is necessary that the user is registered in the lesson
        """
        lesson = get_object_or_404(Lesson.objects, pk=self.kwargs["pk"])
        user_id = request.user.id

        if (Lesson.objects.is_subscribed(lesson.id, user_id)
                and not Lesson.objects.is_approved(lesson.id, user_id)):

            questions = Question.objects.filter(lesson_id=lesson.id)

            serializer = GetLessonQuestionSerializer(questions, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        message = {"message": "the test is not available to the user"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send_test(self, request, pk, *args, **kwargs):
        """
        subscribe a user to a lesson so they can be evaluated
        """
        lesson_id = pk
        user_id = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if (Lesson.objects.is_subscribed(lesson_id, user_id)
                and not Lesson.objects.is_approved(lesson_id, user_id)):

            test_review = TestReview(
                user_id, lesson_id, serializer.data['questions'])

            is_approved, message = test_review.evaluate()

            if is_approved:
                return Response({"message": "success"}, status=status.HTTP_200_OK)

            return Response({"message": "Failed test"}, status=status.HTTP_200_OK)

        message = {"message": "the test is not available to the user"}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
def logic_test(request):
    serializer = LogicSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)

    try:
        logic = LogicTest(serializer.data)

        results = logic.get_results()

        return Response({"result": results}, status=status.HTTP_200_OK)

    except Exception as ex:
        response = {
            "message": f"unexpected error: {ex}"}

        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
