from django.urls import path
from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

course_router = DefaultRouter()
course_router.register(r'courses', views.CourseViewSet, basename="course")

lesson_router = routers.NestedSimpleRouter(course_router, r'courses', lookup='course')
lesson_router.register(r'lessons', views.LessonViewSet)

question_router = routers.NestedSimpleRouter(lesson_router, r'lessons', lookup='lesson')
question_router.register(r'questions', views.QuestionViewSet)

available_courses_router = DefaultRouter()
available_courses_router.register(r'courses', views.CoursesAvailableViewSet, basename="course")

available_lessons_router = routers.NestedSimpleRouter(available_courses_router, r'courses', lookup='course')
available_lessons_router.register(r'lessons', views.LessonsAvailableViewSet)

urlpatterns = [
    url(r'^admin/', include(course_router.urls)),
    url(r'^admin/', include(lesson_router.urls)),
    url(r'^admin/', include(question_router.urls)),
    url(r'^students/', include(available_courses_router.urls)),
    url(r'^students/', include(available_lessons_router.urls)),
    path('logic_test', views.logic_test, name='logic_test'),
]
